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
from simple_localization_manager import get_localization_manager, _

class FinishWidget(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        get_localization_manager().register_widget(self)

        self.initial_animation_done = False
        self.animation_scheduled = False
        
        # Flags
        self.requires_restart = False

        # --- Layout Setup ---
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_hexpand(True)
        self.set_vexpand(True)
        
        # Setup CSS
        self.setup_custom_css()

        # --- Main Layout Architecture: Clamp -> Glass Card ---
        
        # 1. Clamp for centering and max-width control
        self.clamp = Adw.Clamp()
        self.clamp.set_maximum_size(700)
        self.clamp.set_tightening_threshold(600)
        self.append(self.clamp)

        # 2. Main Glass Card Container
        self.card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
        self.card_box.add_css_class("finish-glass-card")
        self.card_box.set_margin_top(40) # Spacing from top
        self.card_box.set_margin_bottom(40)
        self.card_box.set_margin_start(20)
        self.card_box.set_margin_end(20)
        self.clamp.set_child(self.card_box)

        # --- Content Construction ---

        # 1. Hero Icon Area (Animated)
        self.icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.icon_box.set_halign(Gtk.Align.CENTER)
        self.icon_box.set_margin_top(20)
        
        # We can use a large symbolic icon or an image if available
        # Using a composed overlaid icon for a "premium" feel
        self.hero_icon = Gtk.Image.new_from_icon_name("system-software-install-finished-symbolic") # standard fallback
        # Try to find a better icon or composition
        if Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).has_icon("object-select-symbolic"):
             self.hero_icon.set_from_icon_name("object-select-symbolic")
        
        self.hero_icon.set_pixel_size(96)
        self.hero_icon.add_css_class("hero-icon")
        self.hero_icon.add_css_class("accent-gradient-text") # Gradient effect via text clip if supported, else color
        
        self.icon_box.append(self.hero_icon)
        self.card_box.append(self.icon_box)

        # 2. Text Area
        self.text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.text_box.set_halign(Gtk.Align.CENTER)
        
        self.title_label = Gtk.Label()
        self.title_label.set_markup(f'<span size="24000" weight="900" foreground="#ffffff">{_("All Done!")}</span>')
        self.title_label.add_css_class("finish-title")
        self.text_box.append(self.title_label)
        
        self.subtitle_label = Gtk.Label()
        localization_manager = get_localization_manager()
        self.subtitle_label.set_markup(f'<span size="large" alpha="80%">{localization_manager.get_text("Welcome to Linexin v2.0")}</span>')
        self.subtitle_label.add_css_class("finish-subtitle")
        self.subtitle_label.set_wrap(True)
        self.subtitle_label.set_justify(Gtk.Justification.CENTER)
        self.subtitle_label.set_max_width_chars(40)
        self.text_box.append(self.subtitle_label)
        
        self.card_box.append(self.text_box)

        # 3. Status/Details Box (The "Receipt" look)
        self.details_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.details_frame.add_css_class("details-box")
        self.details_frame.set_margin_top(10)
        self.details_frame.set_margin_bottom(10)
        
        # Row 1: System Status
        row1 = self.create_detail_row("system-run-symbolic", _("System Status"), _("Updated Successfully"))
        self.details_frame.append(row1)
        
        # Row 2: version
        row2 = self.create_detail_row("info-symbolic", _("Version"), "2.0 (Stable)")
        self.details_frame.append(row2)
        
        self.card_box.append(self.details_frame)

        # 4. Action Area
        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        self.action_box.set_halign(Gtk.Align.CENTER)
        self.action_box.set_margin_top(30) # Standardized top margin for buttons
        
        # Back Button (Hidden by default, kept for logic compat)
        self.btn_back = Gtk.Button(label=_("Back"))
        self.btn_back.add_css_class("glass-button")
        self.btn_back.set_size_request(120, 50)
        self.btn_back.set_visible(False)
        self.action_box.append(self.btn_back)

        # Main Finish Button
        self.btn_finish = Gtk.Button(label=_("Exit Installer"))
        self.btn_finish.add_css_class("suggested-action")
        self.btn_finish.add_css_class("pill-button")
        self.btn_finish.set_size_request(200, 50)
        self.btn_finish.connect("clicked", self.on_finish_clicked)
        self.action_box.append(self.btn_finish)
        
        self.card_box.append(self.action_box)

        # --- Animation Setup ---
        self.card_box.set_opacity(0)
        self.card_box.set_margin_top(100) # Start lower for slide-up effect
        self.connect("map", self.on_widget_mapped)

    def create_detail_row(self, icon_name, label_text, value_text):
        """Helper to create a detail row"""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        row.set_halign(Gtk.Align.FILL)
        
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.add_css_class("dim-icon")
        row.append(icon)
        
        label = Gtk.Label(label=label_text)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        label.add_css_class("detail-label")
        row.append(label)
        
        value = Gtk.Label(label=value_text)
        value.set_halign(Gtk.Align.END)
        value.add_css_class("detail-value")
        row.append(value)
        
        return row

    def setup_custom_css(self):
        css_provider = Gtk.CssProvider()
        css = """
        .finish-glass-card {
            background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            backdrop-filter: blur(20px);
        }

        .hero-icon {
            -gtk-icon-effect: highlight;
            color: #a3b8ff;
            filter: drop-shadow(0 0 10px rgba(163, 184, 255, 0.3));
            transition: all 0.5s ease;
        }

        .finish-title {
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            font-family: 'Sans';
            padding-bottom: 5px;
        }
        
        .finish-subtitle {
            color: alpha(@theme_fg_color, 0.8);
            font-weight: 300;
        }

        .details-box {
            background: rgba(0,0,0,0.2);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .detail-label {
            font-weight: 500;
            color: alpha(@theme_fg_color, 0.7);
        }
        
        .detail-value {
            font-weight: bold;
            color: @accent_color;
        }
        
        .dim-icon {
            opacity: 0.5;
        }

        .pill-button {
            border-radius: 99px;
            font-weight: 800;
            font-size: 1.1em;
            padding: 0 20px;
            background: linear-gradient(90deg, @accent_color, shade(@accent_color, 1.2));
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
            box-shadow: 0 5px 15px alpha(@accent_color, 0.4);
            transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        .pill-button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 25px alpha(@accent_color, 0.5);
        }
        
        .pill-button:active {
            transform: translateY(1px) scale(0.98);
        }
        
        .glass-button {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            color: white;
            border-radius: 99px;
            font-weight: 600;
        }
        
        .glass-button:hover {
            background: rgba(255,255,255,0.1);
        }

        .pulse {
            animation: pulse-anim 2s infinite;
        }

        @keyframes pulse-anim {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_widget_mapped(self, widget):
        if not self.initial_animation_done:
            self.initial_animation_done = True
            
            # Slide up and fade in
            target = Adw.CallbackAnimationTarget.new(self.animate_step, None)
            animation = Adw.TimedAnimation.new(self, 0, 1, 800, target)
            animation.set_easing(Adw.Easing.EASE_OUT_CUBIC)
            animation.play()
            
            # Pulse the hero icon
            self.hero_icon.add_css_class("pulse")

    def animate_step(self, value, user_data):
        self.card_box.set_opacity(value)
        # Animate margin from 100 down to 40 (standard)
        current_margin = 100 - (60 * value)
        self.card_box.set_margin_top(int(current_margin))

    def on_finish_clicked(self, button):
        self.btn_finish.set_sensitive(False)
        self.btn_back.set_sensitive(False)
        
        if self.requires_restart:
            self.show_reboot_dialog()
        else:
            self.start_fade_out()

    def set_requires_restart(self, requires_restart):
        self.requires_restart = requires_restart
        if requires_restart:
            self.btn_finish.set_label(_("Restart Now"))

    def set_sudo_password(self, password):
        self.sudo_password = password

    def show_reboot_dialog(self):
        root = self.get_root()
        dialog = Adw.MessageDialog(
            transient_for=root,
            heading=_("Reboot Required"),
            body=_("To complete the installation, your computer needs to restart.")
        )
        dialog.add_response("restart", _("Restart Now"))
        dialog.set_default_response("restart")
        dialog.connect("response", self.on_reboot_response)
        dialog.present()

    def on_reboot_response(self, dialog, response):
        dialog.close()
        # Set force_close on the main window to allow it to close during reboot
        root = self.get_root()
        if hasattr(root, 'force_close'):
            root.force_close = True
            
        # Trigger reboot
        if hasattr(self, 'sudo_password') and self.sudo_password:
             try:
                 # Use sudo with password
                 cmd = f"echo '{self.sudo_password}' | sudo -S reboot"
                 subprocess.run(cmd, shell=True)
             except Exception as e:
                 print(f"Sudo reboot failed, trying systemctl: {e}")
                 subprocess.run(["systemctl", "reboot"])
        else:
             # Fallback
             subprocess.run(["systemctl", "reboot"])
             
        # Also quit the app to be sure
        app = root.get_application()
        if app: app.quit()

    def start_fade_out(self):
        app_window = self.get_root()
        if app_window:
            target = Adw.CallbackAnimationTarget.new(lambda v,d: app_window.set_opacity(1.0-v), None)
            animation = Adw.TimedAnimation.new(app_window, 0, 1, 300, target)
            animation.set_easing(Adw.Easing.EASE_IN_QUAD)
            animation.connect("done", lambda a: self.quit_app(app_window))
            animation.play()

    def quit_app(self, window):
        # Set force_close to allow clean exit
        if hasattr(window, 'force_close'):
            window.force_close = True
            
        app = window.get_application()
        if app: app.quit()
        else: window.close()

# Test wrapper
if __name__ == "__main__":
    class FinishApp(Adw.Application):
        def __init__(self):
            super().__init__(application_id="com.linexin.test")
            self.connect('activate', self.on_activate)
        def on_activate(self, app):
            win = Adw.ApplicationWindow(application=app)
            win.set_default_size(800, 600)
            win.set_content(FinishWidget())
            win.present()
            
    app = FinishApp()
    app.run(None)