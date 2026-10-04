from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window

# பின்னணி நிறம் (Dark Theme)
Window.clearcolor = (0.08, 0.08, 0.1, 1)

class TaxiMeterApp(App):
    def build(self):
        self.is_running = False
        self.seconds = 0
        self.distance_km = 0.0
        
        # கட்டண விவரங்கள் (கட்டண விகிதத்தை இங்கு மாற்றிக்கொள்ளலாம்)
        self.base_fare = 35.0      # முதல் 1.8 கி.மீ-க்கு ஆரம்பக் கட்டணம்
        self.base_km = 1.8
        self.rate_per_km = 18.0   # அதன் பின் ஒரு கி.மீ-க்கு கட்டணம்
        self.current_fare = self.base_fare

        # முதன்மை லேஅவுட்
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # தலைப்பு
        title_label = Label(
            text="DIGITAL TAXI METER",
            font_size='22sp',
            bold=True,
            size_hint=(1, 0.1),
            color=(0.9, 0.9, 0.9, 1)
        )
        main_layout.add_widget(title_label)

        # பெரிய கட்டணக் காட்சி (Digital Display Card)
        fare_box = BoxLayout(orientation='vertical', size_hint=(1, 0.35))
        self.fare_title = Label(text="TOTAL FARE", font_size='16sp', color=(0.7, 0.7, 0.7, 1))
        self.fare_display = Label(
            text=f"Rs. {self.current_fare:.2f}",
            font_size='52sp',
            bold=True,
            color=(0.1, 1.0, 0.3, 1)  # நியான் பச்சை நிறம்
        )
        fare_box.add_widget(self.fare_title)
        fare_box.add_widget(self.fare_display)
        main_layout.add_widget(fare_box)

        # கி.மீ மற்றும் நேரம் காட்டும் பகுதி (Grid Display)
        metrics_grid = GridLayout(cols=2, size_hint=(1, 0.25), spacing=10)

        # கி.மீ பெட்டி
        km_box = BoxLayout(orientation='vertical')
        km_title = Label(text="DISTANCE", font_size='14sp', color=(0.7, 0.7, 0.7, 1))
        self.km_display = Label(text="0.00 KM", font_size='28sp', bold=True, color=(1, 0.8, 0.2, 1))
        km_box.add_widget(km_title)
        km_box.add_widget(self.km_display)

        # நேரப் பெட்டி
        time_box = BoxLayout(orientation='vertical')
        time_title = Label(text="TRIP TIME", font_size='14sp', color=(0.7, 0.7, 0.7, 1))
        self.time_display = Label(text="00:00", font_size='28sp', bold=True, color=(0.3, 0.8, 1, 1))
        time_box.add_widget(time_title)
        time_box.add_widget(self.time_display)

        metrics_grid.add_widget(km_box)
        metrics_grid.add_widget(time_box)
        main_layout.add_widget(metrics_grid)

        # இயக்கப் பொத்தான்கள் (Controls)
        btn_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), spacing=15)

        self.start_btn = Button(
            text="START",
            font_size='20sp',
            bold=True,
            background_normal='',
            background_color=(0.15, 0.68, 0.38, 1)
        )
        self.start_btn.bind(on_press=self.toggle_meter)

        self.reset_btn = Button(
            text="RESET",
            font_size='20sp',
            bold=True,
            background_normal='',
            background_color=(0.85, 0.25, 0.2, 1)
        )
        self.reset_btn.bind(on_press=self.reset_meter)

        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.reset_btn)
        main_layout.add_widget(btn_layout)

        # டைமர் ஈவென்ட் (வினாடிக்கு ஒருமுறை இயங்கும்)
        Clock.schedule_interval(self.update_trip, 1.0)

        return main_layout

    def toggle_meter(self, instance):
        if not self.is_running:
            self.is_running = True
            self.start_btn.text = "STOP"
            self.start_btn.background_color = (0.9, 0.5, 0.1, 1)
        else:
            self.is_running = False
            self.start_btn.text = "START"
            self.start_btn.background_color = (0.15, 0.68, 0.38, 1)

    def reset_meter(self, instance):
        self.is_running = False
        self.seconds = 0
        self.distance_km = 0.0
        self.current_fare = self.base_fare
        self.start_btn.text = "START"
        self.start_btn.background_color = (0.15, 0.68, 0.38, 1)
        
        self.fare_display.text = f"Rs. {self.current_fare:.2f}"
        self.km_display.text = "0.00 KM"
        self.time_display.text = "00:00"

    def update_trip(self, dt):
        if self.is_running:
            self.seconds += 1
            mins = self.seconds // 60
            secs = self.seconds % 60
            self.time_display.text = f"{mins:02d}:{secs:02d}"

            # டெஸ்டிங்கிற்காக தானியங்கி தூர அதிகரிப்பு (சுமார் 30 கி.மீ/மணி வேகம்)
            self.distance_km += 0.0083
            self.km_display.text = f"{self.distance_km:.2f} KM"

            # கட்டணக் கணக்கீடு
            if self.distance_km <= self.base_km:
                self.current_fare = self.base_fare
            else:
                extra_km = self.distance_km - self.base_km
                self.current_fare = self.base_fare + (extra_km * self.rate_per_km)

            self.fare_display.text = f"Rs. {self.current_fare:.2f}"

if __name__ == '__main__':
    TaxiMeterApp().run()
