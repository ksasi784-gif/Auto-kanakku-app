import os
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
from kivy.core.text import LabelBase

Window.clearcolor = (0.07, 0.08, 0.1, 1)

# தமிழ் எழுத்துருவை பாதுகாப்பாகப் பதிவு செய்தல்
APP_FONT = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "tamil.ttf")

if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name="TamilFont", fn_regular=FONT_PATH)
        APP_FONT = "TamilFont"
    except Exception:
        APP_FONT = None

class TaxiMeterApp(App):
    def build(self):
        self.is_running = False
        self.is_waiting = False
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0
        self.total_fare = 35.0
        self.upi_id = "9698421798@kotak811"

        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # தலைப்பு
        title_label = Label(
            text="டிஜிட்டல் டாக்ஸி மீட்டர்",
            font_size='22sp',
            bold=True,
            font_name=APP_FONT,
            size_hint=(1, 0.08),
            color=(0.9, 0.9, 0.9, 1)
        )
        main_layout.add_widget(title_label)

        # கட்டண விகிதங்கள்
        settings_grid = GridLayout(cols=3, size_hint=(1, 0.14), spacing=8)

        b_box = BoxLayout(orientation='vertical')
        b_box.add_widget(Label(text="அடிப்படை (ரூ)", font_size='11sp', font_name=APP_FONT, color=(0.7, 0.7, 0.7, 1)))
        self.base_input = TextInput(text="35", multiline=False, input_filter='float', halign='center', font_size='15sp')
        b_box.add_widget(self.base_input)

        km_p_box = BoxLayout(orientation='vertical')
        km_p_box.add_widget(Label(text="கி.மீ கட்டணம் (ரூ)", font_size='11sp', font_name=APP_FONT, color=(0.7, 0.7, 0.7, 1)))
        self.km_input = TextInput(text="18", multiline=False, input_filter='float', halign='center', font_size='15sp')
        km_p_box.add_widget(self.km_input)

        wait_p_box = BoxLayout(orientation='vertical')
        wait_p_box.add_widget(Label(text="காத்திருப்பு/நிமி (ரூ)", font_size='11sp', font_name=APP_FONT, color=(0.7, 0.7, 0.7, 1)))
        self.wait_input = TextInput(text="1.5", multiline=False, input_filter='float', halign='center', font_size='15sp')
        wait_p_box.add_widget(self.wait_input)

        settings_grid.add_widget(b_box)
        settings_grid.add_widget(km_p_box)
        settings_grid.add_widget(wait_p_box)
        main_layout.add_widget(settings_grid)

        # மொத்தக் கட்டணம்
        fare_box = BoxLayout(orientation='vertical', size_hint=(1, 0.25))
        fare_box.add_widget(Label(text="மொத்த கட்டணம்", font_size='14sp', font_name=APP_FONT, color=(0.7, 0.7, 0.7, 1)))
        self.fare_display = Label(
            text="Rs. 35.00",
            font_size='50sp',
            bold=True,
            color=(0.1, 1.0, 0.3, 1)
        )
        fare_box.add_widget(self.fare_display)
        main_layout.add_widget(fare_box)

        # தூரம், பயண நேரம், காத்திருப்பு நேரம்
        metrics_grid = GridLayout(cols=3, size_hint=(1, 0.16), spacing=5)

        # தூரம் பாக்ஸ் (முழுமையாகச் சரிசெய்யப்பட்டது)
        d_box = BoxLayout(orientation='vertical')
        d_box.add_widget(Label(text="தூரம்", font_size='12sp', font_name=APP_FONT, color=(0.7, 0.7, 0.7, 1)))
        self.km_display = Label(text="0.00 KM", font_size='18sp', bold=True, color=(1, 0.8, 0.2, 1))
        d_box.add_widget(self.km_display)

        # நேரம் பாக்ஸ்
        t_box = BoxLayout(orientation='vertical')
        t_box.add_widget(Label(text="பயண நேரம்", font_size='12sp', font_name=APP_FONT, color=(0.7, 0.7, 0.7, 1)))
        self.time_display = Label(text="00:00", font_size='18sp', bold=True, color=(0.3, 0.8, 1, 1))
        t_box.add_widget(self.time_display)

        # காத்திருப்பு பாக்ஸ்
        w_box = BoxLayout(orientation='vertical')
        w_box.add_widget(Label(text="காத்திருப்பு நேரம்", font_size='12sp', font_name=APP_FONT, color=(0.7, 0.7, 0.7, 1)))
        self.wait_display = Label(text="00:00", font_size='18sp', bold=True, color=(1, 0.4, 0.4, 1))
        w_box.add_widget(self.wait_display)

        metrics_grid.add_widget(d_box)
        metrics_grid.add_widget(t_box)
        metrics_grid.add_widget(w_box)
        main_layout.add_widget(metrics_grid)

        # பொத்தான்கள் (தொடங்கு, காத்திரு, மீட்டமை)
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.13), spacing=10)

        self.start_btn = Button(
            text="தொடங்கு",
            font_size='16sp',
            bold=True,
            font_name=APP_FONT,
            background_normal='',
            background_color=(0.15, 0.68, 0.38, 1)
        )
        self.start_btn.bind(on_press=self.toggle_meter)

        self.wait_btn = Button(
            text="காத்திரு ON",
            font_size='14sp',
            bold=True,
            font_name=APP_FONT,
            background_normal='',
            background_color=(0.8, 0.5, 0.1, 1)
        )
        self.wait_btn.bind(on_press=self.toggle_waiting)

        self.reset_btn = Button(
            text="மீட்டமை",
            font_size='15sp',
            bold=True,
            font_name=APP_FONT,
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
            text="கட்டண QR கோட்",
            font_size='17sp',
            bold=True,
            font_name=APP_FONT,
            size_hint=(1, 0.12),
            background_normal='',
            background_color=(0.2, 0.5, 0.9, 1)
        )
        self.qr_btn.bind(on_press=self.show_qr_popup)
        main_layout.add_widget(self.qr_btn)

        Clock.schedule_interval(self.update_meter, 1.0)
        return main_layout

    def toggle_meter(self, instance):
        if not self.is_running:
            self.is_running = True
            self.start_btn.text = "நிறுத்து"
            self.start_btn.background_color = (0.9, 0.2, 0.2, 1)
        else:
            self.is_running = False
            self.is_waiting = False
            self.start_btn.text = "தொடங்கு"
            self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
            self.wait_btn.text = "காத்திரு ON"
            self.wait_btn.background_color = (0.8, 0.5, 0.1, 1)
            self.show_qr_popup(None)

    def toggle_waiting(self, instance):
        if self.is_running:
            self.is_waiting = not self.is_waiting
            if self.is_waiting:
                self.wait_btn.text = "காத்திரு OFF"
                self.wait_btn.background_color = (0.3, 0.3, 0.8, 1)
            else:
                self.wait_btn.text = "காத்திரு ON"
                self.wait_btn.background_color = (0.8, 0.5, 0.1, 1)

    def reset_meter(self, instance):
        self.is_running = False
        self.is_waiting = False
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0

        self.start_btn.text = "தொடங்கு"
        self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
        self.wait_btn.text = "காத்திரு ON"
        self.wait_btn.background_color = (0.8, 0.5, 0.1, 1)

        base_val = float(self.base_input.text or 0)
        self.total_fare = base_val
        self.fare_display.text = f"Rs. {self.total_fare:.2f}"
        self.km_display.text = "0.00 KM"
        self.time_display.text = "00:00"
        self.wait_display.text = "00:00"

    def update_meter(self, dt):
        if self.is_running:
            try:
                base_fare = float(self.base_input.text or 0)
                rate_per_km = float(self.km_input.text or 0)
                rate_per_wait_min = float(self.wait_input.text or 0)
            except ValueError:
                return

            self.trip_seconds += 1
            t_min = self.trip_seconds // 60
            t_sec = self.trip_seconds % 60
            self.time_display.text = f"{t_min:02d}:{t_sec:02d}"

            if self.is_waiting:
                self.wait_seconds += 1
                w_min = self.wait_seconds // 60
                w_sec = self.wait_seconds % 60
                self.wait_display.text = f"{w_min:02d}:{w_sec:02d}"
            else:
                self.distance_km += 0.0083
                self.km_display.text = f"{self.distance_km:.2f} KM"

            base_km = 1.8
            distance_cost = 0.0
            if self.distance_km > base_km:
                distance_cost = (self.distance_km - base_km) * rate_per_km

            waiting_cost = (self.wait_seconds / 60.0) * rate_per_wait_min
            self.total_fare = base_fare + distance_cost + waiting_cost
            self.fare_display.text = f"Rs. {self.total_fare:.2f}"

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
            text=f"செலுத்த வேண்டிய தொகை: ரூ. {final_amt}",
            font_size='18sp',
            bold=True,
            font_name=APP_FONT,
            size_hint=(1, 0.15),
            color=(0.1, 1, 0.3, 1)
        ))
        
        qr_image = Image(source=qr_path, size_hint=(1, 0.7))
        qr_image.reload()
        popup_layout.add_widget(qr_image)

        close_btn = Button(
            text="மூடு",
            font_size='16sp',
            bold=True,
            font_name=APP_FONT,
            size_hint=(1, 0.15),
            background_normal='',
            background_color=(0.85, 0.25, 0.2, 1)
        )
        popup_layout.add_widget(close_btn)

        popup = Popup(
            title="UPI மூலம் செலுத்தவும்",
            title_font=APP_FONT if APP_FONT else 'Roboto',
            content=popup_layout,
            size_hint=(0.9, 0.75),
            auto_dismiss=False
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    TaxiMeterApp().run()
