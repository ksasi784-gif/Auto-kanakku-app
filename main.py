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
        
        # இயல்புநிலை கட்டணங்கள்
        self.val_base = 35.0
        self.val_km = 18.0
        self.val_wait = 1.5
        self.total_fare = self.val_base
        self.upi_id = "9698421798@kotak811"

        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # தலைப்பு
        main_layout.add_widget(Label(
            text="DIGITAL AUTO METER",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.08),
            color=(0.9, 0.9, 0.9, 1)
        ))

        # கட்டண அமைப்புகள் (+/- பட்டன்கள் மற்றும் தொட்டு எண் மாற்றும் வசதி)
        settings_grid = GridLayout(cols=3, size_hint=(1, 0.16), spacing=8)
        minus_color = (0.75, 0.22, 0.17, 1)
        plus_color = (0.16, 0.50, 0.73, 1)

        # 1. BASE FARE
        b_box = BoxLayout(orientation='vertical')
        b_box.add_widget(Label(text="BASE FARE", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        b_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        b_minus = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_color)
        b_minus.bind(on_press=lambda x: self.adjust_rate('base', -5))
        self.b_btn = Button(text=f"{int(self.val_base)}", font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.18, 0.2, 0.25, 1))
        self.b_btn.bind(on_press=lambda x: self.open_numpad('base'))
        b_plus = Button(text="+", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=plus_color)
        b_plus.bind(on_press=lambda x: self.adjust_rate('base', 5))
        b_ctrl.add_widget(b_minus)
        b_ctrl.add_widget(self.b_btn)
        b_ctrl.add_widget(b_plus)
        b_box.add_widget(b_ctrl)

        # 2. PER KM
        km_box = BoxLayout(orientation='vertical')
        km_box.add_widget(Label(text="PER KM", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        km_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        km_minus = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_color)
        km_minus.bind(on_press=lambda x: self.adjust_rate('km', -1))
        self.km_btn = Button(text=f"{int(self.val_km)}", font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.18, 0.2, 0.25, 1))
        self.km_btn.bind(on_press=lambda x: self.open_numpad('km'))
        km_plus = Button(text="+", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=plus_color)
        km_plus.bind(on_press=lambda x: self.adjust_rate('km', 1))
        km_ctrl.add_widget(km_minus)
        km_ctrl.add_widget(self.km_btn)
        km_ctrl.add_widget(km_plus)
        km_box.add_widget(km_ctrl)

        # 3. WAIT/MIN
        w_box = BoxLayout(orientation='vertical')
        w_box.add_widget(Label(text="WAIT/MIN", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        w_ctrl = BoxLayout(orientation='horizontal', spacing=2)
        w_minus = Button(text="-", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=minus_color)
        w_minus.bind(on_press=lambda x: self.adjust_rate('wait', -0.5))
        self.w_btn = Button(text=f"{self.val_wait:.1f}", font_size='18sp', bold=True, size_hint=(0.4, 1), background_normal='', background_color=(0.18, 0.2, 0.25, 1))
        self.w_btn.bind(on_press=lambda x: self.open_numpad('wait'))
        w_plus = Button(text="+", font_size='18sp', bold=True, size_hint=(0.3, 1), background_normal='', background_color=plus_color)
        w_plus.bind(on_press=lambda x: self.adjust_rate('wait', 0.5))
        w_ctrl.add_widget(w_minus)
        w_ctrl.add_widget(self.w_btn)
        w_ctrl.add_widget(w_plus)
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

        # அளவீடுகள்: தூரம், நேரம், காத்திருப்பு
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

        # பிரதான பொத்தான்கள்
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

        # PAYMENT OPTIONS (CASH & QR) பட்டன்
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

    # 1 2 3 எண் பலகை பாப்-அப் (Direct Numpad Input)
    def open_numpad(self, field_type):
        self.numpad_target = field_type
        self.numpad_val = ""

        box = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.num_preview = Label(text="0", font_size='28sp', bold=True, size_hint=(1, 0.25), color=(0.1, 1, 0.3, 1))
        box.add_widget(self.num_preview)

        keys_grid = GridLayout(cols=3, spacing=5, size_hint=(1, 0.6))
        for key in ['1','2','3','4','5','6','7','8','9','C','0','.']:
            b = Button(text=key, font_size='20sp', bold=True, background_normal='', background_color=(0.25, 0.28, 0.35, 1))
            b.bind(on_press=self.numpad_click)
            keys_grid.add_widget(b)
        box.add_widget(keys_grid)

        set_btn = Button(text="SET VALUE", font_size='18sp', bold=True, size_hint=(1, 0.15), background_normal='', background_color=(0.15, 0.68, 0.38, 1))
        box.add_widget(set_btn)

        self.numpad_pop = Popup(title=f"Set Rate for {field_type.upper()}", content=box, size_hint=(0.85, 0.65))
        set_btn.bind(on_press=self.apply_numpad_value)
        self.numpad_pop.open()

    def numpad_click(self, instance):
        k = instance.text
        if k == 'C':
            self.numpad_val = ""
        else:
            if k == '.' and '.' in self.numpad_val:
                return
            self.numpad_val += k
        self.num_preview.text = self.numpad_val if self.numpad_val else "0"

    def apply_numpad_value(self, instance):
        if self.numpad_val:
            val = float(self.numpad_val)
            if self.numpad_target == 'base':
                self.val_base = max(0.0, val)
                self.b_btn.text = f"{int(self.val_base)}"
                if not self.is_running:
                    self.total_fare = self.val_base
                    self.fare_display.text = f"Rs. {self.total_fare:.2f}"
            elif self.numpad_target == 'km':
                self.val_km = max(0.0, val)
                self.km_btn.text = f"{int(self.val_km)}"
            elif self.numpad_target == 'wait':
                self.val_wait = max(0.0, val)
                self.w_btn.text = f"{self.val_wait:.1f}"
            self.recalculate_fare()
        self.numpad_pop.dismiss()

    def adjust_rate(self, kind, step):
        if kind == 'base':
            self.val_base = max(10.0, self.val_base + step)
            self.b_btn.text = f"{int(self.val_base)}"
            if not self.is_running:
                self.total_fare = self.val_base
                self.fare_display.text = f"Rs. {self.total_fare:.2f}"
        elif kind == 'km':
            self.val_km = max(5.0, self.val_km + step)
            self.km_btn.text = f"{int(self.val_km)}"
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
        self.wait_display.text = "
 
