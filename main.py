import os
import json
import math
import datetime
import urllib.parse
import webbrowser
import qrcode
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

try:
    from plyer import gps
except Exception:
    gps = None

Window.clearcolor = (1, 1, 1, 1)

STATE_FILE = "meter_state.json"

class TaxiMeterApp(App):
    def build(self):
        self.is_running = False
        self.is_waiting = False
        self.is_moving = False
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0
        
        self.last_lat = None
        self.last_lon = None
        self.gps_initialized = False

        self.val_base = 70.0
        self.val_km = 20.0
        self.val_wait = 1.5
        self.base_km_limit = 1.5
        self.total_fare = self.val_base
        self.upi_id = "9698421798@kotak811"

        main_layout = BoxLayout(orientation='vertical', padding=12, spacing=8)

        # தலைப்பு மற்றும் நேரலை கடிகாரம்
        header_box = BoxLayout(orientation='vertical', size_hint=(1, 0.11), spacing=2)
        header_box.add_widget(Label(
            text="TAMILAN AUTO METER",
            font_size='22sp',
            bold=True,
            color=(0.1, 0.1, 0.1, 1)
        ))
        self.clock_display = Label(
            text=datetime.datetime.now().strftime("%d-%m-%Y | %I:%M:%S %p"),
            font_size='14sp',
            bold=True,
            color=(0.35, 0.35, 0.35, 1)
        )
        header_box.add_widget(self.clock_display)
        main_layout.add_widget(header_box)

        # ரேட் கண்ட்ரோல்
        settings_grid = GridLayout(cols=3, size_hint=(1, 0.14), spacing=6)
        minus_col = (0.85, 0.25, 0.2, 1)
        plus_col = (0.15, 0.55, 0.85, 1)

        # 1. Base Fare
        b_box = BoxLayout(orientation='vertical')
        b_box.add_widget(Label(text="BASE FARE", font_size='11sp', color=(0.3, 0.3, 0.3, 1), bold=True))
        b_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        b_m = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_col)
        b_m.bind(on_press=lambda x: self.adjust_rate('base', -5))
        self.b_btn = Button(text=str(int(self.val_base)), font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.9, 0.9, 0.9, 1), color=(0.1, 0.1, 0.1, 1))
        self.b_btn.bind(on_press=lambda x: self.open_keypad('base'))
        b_p = Button(text="+", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=plus_col)
        b_p.bind(on_press=lambda x: self.adjust_rate('base', 5))
        b_ctrl.add_widget(b_m)
        b_ctrl.add_widget(self.b_btn)
        b_ctrl.add_widget(b_p)
        b_box.add_widget(b_ctrl)

        # 2. Per KM
        km_box = BoxLayout(orientation='vertical')
        km_box.add_widget(Label(text="PER KM", font_size='11sp', color=(0.3, 0.3, 0.3, 1), bold=True))
        km_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        km_m = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_col)
        km_m.bind(on_press=lambda x: self.adjust_rate('km', -1))
        self.km_btn = Button(text=str(int(self.val_km)), font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.9, 0.9, 0.9, 1), color=(0.1, 0.1, 0.1, 1))
        self.km_btn.bind(on_press=lambda x: self.open_keypad('km'))
        km_p = Button(text="+", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=plus_col)
        km_p.bind(on_press=lambda x: self.adjust_rate('km', 1))
        km_ctrl.add_widget(km_m)
        km_ctrl.add_widget(self.km_btn)
        km_ctrl.add_widget(km_p)
        km_box.add_widget(km_ctrl)

        # 3. Wait/Min
        w_box = BoxLayout(orientation='vertical')
        w_box.add_widget(Label(text="WAIT/MIN", font_size='11sp', color=(0.3, 0.3, 0.3, 1), bold=True))
        w_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        w_m = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_col)
        w_m.bind(on_press=lambda x: self.adjust_rate('wait', -0.5))
        self.w_btn = Button(text=f"{self.val_wait:.1f}", font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.9, 0.9, 0.9, 1), color=(0.1, 0.1, 0.1, 1))
        self.w_btn.bind(on_press=lambda x: self.open_keypad('wait'))
        w_p = Button(text="+", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=plus_col)
        w_p.bind(on_press=lambda x: self.adjust_rate('wait', 0.5))
        w_ctrl.add_widget(w_m)
        w_ctrl.add_widget(self.w_btn)
        w_ctrl.add_widget(w_p)
        w_box.add_widget(w_ctrl)

        settings_grid.add_widget(b_box)
        settings_grid.add_widget(km_box)
        settings_grid.add_widget(w_box)
        main_layout.add_widget(settings_grid)

        # மொத்தக் கட்டணம்
        fare_box = BoxLayout(orientation='vertical', size_hint=(1, 0.22))
        fare_box.add_widget(Label(text="TOTAL FARE", font_size='15sp', bold=True, color=(0.3, 0.3, 0.3, 1)))
        self.fare_display = Label(
            text=f"Rs. {self.total_fare:.2f}",
            font_size='52sp',
            bold=True,
            color=(0.0, 0.6, 0.2, 1)
        )
        fare_box.add_widget(self.fare_display)
        main_layout.add_widget(fare_box)

        # அளவீடுகள்
        metrics_grid = GridLayout(cols=3, size_hint=(1, 0.16), spacing=5)

        d_sub = BoxLayout(orientation='vertical')
        d_sub.add_widget(Label(text="DISTANCE", font_size='12sp', bold=True, color=(0.3, 0.3, 0.3, 1)))
        self.km_display = Label(text="0.00 KM", font_size='22sp', bold=True, color=(0.85, 0.55, 0.0, 1))
        d_sub.add_widget(self.km_display)

        t_sub = BoxLayout(orientation='vertical')
        t_sub.add_widget(Label(text="TRIP TIME", font_size='12sp', bold=True, color=(0.1, 0.5, 0.8, 1)))
        self.time_display = Label(text="00:00", font_size='22sp', bold=True, color=(0.1, 0.5, 0.8, 1))
        t_sub.add_widget(self.time_display)

        w_sub = BoxLayout(orientation='vertical')
        w_sub.add_widget(Label(text="WAIT TIME", font_size='12sp', bold=True, color=(0.3, 0.3, 0.3, 1)))
        self.wait_display = Label(text="00:00", font_size='22sp', bold=True, color=(0.85, 0.2, 0.2, 1))
        w_sub.add_widget(self.wait_display)

        metrics_grid.add_widget(d_sub)
        metrics_grid.add_widget(t_sub)
        metrics_grid.add_widget(w_sub)
        main_layout.add_widget(metrics_grid)

        # பொத்தான்கள்
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.13), spacing=8)

        self.start_btn = Button(text="START", font_size='18sp', bold=True, background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        self.start_btn.bind(on_press=self.toggle_meter)

        self.wait_btn = Button(text="AUTO WAIT", font_size='14sp', bold=True, background_normal='', background_color=(0.85, 0.5, 0.1, 1))
        self.wait_btn.bind(on_press=self.toggle_waiting)

        self.reset_btn = Button(text="RESET", font_size='16sp', bold=True, background_normal='', background_color=(0.85, 0.25, 0.2, 1))
        self.reset_btn.bind(on_press=self.reset_meter)

        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.wait_btn)
        btn_layout.add_widget(self.reset_btn)
        main_layout.add_widget(btn_layout)

        # பில் மற்றும் கட்டண முறை
        self.pay_btn = Button(
            text="VIEW BILL & PAYMENT (SHARE / QR)",
            font_size='16sp',
            bold=True,
            size_hint=(1, 0.12),
            background_normal='',
            background_color=(0.2, 0.5, 0.9, 1)
        )
        self.pay_btn.bind(on_press=self.show_payment_options)
        main_layout.add_widget(self.pay_btn)

        self.init_gps()
        self.load_state()
        Clock.schedule_interval(self.update_timer, 1.0)
        return main_layout

    def set_screen_wake(self, keep_on=True):
        """ஆண்ட்ராய்டில் ஸ்கிரீன் ஆஃப் ஆகாமல் விழித்திருக்கச் செய்யும் வசதி"""
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                FLAG_KEEP_SCREEN_ON = 128  # WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                
                def apply_flag():
                    window = activity.getWindow()
                    if keep_on:
                        window.addFlags(FLAG_KEEP_SCREEN_ON)
                    else:
                        window.clearFlags(FLAG_KEEP_SCREEN_ON)

                activity.runOnUiThread(apply_flag)
            except Exception:
                pass

    def init_gps(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
            except Exception:
                pass
        if gps:
            try:
                gps.configure(on_location=self.on_gps_location)
            except Exception:
                pass

    def on_gps_location(self, **kwargs):
        if not self.is_running:
            return

        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        speed = kwargs.get('speed', 0.0)
        accuracy = kwargs.get('accuracy', 100.0)

        if accuracy is not None and accuracy > 35.0:
            return

        if speed is None:
            speed = 0.0

        self.is_moving = speed > 0.8

        if not self.gps_initialized or self.last_lat is None:
            self.last_lat = lat
            self.last_lon = lon
            self.gps_initialized = True
            return

        dist = self.calculate_distance(self.last_lat, self.last_lon, lat, lon)
        
        if 0.010 <= dist <= 0.200:
            self.distance_km += dist
            self.km_display.text = f"{self.distance_km:.2f} KM"
            self.recalculate_fare()
            self.is_moving = True
            self.last_lat = lat
            self.last_lon = lon
            self.save_state()

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    def open_keypad(self, target):
        self.kp_target = target
        self.kp_text = ""

        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.kp_screen = Label(text="0", font_size='32sp', bold=True, size_hint=(1, 0.22), color=(0.1, 1, 0.3, 1))
        content.add_widget(self.kp_screen)

        grid = GridLayout(cols=3, spacing=6, size_hint=(1, 0.63))
        keys = ['1','2','3','4','5','6','7','8','9','C','0','.']
        for k in keys:
            btn = Button(text=k, font_size='22sp', bold=True, background_normal='', background_color=(0.22, 0.25, 0.32, 1))
            btn.bind(on_press=self.kp_press)
            grid.add_widget(btn)
        content.add_widget(grid)

        save_btn = Button(text="SET RATE", font_size='18sp', bold=True, size_hint=(1, 0.15), background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        save_btn.bind(on_press=self.kp_save)
        content.add_widget(save_btn)

        self.kp_pop = Popup(title=f"Enter {target.upper()} Rate", content=content, size_hint=(0.85, 0.65))
        self.kp_pop.open()

    def kp_press(self, inst):
        v = inst.text
        if v == 'C':
            self.kp_text = ""
        else:
            if v == '.' and '.' in self.kp_text:
                return
            self.kp_text += v
        self.kp_screen.text = self.kp_text if self.kp_text else "0"

    def kp_save(self, inst):
        if self.kp_text:
            try:
                num = float(self.kp_text)
                if self.kp_target == 'base':
                    self.val_base = max(0.0, num)
                    self.b_btn.text = str(int(self.val_base)) if self.val_base.is_integer() else f"{self.val_base:.1f}"
                elif self.kp_target == 'km':
                    self.val_km = max(0.0, num)
                    self.km_btn.text = str(int(self.val_km)) if self.val_km.is_integer() else f"{self.val_km:.1f}"
                elif self.kp_target == 'wait':
                    self.val_wait = max(0.0, num)
                    self.w_btn.text = f"{self.val_wait:.1f}"
                self.recalculate_fare()
                self.save_state()
            except ValueError:
                pass
        self.kp_pop.dismiss()

    def adjust_rate(self, kind, step):
        if kind == 'base':
            self.val_base = max(0.0, self.val_base + step)
            self.b_btn.text = str(int(self.val_base)) if self.val_base.is_integer() else f"{self.val_base:.1f}"
        elif kind == 'km':
            self.val_km = max(0.0, self.val_km + step)
            self.km_btn.text = str(int(self.val_km)) if self.val_km.is_integer() else f"{self.val_km:.1f}"
        elif kind == 'wait':
            self.val_wait = max(0.0, self.val_wait + step)
            self.w_btn.text = f"{self.val_wait:.1f}"
        self.recalculate_fare()
        self.save_state()

    def toggle_meter(self, instance):
        if not self.is_running:
            self.is_running = True
            self.last_lat = None
            self.last_lon = None
            self.gps_initialized = False
            self.start_btn.text = "STOP"
            self.start_btn.background_color = (0.9, 0.2, 0.2, 1)
            self.set_screen_wake(True)  # ஸ்கிரீன் எப்போதும் ஆன்-ல் இருக்கச் செய்தல்
            if gps:
                try:
                    gps.start(1000, 1)
                except Exception:
                    pass
        else:
            self.is_running = False
            self.is_waiting = False
            self.is_moving = False
            self.start_btn.text = "START"
            self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
            self.wait_btn.text = "AUTO WAIT"
            self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)
            self.set_screen_wake(False)  # ஸ்கிரீனை இயல்பு நிலைக்கு மாற்றுதல்
            if gps:
                try:
                    gps.stop()
                except Exception:
                    pass
            self.save_state()
            self.show_payment_options(None)

    def toggle_waiting(self, instance):
        if self.is_running:
            self.is_waiting = not self.is_waiting
            if self.is_waiting:
                self.wait_btn.text = "WAITING..."
                self.wait_btn.background_color = (0.3, 0.3, 0.8, 1)
            else:
                self.wait_btn.text = "AUTO WAIT"
                self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)

    def reset_meter(self, instance):
        self.is_running = False
        self.is_waiting = False
        self.is_moving = False
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0
        self.last_lat = None
        self.last_lon = None
        self.gps_initialized = False

        self.set_screen_wake(False)

        if gps:
            try:
                gps.stop()
            except Exception:
                pass

        self.start_btn.text = "START"
        self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
        self.wait_btn.text = "AUTO WAIT"
        self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)

        self.total_fare = self.val_base
        self.fare_display.text = f"Rs. {self.total_fare:.2f}"
        self.km_display.text = "0.00 KM"
        self.time_display.text = "00:00"
        self.wait_display.text = "00:00"

        if os.path.exists(STATE_FILE):
            try:
                os.remove(STATE_FILE)
            except Exception:
                pass

    def recalculate_fare(self):
        distance_cost = 0.0
        if self.distance_km > self.base_km_limit:
            distance_cost = (self.distance_km - self.base_km_limit) * self.val_km

        waiting_cost = (self.wait_seconds / 60.0) * self.val_wait
        self.total_fare = self.val_base + distance_cost + waiting_cost
        self.fare_display.text = f"Rs. {self.total_fare:.2f}"

    def update_timer(self, dt):
        self.clock_display.text = datetime.datetime.now().strftime("%d-%m-%Y | %I:%M:%S %p")

        if self.is_running:
            self.trip_seconds += 1
            t_min = self.trip_seconds // 60
            t_sec = self.trip_seconds % 60
            self.time_display.text = f"{t_min:02d}:{t_sec:02d}"

            if not self.is_moving:
                self.is_waiting = True
                self.wait_btn.text = "WAITING..."
                self.wait_btn.background_color = (0.3, 0.3, 0.8, 1)
                
                self.wait_seconds += 1
                w_min = self.wait_seconds // 60
                w_sec = self.wait_seconds % 60
                self.wait_display.text = f"{w_min:02d}:{w_sec:02d}"
                self.recalculate_fare()
            else:
                if self.is_waiting:
                    self.is_waiting = False
                    self.wait_btn.text = "AUTO WAIT"
                    self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)

            if self.trip_seconds % 3 == 0:
                self.save_state()

    def save_state(self):
        data = {
            'is_running': self.is_running,
            'trip_seconds': self.trip_seconds,
            'wait_seconds': self.wait_seconds,
            'distance_km': self.distance_km,
            'total_fare': self.total_fare,
            'val_base': self.val_base,
            'val_km': self.val_km,
            'val_wait': self.val_wait
        }
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                self.is_running = data.get('is_running', False)
                self.trip_seconds = data.get('trip_seconds', 0)
                self.wait_seconds = data.get('wait_seconds', 0)
                self.distance_km = data.get('distance_km', 0.0)
                self.total_fare = data.get('total_fare', self.val_base)
                self.val_base = data.get('val_base', 70.0)
                self.val_km = data.get('val_km', 20.0)
                self.val_wait = data.get('val_wait', 1.5)

                self.b_btn.text = str(int(self.val_base))
                self.km_btn.text = str(int(self.val_km))
                self.w_btn.text = f"{self.val_wait:.1f}"

                self.km_display.text = f"{self.distance_km:.2f} KM"
                self.fare_display.text = f"Rs. {self.total_fare:.2f}"
                t_min = self.trip_seconds // 60
                t_sec = self.trip_seconds % 60
                self.time_display.text = f"{t_min:02d}:{t_sec:02d}"
                w_min = self.wait_seconds // 60
                w_sec = self.wait_seconds % 60
                self.wait_display.text = f"{w_min:02d}:{w_sec:02d}"

                if self.is_running:
                    self.start_btn.text = "STOP"
                    self.start_btn.background_color = (0.9, 0.2, 0.2, 1)
                    self.set_screen_wake(True)
                    if gps:
                        try:
                            gps.start(1000, 1)
                        except Exception:
                            pass
            except Exception:
                pass

    def get_bill_summary_text(self):
        extra_km = max(0.0, self.distance_km - self.base_km_limit)
        km_cost = extra_km * self.val_km
        wait_cost = (self.wait_seconds / 60.0) * self.val_wait
        now_time = datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p")

        bill = (
            f"--- TAMILAN AUTO RECEIPT ---\n"
            f"Date & Time: {now_time}\n"
            f"Total Distance: {self.distance_km:.2f} KM\n"
            f"Base Fare ({self.base_km_limit:.1f} KM): Rs. {self.val_base:.2f}\n"
            f"Extra KM ({extra_km:.2f} KM @ Rs.{self.val_km}/KM): Rs. {km_cost:.2f}\n"
            f"Waiting Time ({self.wait_seconds//60}m {self.wait_seconds%60}s): Rs. {wait_cost:.2f}\n"
            f"---------------------------\n"
            f"TOTAL FARE: Rs. {self.total_fare:.2f}\n"
            f"UPI: {self.upi_id}\n"
            f"Thank You! Safe Journey!"
        )
        return bill

    def show_payment_options(self, instance):
        bill_text = self.get_bill_summary_text()

        box = BoxLayout(orientation='vertical', padding=12, spacing=8)
        
        box.add_widget(Label(
            text=bill_text,
            font_size='13sp',
            bold=True,
            halign='left',
            color=(0.1, 0.1, 0.1, 1),
            size_hint=(1, 0.48)
        ))

        row1 = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.17))
        cash_btn = Button(text="CASH PAYMENT", font_size='14sp', bold=True, background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        cash_btn.bind(on_press=self.pay_cash)
        qr_btn = Button(text="UPI QR CODE", font_size='14sp', bold=True, background_normal='', background_color=(0.2, 0.5, 0.9, 1))
        qr_btn.bind(on_press=self.show_qr)
        row1.add_widget(cash_btn)
        row1.add_widget(qr_btn)
        box.add_widget(row1)

        row2 = BoxLayout(orientation='horizontal', spacing=8, size_hint=(1, 0.17))
        share_btn = Button(text="SHARE RECEIPT", font_size='14sp', bold=True, background_normal='', background_color=(0.1, 0.7, 0.4, 1))
        share_btn.bind(on_press=self.share_receipt)
        close_btn = Button(text="CLOSE", font_size='14sp', bold=True, background_normal='', background_color=(0.85, 0.25, 0.2, 1))
        row2.add_widget(share_btn)
        row2.add_widget(close_btn)
        box.add_widget(row2)

        self.pay_pop = Popup(title="Trip Bill & Payment", content=box, size_hint=(0.92, 0.65))
        close_btn.bind(on_press=self.pay_pop.dismiss)
        self.pay_pop.open()

    def share_receipt(self, inst):
        bill = self.get_bill_summary_text()
        encoded = urllib.parse.quote(bill)
        url = f"https://api.whatsapp.com/send?text={encoded}"
        webbrowser.open(url)

    def pay_cash(self, inst):
        self.pay_pop.dismiss()
        box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        box.add_widget(Label(text=f"Cash Collected: Rs. {self.total_fare:.2f}\nTrip Finished!", font_size='18sp', bold=True, halign='center', color=(0.1, 0.1, 0.1, 1)))
        ok = Button(text="DONE", font_size='16sp', bold=True, size_hint=(1, 0.35), background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        box.add_widget(ok)
        p = Popup(title="Cash Mode", content=box, size_hint=(0.85, 0.35))
        ok.bind(on_press=p.dismiss)
        p.open()

    def show_qr(self, inst):
        if hasattr(self, 'pay_pop'):
            self.pay_pop.dismiss()

        final_amt = f"{self.total_fare:.2f}"
        upi_url = f"upi://pay?pa={self.upi_id}&pn=TamilanAuto&am={final_amt}&cu=INR"

        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_path = "fare_qr.png"
        img.save(qr_path)

        box = BoxLayout(orientation='vertical', padding=12, spacing=8)
        box.add_widget(Label(
            text=f"Total Fare: Rs. {final_amt}",
            font_size='20sp',
            bold=True,
            size_hint=(1, 0.12),
            color=(0.0, 0.6, 0.2, 1)
        ))
        
        qr_image = Image(source=qr_path, size_hint=(1, 0.73))
        qr_image.reload()
        box.add_widget(qr_image)

        close_btn = Button(
            text="CLOSE",
            font_size='15sp',
            bold=True,
            size_hint=(1, 0.15),
            background_normal='',
            background_color=(0.85, 0.25, 0.2, 1)
        )
        box.add_widget(close_btn)

        pop = Popup(title="Scan UPI QR", content=box, size_hint=(0.9, 0.75))
        close_btn.bind(on_press=pop.dismiss)
        pop.open()

if __name__ == '__main__':
    TaxiMeterApp().run()
