#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
import os
import gettext
import locale

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


class LinexinCenterStyleWidget(Gtk.Box):

    def __init__(self, on_continue_callback=None, **kwargs):
        """
        Initialize the widget.
        
        Args:
            on_continue_callback: Optional callback function to call when Continue button is clicked
            **kwargs: Additional arguments passed to Gtk.Box
        """
        super().__init__(**kwargs)
        
        print("DEBUG: Starting two box selection widget")
        
        # Store callback
        self.on_continue_callback = on_continue_callback
        self.selected_option = 0  # Default to first box
        self.animation_played = False  
        
        # Basic widget setup
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(30)
        self.set_margin_top(40)
        self.set_margin_bottom(40)
        self.set_margin_start(60)
        self.set_margin_end(60)
        
        # Setup CSS first
        self.setup_css()
        
        # Title
        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">Choose Your Option</span>')
        title.set_halign(Gtk.Align.CENTER)
        title.set_margin_bottom(20)
        self.append(title)
        
        # Get script directory for icons
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define the two options
        self.options = [
            {
                "name": "New Linexin Center (Recommended)",
                "description": "Unify your Linexin apps inside one simple app.",
                "icon": "screen1.png",
                #"details": "Includes gaming launchers, performance tools, and game compatibility layers"
            },
            {
                "name": "Separate Apps Icons",
                "description": "Keep my apps as separate icons.",
                "icon": "screen2.png", 
                #"details": "Office suite, development tools, media editing, and system utilities"
            }
        ]
        
        # Create options container
        options_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        options_container.set_halign(Gtk.Align.CENTER)
        options_container.set_homogeneous(True)
        
        self.option_boxes = []
        
        # Create the two option boxes
        for i, option in enumerate(self.options):
            option_box = self.create_option_box(option, i, script_dir)
            options_container.append(option_box)
            self.option_boxes.append(option_box)
        
        self.append(options_container)
        
        # Set first box as selected by default
        self.update_selection(0)
        
        navigation_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        navigation_btns.set_halign(Gtk.Align.CENTER)
        navigation_btns.set_margin_top(142)

        # Continue button
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
        
        # Add hover effects to continue button
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
        
        print("DEBUG: Two box selection widget initialization complete")
    
    def create_option_box(self, option, index, script_dir):
        """Create a single selectable option box with larger image"""
        
        # Main container - make it clickable
        main_box = Gtk.Button()
        main_box.add_css_class("option_box")
        main_box.set_size_request(300, 400)
        main_box.connect("clicked", lambda btn, idx=index: self.on_option_selected(idx))
        
        # Content container
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(30)
        content_box.set_margin_bottom(30)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        
        # Icon container with larger size
        icon_container = Gtk.Box()
        icon_container.set_size_request(120, 120)
        icon_container.set_halign(Gtk.Align.CENTER)
        icon_container.set_valign(Gtk.Align.CENTER)
        
        # Try to load icon
        icon_loaded = False
        icon_paths = [
            os.path.join(script_dir, option["icon"]),
            os.path.join(script_dir, "images", option["icon"])
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                try:
                    icon = Gtk.Image.new_from_file(path)
                    icon.set_size_request(300, 300)
                    icon.add_css_class("option_icon_image")
                    icon_container.append(icon)
                    icon_loaded = True
                    print(f"DEBUG: Loaded large icon for {option['name']}: {path}")
                    break
                except Exception as e:
                    print(f"DEBUG: Failed to load {path}: {e}")
        
        if not icon_loaded:
            # Fallback icon - larger
            fallback = Gtk.Box()
            fallback.set_size_request(120, 120)
            fallback.add_css_class("large_fallback_icon")
            
            # Add some text to the fallback
            fallback_label = Gtk.Label()
            fallback_label.set_text("📦" if index == 0 else "💼")
            fallback_label.add_css_class("fallback_emoji")
            fallback.set_halign(Gtk.Align.CENTER)
            fallback.set_valign(Gtk.Align.CENTER)
            
            overlay = Gtk.Overlay()
            overlay.set_child(fallback)
            overlay.add_overlay(fallback_label)
            
            icon_container.append(overlay)
            print(f"DEBUG: Using large fallback icon for {option['name']}")
        
        content_box.append(icon_container)
        
        # Option name
        name_label = Gtk.Label()
        name_label.set_markup(f'<span weight="bold" size="x-large">{option["name"]}</span>')
        name_label.set_halign(Gtk.Align.CENTER)
        name_label.set_wrap(True)
        name_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(name_label)
        
        # Option description
        desc_label = Gtk.Label()
        desc_label.set_text(option["description"])
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.set_wrap(True)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.add_css_class("option_description")
        content_box.append(desc_label)
        
        # Details
        #details_label = Gtk.Label()
        #details_label.set_markup(f'<span size="small" style="italic">{option["details"]}</span>')
        #details_label.set_halign(Gtk.Align.CENTER)
        #details_label.set_wrap(True)
        #details_label.set_justify(Gtk.Justification.CENTER)
        #details_label.add_css_class("option_details")
        #content_box.append(details_label)
        
        main_box.set_child(content_box)
        
        # Store index for reference
        main_box.option_index = index
        
        return main_box
    
    def on_option_selected(self, index):
        """Handle option selection"""
        print(f"DEBUG: Option {index} selected: {self.options[index]['name']}")
        self.selected_option = index
        self.update_selection(index)
    
    def update_selection(self, selected_index):
        """Update visual selection state"""
        for i, box in enumerate(self.option_boxes):
            if i == selected_index:
                box.add_css_class("selected")
                box.remove_css_class("unselected")
                print(f"DEBUG: Marked box {i} as selected")
            else:
                box.add_css_class("unselected")
                box.remove_css_class("selected")
                print(f"DEBUG: Marked box {i} as unselected")
    
    def on_continue_clicked(self, button):
        """Handle continue button click"""
        selected_option = self.options[self.selected_option]
        print(f"DEBUG: Continue clicked with selection: {selected_option['name']}")
        
        if self.on_continue_callback:
            # Pass the selected option to the callback
            self.on_continue_callback(self.selected_option, selected_option)
        else:
            print("DEBUG: No continue callback provided")
    
    def get_selected_option(self):
        """Get the currently selected option"""
        return self.selected_option, self.options[self.selected_option]
    
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
        .option_box {
            background: @theme_base_color;
            border: 2px solid rgba(0,0,0,0.1);
            border-radius: 15px;
            margin: 10px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .option_box:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            background: alpha(@theme_base_color, 0.95);
        }
        
        .option_box.selected {
            border-color: @accent_color;
            background: alpha(@accent_color, 0.1);
            transform: scale(1.02);
            box-shadow: 0 8px 30px alpha(@accent_color, 0.3);
        }
        
        .option_box.selected:hover {
            transform: scale(1.02) translateY(-2px);
        }
        
        .option_box.unselected {
            opacity: 0.8;
        }
        
        .option_box.unselected:hover {
            opacity: 1.0;
        }
        
        .large_fallback_icon {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            transition: all 0.3s ease;
        }
        
        .option_icon_image {
            border-radius: 15px;
            transition: all 0.3s ease;
        }
        
        .option_icon_image:hover, .large_fallback_icon:hover {
            transform: scale(1.05);
        }
        
        .fallback_emoji {
            font-size: 48px;
            color: white;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .option_description {
            color: alpha(@theme_fg_color, 0.8);
            font-size: 1.1em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        
        .option_details {
            color: alpha(@theme_fg_color, 0.6);
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
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
            font-size: 1.1em;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .continue_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px alpha(@accent_color, 0.3);
        }
        
        .continue_button:active {
            transform: translateY(0px);
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
            super().__init__(application_id="com.example.twoboxtest")
            self.connect('activate', self.on_activate)

        def on_activate(self, app):
            # Create window
            self.win = Adw.ApplicationWindow(application=app)
            self.win.set_title("Test - Two Box Selection Widget")
            self.win.set_default_size(800, 600)
            
            # Create scrolled window
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            
            # Create widget with callback
            def on_continue(selected_index, selected_option):
                print(f"Continue callback executed!")
                print(f"Selected: {selected_option['name']} (index {selected_index})")
                # Add your navigation logic here
            
            widget = LinexinCenterStyleWidget(on_continue_callback=on_continue)
            scrolled.set_child(widget)
            
            self.win.set_content(scrolled)
            self.win.present()

    print("DEBUG: Starting two box selection test application")
    app = TestApp()
    app.run(None)