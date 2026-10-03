from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class KanakkuMobileApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.lbl_title = Label(text="E-Auto Kanakku App", font_size='24sp', size_hint=(1, 0.2))
        layout.add_widget(self.lbl_title)
        
        self.input_vasool = TextInput(hint_text="Vasool Thogai (Rs.)", multiline=False, input_filter='int', size_hint=(1, 0.2))
        layout.add_widget(self.input_vasool)
        
        self.input_selavu = TextInput(hint_text="Selavu Thogai (Rs.)", multiline=False, input_filter='int', size_hint=(1, 0.2))
        layout.add_widget(self.input_selavu)
        
        self.btn_calc = Button(text="Meethi & Laabam Kaan", background_color=(0, 0.7, 0.2, 1), size_hint=(1, 0.2))
        self.btn_calc.bind(on_press=self.calculate)
        layout.add_widget(self.btn_calc)
        
        self.lbl_result = Label(text="Meethi: Rs. 0", font_size='20sp', size_hint=(1, 0.2))
        layout.add_widget(self.lbl_result)
        
        return layout

    def calculate(self, instance):
        v = int(self.input_vasool.text) if self.input_vasool.text else 0
        s = int(self.input_selavu.text) if self.input_selavu.text else 0
        m = v - s
        status = "Nalla Laabam" if m >= 1400 else "Kuraintha Laabam"
        self.lbl_result.text = f"Meethi: Rs. {m}\n({status})"

if __name__ == '__main__':
    KanakkuMobileApp().run()
