#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
import os
import gettext
import locale
import math

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# Import GLib for the timer and Adw for the animation
from gi.repository import Gtk, Adw, Gdk, GLib

# --- i18n Setup ---
WIDGET_NAME = "linexin-installer-welcome-widget"
LOCALE_DIR = "/usr/share/locale"
locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain(WIDGET_NAME, LOCALE_DIR)
gettext.bindtextdomain(WIDGET_NAME, LOCALE_DIR)
gettext.textdomain(WIDGET_NAME)
_ = gettext.gettext


class WelcomeWidget(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "images", "logo.png")

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        # Add CSS for enhanced styling
        self.setup_custom_css()

        # Create main container with some breathing room
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=40)
        self.main_container.set_margin_top(60)
        self.main_container.set_margin_bottom(60)
        self.main_container.set_margin_start(80)
        self.main_container.set_margin_end(80)
        self.main_container.set_valign(Gtk.Align.CENTER)
        self.main_container.set_halign(Gtk.Align.CENTER)
        
        # Add CSS class for styling
        self.main_container.add_css_class("main_widget_container")

        # Welcome text container - fixed height to prevent layout shifts
        text_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        text_container.set_halign(Gtk.Align.CENTER)
        text_container.set_valign(Gtk.Align.CENTER)
        text_container.set_size_request(-1, 80)

        # Static welcome label
        self.welcome_label = Gtk.Label()
        self.welcome_label.add_css_class("welcome_text")
        self.welcome_label.set_markup(f'<span size="xx-large" weight="bold">{_("Welcome to")}</span>')
        self.welcome_label.set_halign(Gtk.Align.CENTER)
        self.welcome_label.set_valign(Gtk.Align.CENTER)
        text_container.append(self.welcome_label)

        self.main_container.append(text_container)

        # Logo
        self.logo_container = Gtk.Box(halign=Gtk.Align.CENTER)
        self.welcome_image = Gtk.Picture.new_for_filename(image_path)
        self.welcome_image.set_can_shrink(True)
        self.welcome_image.set_halign(Gtk.Align.CENTER)
        self.welcome_image.set_valign(Gtk.Align.CENTER)
        self.welcome_image.add_css_class("logo_image")
        self.welcome_image.set_size_request(250, 250)
        self.logo_container.append(self.welcome_image)
        self.main_container.append(self.logo_container)

        # Button container with hover effects
        button_container = Gtk.Box(halign=Gtk.Align.CENTER, spacing=20)
        button_container.set_margin_top(40)
        
        self.btn_install = Gtk.Button(label=_("Begin"))
        self.btn_install.add_css_class("suggested-action")
        self.btn_install.add_css_class("proceed_button")
        self.btn_install.add_css_class("animated_button")
        self.btn_install.set_size_request(200, 50)
        
        # Add hover effects
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self.on_button_hover_enter)
        hover_controller.connect("leave", self.on_button_hover_leave)
        self.btn_install.add_controller(hover_controller)
        
        button_container.append(self.btn_install)
        self.main_container.append(button_container)

        self.append(self.main_container)
        
        # Show everything immediately with entrance animation
        self.main_container.set_opacity(0)
        
        # Connect to the map signal to trigger entrance animation when widget becomes visible
        self.connect("map", self.on_widget_mapped)

    def setup_custom_css(self):
        """Setup enhanced CSS for modern look and animations"""
        css_provider = Gtk.CssProvider()
        css_data = """
        .main_widget_container {
            transition: all 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        .welcome_text {
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            transition: all 0.5s ease;
        }
        
        .subtitle_text {
            font-style: italic;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .logo_image {
            transition: opacity 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .animated_button {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 25px;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            box-shadow: 0 4px 12px rgba(201, 148, 218, 0.3);
        }
        
        .animated_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(201, 148, 218, 0.3);
        }
        
        .animated_button:active {
            transform: translateY(1px);
            box-shadow: 0 2px 8px rgba(201, 148, 218, 0.3);
        }
        
        /* Pulse animation for active elements */
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .pulse-animation {
            animation: pulse 2s ease-in-out infinite;
        }
        """
        css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_widget_mapped(self, widget):
        """Called when widget is mapped (becomes visible) - just show entrance animation"""
        # Small delay to ensure everything is rendered
        GLib.timeout_add(200, self.start_entrance_animation)
    
    def start_entrance_animation(self):
        """Start the smooth entrance animation - no language cycling afterwards"""
        def animation_callback(value, data):
            self.main_container.set_opacity(value)
        
        # Create the animation target
        target = Adw.CallbackAnimationTarget.new(animation_callback, None)
        
        # Create the timed animation with smooth easing
        animation = Adw.TimedAnimation.new(
            self.main_container,
            0.0,  # Start value (fully transparent)
            1.0,  # End value (fully opaque)
            1200, # Duration in milliseconds
            target
        )
        
        # Use a smooth easing function for natural motion
        animation.set_easing(Adw.Easing.EASE_OUT_QUAD)
        
        # Play the animation - no completion handler needed
        animation.play()
        
        # Alternative approach using margin animations for zoom effect
        self.animate_entrance_with_components()
        
        return False

    def animate_entrance_with_components(self):
        """Animate individual components with staggered timing for smoother effect"""
        # Start with larger margins (simulating zoom)
        initial_margin = 80
        self.main_container.set_margin_top(initial_margin + 60)
        self.main_container.set_margin_bottom(initial_margin + 60)
        self.main_container.set_margin_start(initial_margin + 80)
        self.main_container.set_margin_end(initial_margin + 80)
        
        # Animate margins back to normal
        def margin_callback(value, data):
            current_margin = initial_margin * (1 - value)
            self.main_container.set_margin_top(int(current_margin + 60))
            self.main_container.set_margin_bottom(int(current_margin + 60))
            self.main_container.set_margin_start(int(current_margin + 80))
            self.main_container.set_margin_end(int(current_margin + 80))
        
        margin_target = Adw.CallbackAnimationTarget.new(margin_callback, None)
        margin_animation = Adw.TimedAnimation.new(
            self.main_container,
            0.0,
            1.0,
            1200,
            margin_target
        )
        margin_animation.set_easing(Adw.Easing.EASE_OUT_EXPO)
        margin_animation.play()

    def on_button_hover_enter(self, controller, x, y):
        """Enhanced hover enter effect"""
        self.btn_install.add_css_class("pulse-animation")

    def on_button_hover_leave(self, controller):
        """Enhanced hover leave effect"""
        self.btn_install.remove_css_class("pulse-animation")


class EnhancedWelcomeApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.linexin.installer.welcome")
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        # Create window with modern styling
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("LineXin OS Installer")
        self.win.set_default_size(800, 600)
        
        # Create and add welcome widget
        self.welcome_widget = WelcomeWidget()
        self.win.set_content(self.welcome_widget)
        
        # The widget will handle its own animation via the "map" signal
        self.win.present()


if __name__ == "__main__":
    app = EnhancedWelcomeApp()
    app.run(None)

