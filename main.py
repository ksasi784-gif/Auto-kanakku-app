import os
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

Window.clearcolor = (0.07, 0.08, 0.1, 1)

class TaxiMeterApp(App):
    def build(self):
        self.is_running = False
        self.is_waiting = False
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0
        
        self.val_base = 35.0
        self.val_km = 18.0
        self.val_wait = 1.5
        self.total_fare = self.val_base
        self.upi_id = "9698421798@kotak811"

        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # தலைப்பு
        main_layout.add_widget(Label(
            text="TAMILAN AUTO METER",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.08),
            color=(0.9, 0.9, 0.9, 1)
        ))

        # ரேட் கண்ட்ரோல் (+, -, எண்களைத் தொட்டு மாற்றும் வசதி)
        settings_grid = GridLayout(cols=3, size_hint=(1, 0.16), spacing=8)
        minus_col = (0.75, 0.22, 0.17, 1)
        plus_col = (0.16, 0.50, 0.73, 1)

        # 1. Base Fare
        b_box = BoxLayout(orientation='vertical')
        b_box.add_widget(Label(text="BASE FARE", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        b_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        b_m = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_col)
        b_m.bind(on_press=lambda x: self.adjust_rate('base', -5))
        self.b_btn = Button(text=str(int(self.val_base)), font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.18, 0.2, 0.25, 1))
        self.b_btn.bind(on_press=lambda x: self.open_keypad('base'))
        b_p = Button(text="+", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=plus_col)
        b_p.bind(on_press=lambda x: self.adjust_rate('base', 5))
        b_ctrl.add_widget(b_m)
        b_ctrl.add_widget(self.b_btn)
        b_ctrl.add_widget(b_p)
        b_box.add_widget(b_ctrl)

        # 2. Per KM
        km_box = BoxLayout(orientation='vertical')
        km_box.add_widget(Label(text="PER KM", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        km_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        km_m = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_col)
        km_m.bind(on_press=lambda x: self.adjust_rate('km', -1))
        self.km_btn = Button(text=str(int(self.val_km)), font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.18, 0.2, 0.25, 1))
        self.km_btn.bind(on_press=lambda x: self.open_keypad('km'))
        km_p = Button(text="+", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=plus_col)
        km_p.bind(on_press=lambda x: self.adjust_rate('km', 1))
        km_ctrl.add_widget(km_m)
        km_ctrl.add_widget(self.km_btn)
        km_ctrl.add_widget(km_p)
        km_box.add_widget(km_ctrl)

        # 3. Wait/Min
        w_box = BoxLayout(orientation='vertical')
        w_box.add_widget(Label(text="WAIT/MIN", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        w_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        w_m = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_col)
        w_m.bind(on_press=lambda x: self.adjust_rate('wait', -0.5))
        self.w_btn = Button(text=f"{self.val_wait:.1f}", font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.18, 0.2, 0.25, 1))
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
        fare_box = BoxLayout(orientation='vertical', size_hint=(1, 0.23))
        fare_box.add_widget(Label(text="TOTAL FARE", font_size='15sp', bold=True, color=(0.7, 0.7, 0.7, 1)))
        self.fare_display = Label(
            text=f"Rs. {self.total_fare:.2f}",
            font_size='54sp',
            bold=True,
            color=(0.1, 1.0, 0.3, 1)
        )
        fare_box.add_widget(self.fare_display)
        main_layout.add_widget(fare_box)

        # அளவீடுகள்
        metrics_grid = GridLayout(cols=3, size_hint=(1, 0.19), spacing=5)

        d_sub = BoxLayout(orientation='vertical')
        d_sub.add_widget(Label(text="DISTANCE", font_size='13sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        self.km_display = Label(text="0.00 KM", font_size='25sp', bold=True, color=(1, 0.82, 0.1, 1))
        d_sub.add_widget(self.km_display)

        t_sub = BoxLayout(orientation='vertical')
        t_sub.add_widget(Label(text="TRIP TIME", font_size='13sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        self.time_display = Label(text="00:00", font_size='25sp', bold=True, color=(0.25, 0.85, 1, 1))
        t_sub.add_widget(self.time_display)

        w_sub = BoxLayout(orientation='vertical')
        w_sub.add_widget(Label(text="WAIT TIME", font_size='13sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        self.wait_display = Label(text="00:00", font_size='25sp', bold=True, color=(1, 0.35, 0.35, 1))
        w_sub.add_widget(self.wait_display)

        metrics_grid.add_widget(d_sub)
        metrics_grid.add_widget(t_sub)
        metrics_grid.add_widget(w_sub)
        main_layout.add_widget(metrics_grid)

        # பொத்தான்கள்
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=10)

        self.start_btn = Button(text="START", font_size='18sp', bold=True, background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        self.start_btn.bind(on_press=self.toggle_meter)

        self.wait_btn = Button(text="WAIT ON", font_size='15sp', bold=True, background_normal='', background_color=(0.85, 0.5, 0.1, 1))
        self.wait_btn.bind(on_press=self.toggle_waiting)

        self.reset_btn = Button(text="RESET", font_size='16sp', bold=True, background_normal='', background_color=(0.85, 0.25, 0.2, 1))
        self.reset_btn.bind(on_press=self.reset_meter)

        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.wait_btn)
        btn_layout.add_widget(self.reset_btn)
        main_layout.add_widget(btn_layout)

        # CASH / QR பொத்தான்
        self.pay_btn = Button(
            text="PAYMENT OPTIONS (CASH / QR)",
            font_size='17sp',
            bold=True,
            size_hint=(1, 0.11),
            background_normal='',
            background_color=(0.2, 0.5, 0.9, 1)
        )
        self.pay_btn.bind(on_press=self.show_payment_options)
        main_layout.add_widget(self.pay_btn)

        Clock.schedule_interval(self.update_timer, 1.0)
        return main_layout

    def open_keypad(self, target):
        self.kp_target = target
        self.kp_text = ""

        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.kp_screen = Label(text="0", font_size='30sp', bold=True, size_hint=(1, 0.22), color=(0.1, 1, 0.3, 1))
        content.add_widget(self.kp_screen)

        grid = GridLayout(cols=3, spacing=6, size_hint=(1, 0.63))
        keys = ['1','2','3','4','5','6','7','8','9','C','0','.']
        for k in keys:
            btn = Button(text=k, font_size='22sp', bold=True, background_normal='', background_color=(0.22, 0.25, 0.32, 1))
            btn.bind(on_press=self.kp_press)
            grid.add_widget(btn)
        content.add_widget(grid)

        save_btn = Button(text="SAVE RATE", font_size='18sp', bold=True, size_hint=(1, 0.15), background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        save_btn.bind(on_press=self.kp_save)
        content.add_widget(save_btn)

        self.kp_pop = Popup(title=f"Set {target.upper()}", content=content, size_hint=(0.85, 0.65))
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
                    self.b_btn.text = str(int(self.val_base))
                    if not self.is_running:
                        self.total_fare = self.val_base
                        self.fare_display.text = f"Rs. {self.total_fare:.2f}"
                elif self.kp_target == 'km':
                    self.val_km = max(0.0, num)
                    self.km_btn.text = str(int(self.val_km))
                elif self.kp_target == 'wait':
                    self.val_wait = max(0.0, num)
                    self.w_btn.text = f"{self.val_wait:.1f}"
                self.recalculate_fare()
            except ValueError:
                pass
        self.kp_pop.dismiss()

    def adjust_rate(self, kind, step):
        if kind == 'base':
            self.val_base = max(10.0, self.val_base + step)
            self.b_btn.text = str(int(self.val_base))
            if not self.is_running:
                self.total_fare = self.val_base
                self.fare_display.text = f"Rs. {self.total_fare:.2f}"
        elif kind == 'km':
            self.val_km = max(5.0, self.val_km + step)
            self.km_btn.text = str(int(self.val_km))
        elif kind == 'wait':
            self.val_wait = max(0.5, self.val_wait + step)
            self.w_btn.text = f"{self.val_wait:.1f}"
        self.recalculate_fare()

    def toggle_meter(self, instance):
        if not self.is_running:
            self.is_running = True
            self.start_btn.text = "STOP"
            self.start_btn.background_color = (0.9, 0.2, 0.2, 1)
        else:
            self.is_running = False
            self.is_waiting = False
            self.start_btn.text = "START"
            self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
            self.wait_btn.text = "WAIT ON"
            self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)
            self.show_payment_options(None)

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
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0

        self.start_btn.text = "START"
        self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
        self.wait_btn.text = "WAIT ON"
        self.wait_btn.background_color = (0.85, 0.5, 0.1, 1)

        self.total_fare = self.val_base
        self.fare_display.text = f"Rs. {self.total_fare:.2f}"
        self.km_display.text = "0.00 KM"
        self.time_display.text = "00:00"
        self.wait_display.text = "00:00"

    def recalculate_fare(self):
        base_km = 1.8
        distance_cost = 0.0
        if self.distance_km > base_km:
            distance_cost = (self.distance_km - base_km) * self.val_km

        waiting_cost = (self.wait_seconds / 60.0) * self.val_wait
        self.total_fare = self.val_base + distance_cost + waiting_cost
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
                self.recalculate_fare()

    def show_payment_options(self, instance):
        final_amt = f"{self.total_fare:.2f}"
        box = BoxLayout(orientation='vertical', padding=15, spacing=15)

        box.add_widget(Label(
            text=f"Total Fare: Rs. {final_amt}",
            font_size='24sp',
            bold=True,
            size_hint=(1, 0.3),
            color=(0.1, 1, 0.3, 1)
        ))

        btn_row = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.45))
        
        cash_btn = Button(text="CASH PAYMENT", font_size='16sp', bold=True, background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        cash_btn.bind(on_press=self.pay_cash)

        qr_opt_btn = Button(text="ONLINE UPI QR", font_size='16sp', bold=True, background_normal='', background_color=(0.2, 0.5, 0.9, 1))
        qr_opt_btn.bind(on_press=self.show_qr)

        btn_row.add_widget(cash_btn)
        btn_row.add_widget(qr_opt_btn)
        box.add_widget(btn_row)

        close_btn = Button(text="CLOSE", font_size='16sp', bold=True, size_hint=(1, 0.25), background_normal='', background_color=(0.85, 0.25, 0.2, 1))
        box.add_widget(close_btn)

        self.pay_pop = Popup(title="Select Payment Method", content=box, size_hint=(0.9, 0.45))
        close_btn.bind(on_press=self.pay_pop.dismiss)
        self.pay_pop.open()

    def pay_cash(self, inst):
        self.pay_pop.dismiss()
        box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        box.add_widget(Label(text=f"Cash Collected: Rs. {self.total_fare:.2f}\nTrip Finished!", font_size='20sp', bold=True, halign='center'))
        ok = Button(text="DONE", font_size='18sp', bold=True, size_hint=(1, 0.35), background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        box.add_widget(ok)
        p = Popup(title="Cash Mode", content=box, size_hint=(0.85, 0.35))
        ok.bind(on_press=p.dismiss)
        p.open()

    def show_qr(self, inst):
        if hasattr(self, 'pay_pop'):
            self.pay_pop.dismiss()

        final_amt = f"{self.total_fare:.2f}"
        upi_url = f"upi://pay?pa={self.upi_id}&pn=AutoKanakku&am={final_amt}&cu=INR"

        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_path = "fare_qr.png"
        img.save(qr_path)

        box = BoxLayout(orientation='vertical', padding=15, spacing=10)
        box.add_widget(Label(
            text=f"Total Fare: Rs. {final_amt}",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.15),
            color=(0.1, 1, 0.3, 1)
        ))
        
        qr_image = Image(source=qr_path, size_hint=(1, 0.7))
        qr_image.reload()
        box.add_widget(qr_image)

        close_btn = Button(
            text="CLOSE",
            font_size='16sp',
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
