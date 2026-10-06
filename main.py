import os
import math
import qrcode
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

# Android GPS அணுகல்
try:
    from plyer import gps
except Exception:
    gps = None

Window.clearcolor = (0.07, 0.08, 0.1, 1)

def haversine(lat1, lon1, lat2, lon2):
    """இரு GPS புள்ளிகளுக்கு இடையே உள்ள தூரத்தைக் (KM) கணக்கிடும் சூத்திரம்"""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

class TaxiMeterApp(App):
    def build(self):
        self.is_running = False
        self.is_waiting = False
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0
        self.total_fare = 35.0
        self.last_lat = None
        self.last_lon = None
        self.upi_id = "9698421798@kotak811"

        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
            except Exception:
                pass

        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # தலைப்பு
        title_label = Label(
            text="DIGITAL AUTO METER",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.07),
            color=(0.9, 0.9, 0.9, 1)
        )
        main_layout.add_widget(title_label)

        # கட்டண விகிதங்கள்
        settings_grid = GridLayout(cols=3, size_hint=(1, 0.13), spacing=8)

        b_box = BoxLayout(orientation='vertical')
        b_box.add_widget(Label(text="BASE FARE (Rs)", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        self.base_input = TextInput(text="35", multiline=False, input_filter='float', halign='center', font_size='16sp')
        b_box.add_widget(self.base_input)

        km_p_box = BoxLayout(orientation='vertical')
        km_p_box.add_widget(Label(text="PER KM (Rs)", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        self.km_input = TextInput(text="18", multiline=False, input_filter='float', halign='center', font_size='16sp')
        km_p_box.add_widget(self.km_input)

        wait_p_box = BoxLayout(orientation='vertical')
        wait_p_box.add_widget(Label(text="WAIT/MIN (Rs)", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        self.wait_input = TextInput(text="1.5", multiline=False, input_filter='float', halign='center', font_size='16sp')
        wait_p_box.add_widget(self.wait_input)

        settings_grid.add_widget(b_box)
        settings_grid.add_widget(km_p_box)
        settings_grid.add_widget(wait_p_box)
        main_layout.add_widget(settings_grid)

        # மொத்தக் கட்டணம்
        fare_box = BoxLayout(orientation='vertical', size_hint=(1, 0.24))
        fare_box.add_widget(Label(text="TOTAL FARE", font_size='15sp', bold=True, color=(0.7, 0.7, 0.7, 1)))
        self.fare_display = Label(
            text="Rs. 35.00",
            font_size='54sp',
            bold=True,
            color=(0.1, 1.0, 0.3, 1)
        )
        fare_box.add_widget(self.fare_display)
        main_layout.add_widget(fare_box)

        # தூரம், பயண நேரம், காத்திருப்பு நேரம் (Big & Bold எழுத்துகள்)
        metrics_grid = GridLayout(cols=3, size_hint=(1, 0.20), spacing=5)

        # தூரம் (KM)
        d_box = BoxLayout(orientation='vertical')
        d_box.add_widget(Label(text="DISTANCE", font_size='13sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        self.km_display = Label(text="0.00 KM", font_size='25sp', bold=True, color=(1, 0.82, 0.1, 1))
        d_box.add_widget(self.km_display)

        # பயண நேரம்
        t_box = BoxLayout(orientation='vertical')
        t_box.add_widget(Label(text="TRIP TIME", font_size='13sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        self.time_display = Label(text="00:00", font_size='25sp', bold=True, color=(0.25, 0.85, 1, 1))
        t_box.add_widget(self.time_display)

        # காத்திருப்பு நேரம்
        w_box = BoxLayout(orientation='vertical')
        w_box.add_widget(Label(text="WAIT TIME", font_size='13sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        self.wait_display = Label(text="00:00", font_size='25sp', bold=True, color=(1, 0.35, 0.35, 1))
        w_box.add_widget(self.wait_display)

        metrics_grid.add_widget(d_box)
        metrics_grid.add_widget(t_box)
        metrics_grid.add_widget(w_box)
        main_layout.add_widget(metrics_grid)

        # கட்டுப்பாட்டு பொத்தான்கள்
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=10)

        self.start_btn = Button(
            text="START",
            font_size='18sp',
            bold=True,
            background_normal='',
            background_color=(0.15, 0.68, 0.38, 1)
        )
        self.start_btn.bind(on_press=self.toggle_meter)

        self.wait_btn = Button(
            text="WAIT ON",
            font_size='15sp',
            bold=True,
            background_normal='',
            background_color=(0.85, 0.5, 0.1, 1)
        )
        self.wait_btn.bind(on_press=self.toggle_waiting)

        self.reset_btn = Button(
            text="RESET",
            font_size='16sp',
            bold=True,
            background_normal='',
            background_color=(0.85, 0.25, 0.2, 1)
        )
        self.reset_btn.bind(on_press=self.reset_meter)

        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.wait_btn)
        btn_layout.add_widget(self.reset_btn)
        main_layout.add_widget(btn_layout)

        # கட்டண QR பொத்தான்
        self.qr_btn = Button(
            text="PAYMENT QR CODE",
            font_size='18sp',
            bold=True,
            size_hint=(1, 0.11),
            background_normal='',
            background_color=(0.2, 0.5, 0.9, 1)
        )
        self.qr_btn.bind(on_press=self.show_qr_popup)
        main_layout.add_widget(self.qr_btn)

        Clock.schedule_interval(self.update_timer, 1.0)
        return main_layout

    def start_gps(self):
        if gps:
            try:
                gps.configure(on_location=self.on_gps_location)
                gps.start(minTime=1000, minDistance=1)
            except Exception:
                pass

    def stop_gps(self):
        if gps:
            try:
                gps.stop()
            except Exception:
                pass
        self.last_lat = None
        self.last_lon = None

    def on_gps_location(self, **kwargs):
        if not self.is_running or self.is_waiting:
            return
        lat = kwargs.get('lat')
        lon = kwargs.get('lon')
        if lat is None or lon is None:
            return

        if self.last_lat is not None and self.last_lon is not None:
            dist = haversine(self.last_lat, self.last_lon, lat, lon)
            if dist > 0.005:
                self.distance_km += dist
                self.km_display.text = f"{self.distance_km:.2f} KM"
                self.calculate_fare()

        self.last_lat = lat
        self.last_lon = lon

    def toggle_meter(self, instance):
        if not self.is_running:
            self.is_running = True
            self.start_btn.text = "STOP"
            self.start_btn.background_color = (0.9, 0.2, 0.2, 1)
            self.start_gps()
        else:
            self.is_running = False
            self.is_waiting = False
            self.stop_gps()
            self.start_btn.text = "START"
            self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
            self.wait_btn.text = "WAIT ON"
            self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)
            self.show_qr_popup(None)

    def toggle_waiting(self, instance):
        if self.is_running:
            self.is_waiting = not self.is_waiting
            if self.is_waiting:
                self.wait_btn.text = "WAIT OFF"
                self.wait_btn.background_color = (0.3, 0.3, 0.8, 1)
            else:
                self.wait_btn.text = "WAIT ON"
                self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)

    def reset_meter(self, instance):
        self.is_running = False
        self.is_waiting = False
        self.stop_gps()
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0

        self.start_btn.text = "START"
        self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
        self.wait_btn.text = "WAIT ON"
        self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)

        base_val = float(self.base_input.text or 0)
        self.total_fare = base_val
        self.fare_display.text = f"Rs. {self.total_fare:.2f}"
        self.km_display.text = "0.00 KM"
        self.time_display.text = "00:00"
        self.wait_display.text = "00:00"

    def calculate_fare(self):
        try:
            base_fare = float(self.base_input.text or 0)
            rate_per_km = float(self.km_input.text or 0)
            rate_per_wait_min = float(self.wait_input.text or 0)
        except ValueError:
            return

        base_km = 1.8
        distance_cost = 0.0
        if self.distance_km > base_km:
            distance_cost = (self.distance_km - base_km) * rate_per_km

        waiting_cost = (self.wait_seconds / 60.0) * rate_per_wait_min
        self.total_fare = base_fare + distance_cost + waiting_cost
        self.fare_display.text = f"Rs. {self.total_fare:.2f}"

    def update_timer(self, dt):
        if self.is_running:
            self.trip_seconds += 1
            t_min = self.trip_seconds // 60
            t_sec = self.trip_seconds % 60
            self.time_display.text = f"{t_min:02d}:{t_sec:02d}"

            if self.is_waiting:
                self.wait_seconds += 1
                w_min = self.wait_seconds // 60
                w_sec = self.wait_seconds % 60
                self.wait_display.text = f"{w_min:02d}:{w_sec:02d}"
                self.calculate_fare()

    def show_qr_popup(self, instance):
        final_amt = f"{self.total_fare:.2f}"
        upi_url = f"upi://pay?pa={self.upi_id}&pn=AutoKanakku&am={final_amt}&cu=INR"

        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_path = os.path.join(self.user_data_dir, "fare_qr.png")
        img.save(qr_path)

        popup_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        popup_layout.add_widget(Label(
            text=f"Total Fare: Rs. {final_amt}",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.15),
            color=(0.1, 1, 0.3, 1)
        ))
        
        qr_image = Image(source=qr_path, size_hint=(1, 0.7))
        qr_image.reload()
        popup_layout.add_widget(qr_image)

        close_btn = Button(
            text="CLOSE",
            font_size='16sp',
            bold=True,
            size_hint=(1, 0.15),
            background_normal='',
            background_color=(0.85, 0.25, 0.2, 1)
        )
        popup_layout.add_widget(close_btn)

        popup = Popup(
            title="Scan & Pay UPI",
            content=popup_layout,
            size_hint=(0.9, 0.75),
            auto_dismiss=False
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    TaxiMeterApp().run()
