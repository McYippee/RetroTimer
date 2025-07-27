from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse
import pygame
import os
import math
import time

# Initialize pygame mixer for sounds
pygame.mixer.init()

def play_sound(filename):
    """Play a sound file if it exists."""
    if os.path.exists(filename):
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

class AnimatedGlow:
    """Utility to create pulsing color animations."""
    @staticmethod
    def pulse(base_color, t):
        factor = 0.8 + 0.2 * math.sin(t * 2)
        return [c * factor for c in base_color[:3]] + [base_color[3]]

class NeonTextInput(TextInput):
    def __init__(self, glow_color=(0, 1, 1, 0.7), **kwargs):
        super().__init__(**kwargs)
        self.glow_color = glow_color
        with self.canvas.before:
            self.color_instruction = Color(*self.glow_color)
            self.bg_rect = RoundedRectangle(radius=[20])
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (1, 1, 1, 1)
        self.bind(pos=self.update_bg, size=self.update_bg)
        Clock.schedule_interval(self.animate_glow, 1/30)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def animate_glow(self, dt):
        t = time.time()
        self.color_instruction.rgba = AnimatedGlow.pulse(self.glow_color, t)

class CircleButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 0, 1)
        self.circle_color = Color(1, 0, 0.4, 1)
        with self.canvas.before:
            self.circle = Ellipse()
        self.bind(pos=self.update_circle, size=self.update_circle)
        Clock.schedule_interval(self.animate_glow, 1/30)

    def update_circle(self, *args):
        d = min(self.width, self.height)
        self.circle.pos = (self.center_x - d / 2, self.center_y - d / 2)
        self.circle.size = (d, d)

    def animate_glow(self, dt):
        t = time.time()
        pulsing_color = AnimatedGlow.pulse((1, 0, 0.4, 1), t)
        self.circle_color.rgba = pulsing_color

class WorkoutUI(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        pixel_font = 'pixel_font.ttf'

        # Background image
        self.bg = Image(source='bg_pixel.png', allow_stretch=True, keep_ratio=False)
        self.add_widget(self.bg)

        self.main_layout = BoxLayout(orientation='vertical',
                                     spacing=20,
                                     padding=20,
                                     size_hint=(0.85, 0.85),
                                     pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(self.main_layout)

        label_style = {'font_size': 20, 'color': (1, 1, 0, 1), 'font_name': pixel_font}

        # Title
        self.main_layout.add_widget(Label(text='RETRO TIMER', font_size=28,
                                          color=(0, 1, 1, 1), font_name=pixel_font))

        # Sets input
        self.main_layout.add_widget(Label(text='SETS:', **label_style))
        self.sets_input = NeonTextInput(
            text='3', multiline=False, halign='center', font_size=22,
            font_name=pixel_font, glow_color=(1, 1, 0, 0.6)
        )
        self.main_layout.add_widget(self.sets_input)

        # Rest input
        self.main_layout.add_widget(Label(text='REST (S):', **label_style))
        self.rest_input = NeonTextInput(
            text='60', multiline=False, halign='center', font_size=22,
            font_name=pixel_font, glow_color=(0, 1, 0.8, 0.6)
        )
        self.main_layout.add_widget(self.rest_input)

        # Start/DONE button
        self.start_button = CircleButton(text='START')
        self.start_button.font_size = 16
        self.start_button.font_name = pixel_font
        self.start_button.size_hint = (None, None)
        self.start_button.size = (140, 140)
        self.start_button.pos_hint = {'center_x': 0.5}
        self.start_button.bind(on_press=self.start_workout)
        self.main_layout.add_widget(self.start_button)

        # Status label
        self.status_label = Label(text='', font_size=20, color=(1, 1, 1, 1), font_name=pixel_font)
        self.main_layout.add_widget(self.status_label)

        # Workout state variables
        self.current_set = 0
        self.total_sets = 0
        self.rest_time = 0
        self.timer_event = None
        self.remaining = 0

        # Bind global click sound
        self.bind(on_touch_down=self.global_click)

    def global_click(self, instance, touch):
        """Play click sound for buttons and text fields."""
        for child in self.walk():
            if (isinstance(child, Button) or isinstance(child, TextInput)) and child.collide_point(*touch.pos):
                play_sound('click.wav')  # or click.mp3
                break


    def reset_workout(self):
        """Reset the app state so another workout can start."""
        self.current_set = 0
        self.status_label.text = ""
        self.start_button.text = "START"
        self.start_button.unbind(on_press=self.next_set)
        self.start_button.bind(on_press=self.start_workout)

    def start_workout(self, instance):
        self.current_set = 1
        self.total_sets = int(self.sets_input.text)
        self.rest_time = int(self.rest_input.text)
        self.status_label.text = f"SET {self.current_set}\nPRESS WHEN DONE"
        self.start_button.text = "DONE"
        self.start_button.unbind(on_press=self.start_workout)
        self.start_button.bind(on_press=self.next_set)

    def next_set(self, instance):
        if self.current_set < self.total_sets:
            # Play bell at start of rest
            play_sound('bell.mp3')
            self.status_label.text = f"REST: {self.rest_time}"
            self.remaining = self.rest_time
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)
        else:
            self.status_label.text = "WORKOUT DONE!"
            play_sound('finish.mp3')
            # Reset after 3 seconds so user can start a new workout
            Clock.schedule_once(lambda dt: self.reset_workout(), 3)

    def update_timer(self, dt):
        self.remaining -= 1
        self.status_label.text = f"REST: {self.remaining}"
        if self.remaining <= 0:
            self.timer_event.cancel()
            # Play rest-end sound
            play_sound('rest_end.mp3')
            play_sound('start_lifting.mp3')
            self.current_set += 1
            if self.current_set <= self.total_sets:
                self.status_label.text = f"SET {self.current_set}\nPRESS WHEN DONE"
            else:
                self.status_label.text = "WORKOUT DONE!"
                play_sound('finish.mp3')
                # Reset after 3 seconds
                Clock.schedule_once(lambda dt: self.reset_workout(), 3)

class WorkoutApp(App):
    def build(self):
        return WorkoutUI()

if __name__ == '__main__':
    WorkoutApp().run()
