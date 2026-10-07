import os
import math
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

Window.clearcolor = (0.07, 0.08, 0.1, 1)

def haversine(lat1, lon1, lat2, lon2):
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
        
        self.val_base = 35.0
        self.val_km = 18.0
        self.val_wait = 1.5
        self.total_fare = self.val_base
        self.upi_id = "9698421798@kotak811"

        self.last_lat = None
        self.last_lon = None
        self.gps_active = False

        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # தலைப்பு
        main_layout.add_widget(Label(
            text="DIGITAL AUTO METER",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.08),
            color=(0.9, 0.9, 0.9, 1)
        ))

        # கட்டண அமைப்புகள் (+/- பட்டன்கள் கலருடன்)
        settings_grid = GridLayout(cols=3, size_hint=(1, 0.16), spacing=8)

        minus_color = (0.75, 0.22, 0.17, 1)  # சிவப்பு
        plus_color = (0.16, 0.50, 0.73, 1)   # நீலம்

        # 1. BASE FARE
        b_box = BoxLayout(orientation='vertical')
        b_box.add_widget(Label(text="BASE FARE", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        b_ctrl = BoxLayout(orientation='horizontal', spacing=3)
        b_minus = Button(text="-", font_size='20sp', bold=True, size_hint=(0.32, 1), background_normal='', background_color=minus_color)
        b_minus.bind(on_press=lambda x: self.adjust_rate('base', -5))
        self.b_lbl = Label(text=f"{int(self.val_base)}", font_size='18sp', bold=True, size_hint=(0.36, 1))
        b_plus = Button(text="+", font_size='20sp', bold=True, size_hint=(0.32, 1), background_normal='', background_color=plus_color)
        b_plus.bind(on_press=lambda x: self.adjust_rate('base', 5))
        b_ctrl.add_widget(b_minus)
        b_ctrl.add_widget(self.b_lbl)
        b_ctrl.add_widget(b_plus)
        b_box.add_widget(b_ctrl)

        # 2. PER KM
        km_box = BoxLayout(orientation='vertical')
        km_box.add_widget(Label(text="PER KM", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        km_ctrl = BoxLayout(orientation='horizontal', spacing=3)
        km_minus = Button(text="-", font_size='20sp', bold=True, size_hint=(0.32, 1), background_normal='', background_color=minus_color)
        km_minus.bind(on_press=lambda x: self.adjust_rate('km', -1))
        self.km_lbl = Label(text=f"{int(self.val_km)}", font_size='18sp', bold=True, size_hint=(0.36, 1))
        km_plus = Button(text="+", font_size='20sp', bold=True, size_hint=(0.32, 1), background_normal='', background_color=plus_color)
        km_plus.bind(on_press=lambda x: self.adjust_rate('km', 1))
        km_ctrl.add_widget(km_minus)
        km_ctrl.add_widget(self.km_lbl)
        km_ctrl.add_widget(km_plus)
        km_box.add_widget(km_ctrl)

        # 3. WAIT/MIN
        w_box = BoxLayout(orientation='vertical')
        w_box.add_widget(Label(text="WAIT/MIN", font_size='11sp', color=(0.7, 0.7, 0.7, 1)))
        w_ctrl = BoxLayout(orientation='horizontal', spacing=3)
        w_minus = Button(text="-", font_size='20sp', bold=True, size_hint=(0.32, 1), background_normal='', background_color=minus_color)
        w_minus.bind(on_press=lambda x: self.adjust_rate('wait', -0.5))
        self.w_lbl = Label(text=f"{self.val_wait:.1f}", font_size='18sp', bold=True, size_hint=(0.36, 1))
        w_plus = Button(text="+", font_size='20sp', bold=True, size_hint=(0.32, 1), background_normal='', background_color=plus_color)
        w_plus.bind(on_press=lambda x: self.adjust_rate('wait', 0.5))
        w_ctrl.add_widget(w_minus)
        w_ctrl.add_widget(self.w_lbl)
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

        # QR பொத்தான்
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
        Clock.schedule_once(self.request_android_permissions, 1.0)
        return main_layout

    def request_android_permissions(self, dt):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
            except Exception:
                pass

    def adjust_rate(self, kind, step):
        if kind == 'base':
            self.val_base = max(10.0, self.val_base + step)
            self.b_lbl.text = f"{int(self.val_base)}"
            if not self.is_running:
                self.total_fare = self.val_base
                self.fare_display.text = f"Rs. {self.total_fare:.2f}"
        elif kind == 'km':
            self.val_km = max(5.0, self.val_km + step)
            self.km_lbl.text = f"{int(self.val_km)}"
        elif kind == 'wait':
            self.val_wait = max(0.5, self.val_wait + step)
            self.w_lbl.text = f"{self.val_wait:.1f}"

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
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km =
