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

Window.clearcolor = (0.07, 0.08, 0.1, 1)

# தமிழ் எழுத்துரு Android-ல் சரியாகத் தெரிய
TAMIL_FONT = "/system/fonts/NotoSansTamil-Regular.ttf"
if not os.path.exists(TAMIL_FONT):
    TAMIL_FONT = None

TRANSLATIONS = {
    'en': {
        'title': "DIGITAL TAXI METER",
        'base': "BASE (Rs)",
        'per_km': "PER KM (Rs)",
        'wait_min': "WAIT/MIN (Rs)",
        'fare': "TOTAL FARE",
        'distance': "DISTANCE",
        'trip_time': "TRIP TIME",
        'wait_time': "WAIT TIME",
        'start': "START",
        'stop': "STOP",
        'wait_on': "WAIT ON",
        'wait_off': "WAIT OFF",
        'reset': "RESET",
        'qr_btn': "PAYMENT QR CODE",
        'popup_title': "Scan & Pay UPI",
        'pay_label': "Payable Amount: Rs. ",
        'close': "CLOSE",
        'lang_btn': "தமிழ்"
    },
    'ta': {
        'title': "டிஜிட்டல் டாக்ஸி மீட்டர்",
        'base': "அடிப்படை (ரூ)",
        'per_km': "கி.மீ கட்டணம் (ரூ)",
        'wait_min': "காத்திருப்பு/நிமி (ரூ)",
        'fare': "மொத்த கட்டணம்",
        'distance': "தூரம்",
        'trip_time': "பயண நேரம்",
        'wait_time': "காத்திருப்பு நேரம்",
        'start': "தொடங்கு",
        'stop': "நிறுத்து",
        'wait_on': "காத்திரு ON",
        'wait_off': "காத்திரு OFF",
        'reset': "மீட்டமை",
        'qr_btn': "கட்டண QR கோட்",
        'popup_title': "UPI மூலம் செலுத்தவும்",
        'pay_label': "செலுத்த வேண்டிய தொகை: ரூ. ",
        'close': "மூடு",
        'lang_btn': "English"
    }
}

class TaxiMeterApp(App):
    def build(self):
        self.current_lang = 'ta'  # துவக்கத்தில் தமிழ் மொழி
        self.is_running = False
        self.is_waiting = False
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0
        self.total_fare = 35.0
        self.upi_id = "9698421798@kotak811"

        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # மேல் பகுதி: தலைப்பு & மொழி மாற்றும் பட்டன்
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.09))
        self.title_label = Label(
            text=TRANSLATIONS[self.current_lang]['title'],
            font_size='20sp',
            bold=True,
            font_name=TAMIL_FONT if self.current_lang == 'ta' else 'Roboto',
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(0.75, 1)
        )
        self.lang_btn = Button(
            text=TRANSLATIONS[self.current_lang]['lang_btn'],
            font_size='14sp',
            bold=True,
            font_name=TAMIL_FONT,
            size_hint=(0.25, 1),
            background_normal='',
            background_color=(0.3, 0.3, 0.5, 1)
        )
        self.lang_btn.bind(on_press=self.toggle_language)
        top_bar.add_widget(self.title_label)
        top_bar.add_widget(self.lang_btn)
        main_layout.add_widget(top_bar)

        # கட்டண விகிதங்கள்
        settings_grid = GridLayout(cols=3, size_hint=(1, 0.14), spacing=8)

        b_box = BoxLayout(orientation='vertical')
        self.base_lbl = Label(text=TRANSLATIONS[self.current_lang]['base'], font_size='10sp', font_name=TAMIL_FONT, color=(0.7, 0.7, 0.7, 1))
        self.base_input = TextInput(text="35", multiline=False, input_filter='float', halign='center', font_size='15sp')
        b_box.add_widget(self.base_lbl)
        b_box.add_widget(self.base_input)

        km_p_box = BoxLayout(orientation='vertical')
        self.km_lbl = Label(text=TRANSLATIONS[self.current_lang]['per_km'], font_size='10sp', font_name=TAMIL_FONT, color=(0.7, 0.7, 0.7, 1))
        self.km_input = TextInput(text="18", multiline=False, input_filter='float', halign='center', font_size='15sp')
        km_p_box.add_widget(self.km_lbl)
        km_p_box.add_widget(self.km_input)

        wait_p_box = BoxLayout(orientation='vertical')
        self.wait_lbl = Label(text=TRANSLATIONS[self.current_lang]['wait_min'], font_size='10sp', font_name=TAMIL_FONT, color=(0.7, 0.7, 0.7, 1))
        self.wait_input = TextInput(text="1.5", multiline=False, input_filter='float', halign='center', font_size='15sp')
        wait_p_box.add_widget(self.wait_lbl)
        wait_p_box.add_widget(self.wait_input)

        settings_grid.add_widget(b_box)
        settings_grid.add_widget(km_p_box)
        settings_grid.add_widget(wait_p_box)
        main_layout.add_widget(settings_grid)

        # மொத்தக் கட்டணம்
        fare_box = BoxLayout(orientation='vertical', size_hint=(1, 0.25))
        self.fare_title_lbl = Label(text=TRANSLATIONS[self.current_lang]['fare'], font_size='14sp', font_name=TAMIL_FONT, color=(0.7, 0.7, 0.7, 1))
        fare_box.add_widget(self.fare_title_lbl)
        self.fare_display = Label(
            text="Rs. 35.00",
            font_size='50sp',
            bold=True,
            color=(0.1, 1.0, 0.3, 1)
        )
        fare_box.add_widget(self.fare_display)
        main_layout.add_widget(fare_box)

        # தூரம், நேரம், வெயிட்டிங்
        metrics_grid = GridLayout(cols=3, size_hint=(1, 0.16), spacing=5)

        d_box = BoxLayout(orientation='vertical')
        self.dist_lbl = Label(text=TRANSLATIONS[self.current_lang]['distance'], font_size='11sp', font_name=TAMIL_FONT, color=(0.7, 0.7, 0.7, 1))
        self.km_display = Label(text="0.00 KM", font_size='18sp', bold=True, color=(1, 0.8, 0.2, 1))
        d_box.add_widget(self.dist_lbl)
        d_box.add_widget(self.km_display)

        t_box = BoxLayout(orientation='vertical')
        self.time_lbl = Label(text=TRANSLATIONS[self.current_lang]['trip_time'], font_size='11sp', font_name=TAMIL_FONT, color=(0.7, 0.7, 0.7, 1))
        self.time_display = Label(text="00:00", font_size='18sp', bold=True, color=(0.3, 0.8, 1, 1))
        t_box.add_widget(self.time_lbl)
        t_box.add_widget(self.time_display)

        w_box = BoxLayout(orientation='vertical')
        self.w_time_lbl = Label(text=TRANSLATIONS[self.current_lang]['wait_time'], font_size='11sp', font_name=TAMIL_FONT, color=(0.7, 0.7, 0.7, 1))
        self.wait_display = Label(text="00:00", font_size='18sp', bold=True, color=(1, 0.4, 0.4, 1))
        w_box.add_widget(self.w_time_lbl)
        w_box.add_widget(self.wait_display)

        metrics_grid.add_widget(d_box)
        metrics_grid.add_widget(t_box)
        metrics_grid.add_widget(w_box)
        main_layout.add_widget(metrics_grid)

        # பட்டன்கள் (START, WAIT, RESET)
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.13), spacing=10)

        self.start_btn = Button(
            text=TRANSLATIONS[self.current_lang]['start'],
            font_size='16sp',
            bold=True,
            font_name=TAMIL_FONT,
            background_normal='',
            background_color=(0.15, 0.68, 0.38, 1)
        )
        self.start_btn.bind(on_press=self.toggle_meter)

        self.wait_btn = Button(
            text=TRANSLATIONS[self.current_lang]['wait_on'],
            font_size='14sp',
            bold=True,
            font_name=TAMIL_FONT,
            background_normal='',
            background_color=(0.8, 0.5, 0.1, 1)
        )
        self.wait_btn.bind(on_press=self.toggle_waiting)

        self.reset_btn = Button(
            text=TRANSLATIONS[self.current_lang]['reset'],
            font_size='15sp',
            bold=True,
            font_name=TAMIL_FONT,
            background_normal='',
            background_color=(0.85, 0.25, 0.2, 1)
        )
        self.reset_btn.bind(on_press=self.reset_meter)

        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.wait_btn)
        btn_layout.add_widget(self.reset_btn)
        main_layout.add_widget(btn_layout)

        # QR பட்டன்
        self.qr_btn = Button(
            text=TRANSLATIONS[self.current_lang]['qr_btn'],
            font_size='16sp',
            bold=True,
            font_name=TAMIL_FONT,
            size_hint=(1, 0.12),
            background_normal='',
            background_color=(0.2, 0.5, 0.9, 1)
        )
        self.qr_btn.bind(on_press=self.show_qr_popup)
        main_layout.add_widget(self.qr_btn)

        Clock.schedule_interval(self.update_meter, 1.0)
        return main_layout

    def toggle_language(self, instance):
        self.current_lang = 'en' if self.current_lang == 'ta' else 'ta'
        t = TRANSLATIONS[self.current_lang]
        f = TAMIL_FONT if self.current_lang == 'ta' else 'Roboto'

        self.title_label.text = t['title']
        self.title_label.font_name = f
        self.lang_btn.text = t['lang_btn']

        self.base_lbl.text = t['base']
        self.base_lbl.font_name = f
        self.km_lbl.text = t['per_km']
        self.km_lbl.font_name = f
        self.wait_lbl.text = t['wait_min']
        self.wait_lbl.font_name = f

        self.fare_title_lbl.text = t['fare']
        self.fare_title_lbl.font_name = f

        self.dist_lbl.text = t['distance']
        self.dist_lbl.font_name = f
        self.time_lbl.text = t['trip_time']
        self.time_lbl.font_name = f
        self.w_time_lbl.text = t['wait_time']
        self.w_time_lbl.font_name = f

        self.start_btn.text = t['stop'] if self.is_running else t['start']
        self.start_btn.font_name = f

        self.wait_btn.text = t['wait_off'] if self.is_waiting else t['wait_on']
        self.wait_btn.font_name = f

        self.reset_btn.text = t['reset']
        self.reset_btn.font_name = f
        self.qr_btn.text = t['qr_btn']
        self.qr_btn.font_name = f

    def toggle_meter(self, instance):
        t = TRANSLATIONS[self.current_lang]
        if not self.is_running:
            self.is_running = True
            self.start_btn.text = t['stop']
            self.start_btn.background_color = (0.9, 0.2, 0.2, 1)
        else:
            self.is_running = False
            self.is_waiting = False
            self.start_btn.text = t['start']
            self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
            self.wait_btn.text = t['wait_on']
            self.wait_btn.background_color = (0.8, 0.5, 0.1, 1)
            self.show_qr_popup(None)

    def toggle_waiting(self, instance):
        t = TRANSLATIONS[self.current_lang]
        if self.is_running:
            self.is_waiting = not self.is_waiting
            if self.is_waiting:
                self.wait_btn.text = t['wait_off']
                self.wait_btn.background_color = (0.3, 0.3, 0.8, 1)
            else:
                self.wait_btn.text = t['wait_on']
                self.wait_btn.background_color = (0.8, 0.5, 0.1, 1)

    def reset_meter(self, instance):
        t = TRANSLATIONS[self.current_lang]
        self.is_running = False
        self.is_waiting = False
        self.trip_seconds = 0
        self.wait_seconds = 0
        self.distance_km = 0.0

        self.start_btn.text = t['start']
        self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
        self.wait_btn.text = t['wait_on']
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
        t = TRANSLATIONS[self.current_lang]
        f = TAMIL_FONT if self.current_lang == 'ta' else 'Roboto'
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
            text=f"{t['pay_label']}{final_amt}",
            font_size='18sp',
            bold=True,
            font_name=f,
            size_hint=(1, 0.15),
            color=(0.1, 1, 0.3, 1)
        ))
        
        qr_image = Image(source=qr_path, size_hint=(1, 0.7))
        qr_image.reload()
        popup_layout.add_widget(qr_image)

        close_btn = Button(
            text=t['close'],
            font_size='16sp',
            bold=True,
            font_name=f,
            size_hint=(1, 0.15),
            background_normal='',
            background_color=(0.85, 0.25, 0.2, 1)
        )
        popup_layout.add_widget(close_btn)

        popup = Popup(
            title=t['popup_title'],
            title_font=f,
            content=popup_layout,
            size_hint=(0.9, 0.75),
            auto_dismiss=False
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    TaxiMeterApp().run()
