#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
import os
import gettext
import locale
import subprocess
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk, GLib

# --- i18n Setup ---
WIDGET_NAME = "linexin-installer-defaults-widget"
LOCALE_DIR = "/usr/share/locale"
locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain(WIDGET_NAME, LOCALE_DIR)
gettext.bindtextdomain(WIDGET_NAME, LOCALE_DIR)
gettext.textdomain(WIDGET_NAME)
_ = gettext.gettext


class InstallDefaultsWidget(Gtk.Box):
    """
    A standalone widget for installing default applications.
    Can be embedded in any GTK4/Adwaita application.
    
    Usage:
        widget = InstallDefaultsWidget()
        parent_container.append(widget)
    """
    
    def __init__(self, on_continue_callback=None, **kwargs):
        """
        Initialize the widget.
        
        Args:
            on_continue_callback: Optional callback function to call when Continue button is clicked
            **kwargs: Additional arguments passed to Gtk.Box
        """
        super().__init__(**kwargs)
        
        print("DEBUG: Starting new widget with individual commands")
        
        # Store callback
        self.on_continue_callback = on_continue_callback
        self.animation_played = False  
        
        # Basic widget setup
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(20)
        self.set_margin_top(30)
        self.set_margin_bottom(30)
        self.set_margin_start(50)
        self.set_margin_end(50)
        
        # Setup CSS first
        self.setup_css()
        
        # Title
        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">Install new apps</span>')
        title.set_halign(Gtk.Align.CENTER)
        self.append(title)
        
        # Get script directory for icons
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define applications with their specific installation commands
        self.applications = [
            {
                "name": "Zen Browser",
                "description": "Browse your internet with beautifully designed, privacy-focused app.", 
                "icon": "icon1.png",
                "command": "flatpak install app.zen_browser.zen --assumeyes"
            },
            {
                "name": "Gear Lever",
                "description": "Manage AppImages and replace old AppImageLauncher with a modern tool",
                "icon": "icon2.png", 
                "command": "flatpak install it.mijorus.gearlever --assumeyes && run0 pacman -Rsc appimagelauncher --noconfirm 2>/dev/null || true"
            },
            {
                "name": "Flatseal",
                "description": "Manage Flatpak permissions with ease. No more pesky terminal commands.",
                "icon": "icon3.png", 
                "command": "flatpak install com.github.tchx84.Flatseal --assumeyes"
            },
            {
                "name": "Bottles",
                "description": "Run Windows software. ",
                "icon": "icon4.png",
                "command": "flatpak install com.usebottles.bottles --assumeyes"
            },
            {
                "name": "Heroic Launcher", 
                "description": "Play Epic, GOG and Amazon Games",
                "icon": "icon5.png",
                "command": "flatpak install com.heroicgameslauncher.hgl --assumeyes"
            },
            {
                "name": "Faugus Launcher",
                "description": "Play your games with a simple and lightweight app.", 
                "icon": "icon6.png",
                "command": "flatpak install io.github.Faugus.faugus-launcher --assumeyes"
            },
            {
                "name": "Twintail Launcher",
                "description": "Run morally questionable anime games on Linexin.", 
                "icon": "icon7.png",
                "command": "flatpak install app.twintaillauncher.ttl --assumeyes"
            }
        ]
        
        self.install_buttons = []
        
        # Create app boxes
        for i, app in enumerate(self.applications):
            print(f"DEBUG: Creating {app['name']} with command: {app['command']}")
            
            app_box = self.create_application_box(app, i, script_dir)
            self.append(app_box)
        
        # Continue button

        navigation_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        navigation_btns.set_halign(Gtk.Align.CENTER)


        self.continue_btn = Gtk.Button()
        self.continue_btn.set_label("Continue")
        self.continue_btn.add_css_class("suggested-action")
        self.continue_btn.add_css_class("continue_button")
        self.continue_btn.set_size_request(200, 50)
        self.continue_btn.set_halign(Gtk.Align.CENTER)
        self.continue_btn.set_margin_end(10)
        self.continue_btn.set_margin_top(20)
        self.continue_btn.connect("clicked", self.on_continue_clicked)
        

        self.back_btn = Gtk.Button()
        self.back_btn.set_label("Back")
        #self.back_btn.add_css_class("suggested-action")
        self.back_btn.add_css_class("back_button")
        self.back_btn.set_size_request(200, 50)
        self.back_btn.set_halign(Gtk.Align.CENTER)
        self.back_btn.set_margin_top(20)
        self.back_btn.set_margin_end(10)
        self.back_btn.connect("clicked", self.on_continue_clicked)
        
        # Add hover effects
        continue_hover = Gtk.EventControllerMotion()
        continue_hover.connect("enter", lambda c, x, y: self.continue_btn.add_css_class("pulse-animation"))
        continue_hover.connect("leave", lambda c: self.continue_btn.remove_css_class("pulse-animation"))
        self.continue_btn.add_controller(continue_hover)
        
        # Add hover effects to back button
        back_hover = Gtk.EventControllerMotion()
        back_hover.connect("enter", lambda c, x, y: self.back_btn.add_css_class("pulse-animation"))
        back_hover.connect("leave", lambda c: self.back_btn.remove_css_class("pulse-animation"))
        self.back_btn.add_controller(back_hover)

        navigation_btns.append(self.back_btn)
        navigation_btns.append(self.continue_btn)
        self.append(navigation_btns)

        # Animation setup
        self.set_opacity(0)
        self.connect("map", self.on_widget_mapped)
        
        print("DEBUG: Widget initialization complete")
    
    def create_application_box(self, app, index, script_dir):
        """Create a single application box"""
        
        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        box.add_css_class("app_box")
        box.set_size_request(-1, 70)
        
        # Icon container
        icon_container = Gtk.Box()
        icon_container.set_size_request(48, 48)
        icon_container.set_halign(Gtk.Align.CENTER)
        icon_container.set_valign(Gtk.Align.CENTER)
        
        # Try to load icon
        icon_loaded = False
        icon_paths = [
            os.path.join(script_dir, app["icon"]),
            os.path.join(script_dir, "images", app["icon"])
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                try:
                    icon = Gtk.Image.new_from_file(path)
                    icon.set_size_request(48, 48)
                    icon.add_css_class("app_icon_image")
                    icon_container.append(icon)
                    icon_loaded = True
                    print(f"DEBUG: Loaded icon for {app['name']}: {path}")
                    break
                except Exception as e:
                    print(f"DEBUG: Failed to load {path}: {e}")
        
        if not icon_loaded:
            # Fallback icon
            fallback = Gtk.Box()
            fallback.set_size_request(48, 48)
            fallback.add_css_class("fallback_icon")
            icon_container.append(fallback)
            print(f"DEBUG: Using fallback icon for {app['name']}")
        
        box.append(icon_container)
        
        # Text container
        text_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        text_container.set_hexpand(True)
        text_container.set_valign(Gtk.Align.CENTER)
        
        # App name
        name_label = Gtk.Label()
        name_label.set_markup(f'<span weight="bold" size="large">{app["name"]}</span>')
        name_label.set_halign(Gtk.Align.START)
        text_container.append(name_label)
        
        # App description
        desc_label = Gtk.Label()
        desc_label.set_text(app["description"])
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("subtitle_text")
        text_container.append(desc_label)
        
        box.append(text_container)
        
        # Install button
        install_btn = Gtk.Button()
        install_btn.set_label("Install")
        install_btn.add_css_class("suggested-action")
        install_btn.add_css_class("install_button")
        install_btn.set_size_request(100, 40)
        install_btn.set_valign(Gtk.Align.CENTER)
        
        # Store the command directly with the button for debugging
        install_btn.install_command = app["command"]
        install_btn.app_name = app["name"]
        
        print(f"DEBUG: Button for {app['name']} will run: {app['command']}")
        
        # Connect the click event
        install_btn.connect("clicked", self.on_install_button_clicked)
        
        # Add hover effects
        hover = Gtk.EventControllerMotion()
        hover.connect("enter", lambda c, x, y, btn=install_btn: btn.add_css_class("pulse-animation"))
        hover.connect("leave", lambda c, btn=install_btn: btn.remove_css_class("pulse-animation"))
        install_btn.add_controller(hover)
        
        box.append(install_btn)
        self.install_buttons.append(install_btn)
        
        return box
    
    def on_install_button_clicked(self, button):
        """Handle install button clicks"""
        print(f"DEBUG: Installing {button.app_name}")
        print(f"DEBUG: Running command: {button.install_command}")
        
        button.set_label("Installing...")
        button.set_sensitive(False)
        
        def run_installation():
            try:
                # Run the specific command for this app
                result = subprocess.run(
                    button.install_command, 
                    shell=True, 
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"DEBUG: Installation of {button.app_name} completed successfully")
                print(f"DEBUG: Output: {result.stdout}")
                GLib.idle_add(self.installation_complete, button, True)
                
            except subprocess.CalledProcessError as e:
                print(f"DEBUG: Installation of {button.app_name} failed")
                print(f"DEBUG: Error: {e.stderr}")
                GLib.idle_add(self.installation_complete, button, False)
                
            except Exception as e:
                print(f"DEBUG: Unexpected error installing {button.app_name}: {e}")
                GLib.idle_add(self.installation_complete, button, False)
        
        # Run installation in background thread
        thread = threading.Thread(target=run_installation, daemon=True)
        thread.start()
    
    def installation_complete(self, button, success):
        """Called when installation completes"""
        if success:
            button.set_label("Installed")
            button.add_css_class("success_button")
            print(f"DEBUG: {button.app_name} installation marked as successful")
        else:
            button.set_label("Failed")
            button.add_css_class("error_button")
            button.set_sensitive(True)
            print(f"DEBUG: {button.app_name} installation marked as failed")
    
    def on_continue_clicked(self, button):
        """Handle continue button click"""
        print("DEBUG: Continue button clicked")
        if self.on_continue_callback:
            self.on_continue_callback()
        else:
            print("DEBUG: No continue callback provided")
    
    def on_widget_mapped(self, widget):
        """Start entrance animation"""
        if not self.animation_played:
            GLib.timeout_add(200, self.start_animation)
            self.animation_played = True
    
    def start_animation(self):
        """Fade in animation"""
        def animate(value, data):
            self.set_opacity(value)
        
        target = Adw.CallbackAnimationTarget.new(animate, None)
        animation = Adw.TimedAnimation.new(self, 0.0, 1.0, 1200, target)
        animation.set_easing(Adw.Easing.EASE_OUT_QUAD)
        animation.play()
        return False
    
    def setup_css(self):
        """Setup CSS styling"""
        css_provider = Gtk.CssProvider()
        css_data = """
        .app_box {
            background: @theme_base_color;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 0px 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .app_box:hover {
            transform: translateY(-2px);
            background: alpha(@theme_base_color, 0.95);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }
        
        .fallback_icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .app_icon_image {
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .app_icon_image:hover, .fallback_icon:hover {
            transform: scale(1.05);
        }
        
        .subtitle_text {
            color: alpha(@theme_fg_color, 0.7);
            font-size: 0.9em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        
        .install_button {
            border-radius: 20px;
            font-weight: bold;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .install_button:hover {
            transform: translateY(-1px);
        }
        
        .install_button:active {
            transform: translateY(1px);
        }
        
        .back_button {
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.1em;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .back_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px alpha(@theme_bg_color, 0.3);
        }
        
        .back_button:active {
            transform: translateY(0px);
        }

        .continue_button {
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .continue_button:hover {
            transform: translateY(-2px);
        }
        
        .continue_button:active {
            transform: translateY(1px);
        }
        
        .success_button {
            background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
            color: white;
            border: none;
        }
        
        .error_button {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border: none;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .pulse-animation {
            animation: pulse 2s ease-in-out infinite;
        }
        
        label {
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        """
        
        css_provider.load_from_data(css_data.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


# Example usage - this part can be removed when using as a widget
if __name__ == "__main__":
    """
    Example of how to use the widget in an application.
    Remove this section when using the widget in your own application.
    """
    
    class TestApp(Adw.Application):
        def __init__(self):
            super().__init__(application_id="com.example.test")
            self.connect('activate', self.on_activate)

        def on_activate(self, app):
            # Create window
            self.win = Adw.ApplicationWindow(application=app)
            self.win.set_title("Test - Install Defaults Widget")
            self.win.set_default_size(800, 700)
            
            # Create scrolled window
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            
            # Create widget with callback
            def on_continue():
                print("Continue callback executed!")
                # Add your navigation logic here
            
            widget = InstallDefaultsWidget(on_continue_callback=on_continue)
            scrolled.set_child(widget)
            
            self.win.set_content(scrolled)
            self.win.present()

    print("DEBUG: Starting test application")
    app = TestApp()
    app.run(None)