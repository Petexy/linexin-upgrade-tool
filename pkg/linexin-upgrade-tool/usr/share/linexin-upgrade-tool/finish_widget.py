#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
import os
import gettext
import locale
import subprocess

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# Import GLib for the timer and Adw for the animation
from gi.repository import Gtk, Adw, Gdk, GLib
from simple_localization_manager import get_localization_manager
_ = get_localization_manager().get_text

# --- i18n Setup ---
WIDGET_NAME = "linexin-installer-finish-widget"
LOCALE_DIR = "/usr/share/locale"
locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain(WIDGET_NAME, LOCALE_DIR)
gettext.bindtextdomain(WIDGET_NAME, LOCALE_DIR)
gettext.textdomain(WIDGET_NAME)
_ = gettext.gettext


class FinishWidget(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        get_localization_manager().register_widget(self)

        self.initial_animation_done = False
        self.animation_scheduled = False

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        # Add CSS for enhanced styling
        self.setup_custom_css()

        # Create main container with some breathing room
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.main_container.set_margin_top(60)
        self.main_container.set_margin_bottom(60)
        self.main_container.set_margin_start(80)
        self.main_container.set_margin_end(80)
        self.main_container.set_valign(Gtk.Align.CENTER)
        self.main_container.set_halign(Gtk.Align.CENTER)
        
        # Add CSS class for animation
        self.main_container.add_css_class("main_widget_container")

        # Success icon (checkmark)
        self.success_icon = Gtk.Image.new_from_icon_name("checkbox-checked-symbolic")
        self.success_icon.set_pixel_size(120)
        self.success_icon.add_css_class("success_icon")
        self.success_icon.set_halign(Gtk.Align.CENTER)
        self.success_icon.set_margin_bottom(20)
        self.main_container.append(self.success_icon)

        # Main title
        self.title_label = Gtk.Label()
        self.title_label.add_css_class("finish_title")
        self.title_label.set_markup('<span size="xx-large" weight="bold">Upgrade has finished successfully!</span>')
        self.title_label.set_halign(Gtk.Align.CENTER)
        self.title_label.set_valign(Gtk.Align.CENTER)
        self.title_label.set_wrap(True)
        self.title_label.set_justify(Gtk.Justification.CENTER)
        self.main_container.append(self.title_label)

        # Subtitle with instructions
        self.subtitle_label = Gtk.Label()
        self.subtitle_label.add_css_class("finish_subtitle")
        localization_manager = get_localization_manager()
        self.subtitle_label.set_markup(f'<span size="large">{localization_manager.get_text("Welcome to Linexin v1.1")}</span>')
        self.subtitle_label.set_halign(Gtk.Align.CENTER)
        self.subtitle_label.set_valign(Gtk.Align.CENTER)
        self.subtitle_label.set_wrap(True)
        self.subtitle_label.set_justify(Gtk.Justification.CENTER)
        self.subtitle_label.set_margin_top(10)
        self.subtitle_label.set_margin_bottom(30)
        self.main_container.append(self.subtitle_label)

        # Button container
        button_container = Gtk.Box(halign=Gtk.Align.CENTER, spacing=20)
        button_container.set_margin_top(20)
        
        # Back button
        self.btn_back = Gtk.Button(label=_("Back"))
        self.btn_back.add_css_class("back_button")
        self.btn_back.add_css_class("buttons_all")
        self.btn_back.set_size_request(150, 50)
        self.btn_back.set_visible(False)
        
        # Finish button with special styling
        self.btn_finish = Gtk.Button(label=_("Finish"))
        self.btn_finish.add_css_class("suggested-action")
        self.btn_finish.add_css_class("finish_button")
        self.btn_finish.add_css_class("animated_button")
        self.btn_finish.set_size_request(200, 50)
        
        # Connect the finish action
        self.btn_finish.connect("clicked", self.on_finish_clicked)
        
        # Add hover effects for finish button
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self.on_button_hover_enter)
        hover_controller.connect("leave", self.on_button_hover_leave)
        self.btn_finish.add_controller(hover_controller)
        
        button_container.append(self.btn_back)
        button_container.append(self.btn_finish)
        self.main_container.append(button_container)

        self.append(self.main_container)
        
        # Initially hide everything for the zoom animation
        self.main_container.set_opacity(0)
        
        # Connect to the map signal to trigger animation when widget becomes visible
        self.connect("map", self.on_widget_mapped)

    def setup_custom_css(self):
        """Setup enhanced CSS for modern look and animations"""
        css_provider = Gtk.CssProvider()
        css_data = """
        .main_widget_container {
            transition: all 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        .success_icon {
            color: #4CAF50;
            text-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
        }
        
        .finish_title {
            color: #2E7D32;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            transition: all 0.5s ease;
        }
        
        .finish_subtitle {
            opacity: 0.9;
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
            transition: all 0.5s ease;
        }
        
        .finish_button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 25px;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .finish_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        .finish_button:active {
            transform: translateY(1px);
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4);
        }
        
        .back_button {
            background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
            color: #333;
            border: 1px solid #ccc;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 25px;
            font-weight: bold;
            text-shadow: none;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .back_button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            background: linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%);
        }
        
        .back_button:active {
            transform: translateY(1px);
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.1);
        }
        
        .animated_button {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Pulse animation for button */
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .pulse-animation {
            animation: pulse 2s ease-in-out infinite;
        }
        
        /* Success icon animation */
        @keyframes checkmark {
            0% { 
                transform: scale(0) rotate(-45deg);
                opacity: 0;
            }
            50% {
                transform: scale(1.2) rotate(0deg);
            }
            100% { 
                transform: scale(1) rotate(0deg);
                opacity: 1;
            }
        }
        
        .success-animation {
            animation: checkmark 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
        }
        """
        css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_widget_mapped(self, widget):
        """Called when widget is mapped (becomes visible)"""
        if not self.animation_scheduled and not self.initial_animation_done:
            self.animation_scheduled = True
            # Small delay to ensure everything is rendered
            GLib.timeout_add(200, self.start_entrance_animation)
    
    def start_entrance_animation(self):
        """Start the smooth zoom-out entrance animation after widget is visible"""
        if self.initial_animation_done:
            return False
            
        self.initial_animation_done = True
        self.animation_scheduled = False
        
        # Create a smooth zoom-out effect with opacity fade
        def animation_callback(value, data):
            # Calculate scale: from 1.3 to 1.0
            scale = 1.3 - (0.3 * value)
            
            # Apply opacity
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
        
        # Connect completion handler to animate the success icon
        animation.connect("done", self.on_entrance_animation_complete)
        
        # Play the animation
        animation.play()
        
        # Alternative approach using margin animation for zoom effect
        self.animate_entrance_with_margins()
        
        return False

    def animate_entrance_with_margins(self):
        """Animate margins to simulate zoom effect"""
        # Start with larger margins (simulating zoom)
        initial_margin = 60  # Smaller than welcome widget for subtler effect
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

    def on_entrance_animation_complete(self, animation):
        """Called when the entrance animation completes"""
        # Animate the success icon with a special effect
        self.success_icon.add_css_class("success-animation")
        
        # Add subtle pulse to the finish button after a delay
        GLib.timeout_add(800, self.start_button_pulse)

    def start_button_pulse(self):
        """Add a subtle pulse effect to the finish button"""
        self.btn_finish.add_css_class("pulse-animation")
        return False

    def on_button_hover_enter(self, controller, x, y):
        """Enhanced hover enter effect"""
        self.btn_finish.remove_css_class("pulse-animation")

    def on_button_hover_leave(self, controller):
        """Enhanced hover leave effect"""
        self.btn_finish.add_css_class("pulse-animation")

    def on_finish_clicked(self, button):
        """Handle finish button click with fade-out animation"""
        # Disable buttons to prevent multiple clicks
        self.btn_finish.set_sensitive(False)
        self.btn_back.set_sensitive(False)
        
        # Start the fade-out animation
        self.start_fade_out_animation()

    def start_fade_out_animation(self):
        """Animate the entire application window fading out"""
        # Get the main application window
        app_window = self.get_root()
        
        if app_window:
            # Create fade-out animation callback
            def fade_callback(value, data):
                # Calculate opacity: from 1.0 to 0.0
                opacity = 1.0 - value
                app_window.set_opacity(opacity)
            
            # Create the animation target
            target = Adw.CallbackAnimationTarget.new(fade_callback, None)
            
            # Create the timed animation with ease-in easing (starts slow, speeds up)
            animation = Adw.TimedAnimation.new(
                app_window,
                0.0,  # Start value
                1.0,  # End value (full fade)
                300, # Duration in milliseconds (2 seconds)
                target
            )
            
            # Use ease-in easing (starts slow, accelerates)
            animation.set_easing(Adw.Easing.EASE_IN_QUAD)
            
            # Connect completion handler to close the application
            animation.connect("done", self.on_fade_out_complete)
            
            # Play the animation
            animation.play()

    def on_fade_out_complete(self, animation):
        """Called when fade-out animation completes - close the application"""
        app_window = self.get_root()
        if app_window:
            # Get the application from the window
            app = app_window.get_application()
            if app:
                # Quit the application gracefully
                app.quit()
            else:
                # Fallback: close the window
                app_window.close()


class FinishApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.linexin.installer.finish")
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        # Create window
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("Upgrade Complete")
        self.win.set_default_size(800, 600)
        
        # Create and add finish widget
        self.finish_widget = FinishWidget()
        self.win.set_content(self.finish_widget)
        
        self.win.present()


if __name__ == "__main__":
    app = FinishApp()
    app.run(None)