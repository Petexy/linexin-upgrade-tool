
import gi
import os
import gettext
import locale

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk, GLib

from simple_localization_manager import get_localization_manager, _


class WhatsNewWidget(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Auto-register for translation updates
        get_localization_manager().register_widget(self)

        self.animation_played = False 

        # --- Carousel Data (Easy to modify) ---
        self.slides = [
            {
                "title": _("Kinexin Desktop"),
                "description": _("A meme becomes reality. Kinexin finally exists. It offers a carefully crafted Plasma experience with marvellous glass effects."),
                "image_path": "1.png"
            },
            {
                "title": _("Linexin Package Manager"),
                "description": _("Linpama (Linexin Package Manager) is a new pacman and AUR wrapper written specifically for Linexin. Customize your system with ease!"),
                "image_path": "2.png"
            },
            {
                "title": _("Updated GNOME Extensions"),
                "description": _("GNOME Extensions are now updated to the latest version. They also have been separated from the system, hence they can update automatically."),
                "image_path": "3.png"
            },
            {
                "title": _("Easier installation"),
                "description": _("No need to take care of your partitions when installing Linexin. Just select the partition or free space and let the installer do the rest."),
                "image_path": "4.png"
            },
            {
                "title": _("Affinity 3 (2025) support"),
                "description": _("Affinity Installer is more powerful than ever. With it you can install Affinity 3 (2025) on your system easily as well as older Affinity products."),
                "image_path": "5.png"
            }
        ]
        
        self.current_slide_index = 0
        self.auto_advance_timer = None
        self.animation_in_progress = False

        self.set_orientation(Gtk.Orientation.VERTICAL)
        # Main widget fills the available space
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)

        # Add CSS for enhanced styling
        self.setup_custom_css()

        # --- Robust Layout with Adw.Clamp ---
        # Clamp ensures content never exceeds max size but scales down
        self.clamp = Adw.Clamp()
        self.clamp.set_maximum_size(800)
        self.clamp.set_tightening_threshold(600)
        self.append(self.clamp)

        # Main container inside clamp
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_container.set_margin_bottom(30) # Standardized
        self.main_container.set_margin_top(30)
        self.main_container.set_valign(Gtk.Align.CENTER)
        self.main_container.add_css_class("main_widget_container")
        self.clamp.set_child(self.main_container)

        # Title section
        self.main_title = Gtk.Label()
        self.main_title.set_markup(f'<span size="xx-large" weight="bold">{_("What has changed?")}</span>')
        self.main_title.add_css_class("main_title")
        self.main_title.set_halign(Gtk.Align.CENTER)
        self.main_container.append(self.main_title)

        # Carousel container (Arrow - Card - Arrow)
        carousel_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        carousel_row.set_halign(Gtk.Align.CENTER)
        
        # Left arrow button
        self.left_arrow = Gtk.Button()
        self.left_arrow.set_icon_name("go-previous-symbolic")
        self.left_arrow.add_css_class("carousel_arrow")
        self.left_arrow.set_valign(Gtk.Align.CENTER)
        self.left_arrow.connect("clicked", self.on_previous_slide)
        carousel_row.append(self.left_arrow)

        # Content Card (Image + Text)
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.content_box.add_css_class("content_box")
        # Let the box fill the clamped width minus arrows
        self.content_box.set_hexpand(True) 
        
        # Image
        self.slide_image = Gtk.Picture()
        self.slide_image.set_size_request(480, 270)
        self.slide_image.set_can_shrink(True)
        self.slide_image.set_content_fit(Gtk.ContentFit.CONTAIN) # Ensure aspect ratio
        self.slide_image.set_halign(Gtk.Align.CENTER)
        self.slide_image.add_css_class("slide_image")
        
        # Create placeholder image
        self.create_placeholder_image()
        self.content_box.append(self.slide_image)

        # Text container
        text_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        text_container.set_halign(Gtk.Align.CENTER)
        
        # Slide title
        self.slide_title = Gtk.Label()
        self.slide_title.add_css_class("slide_title")
        self.slide_title.set_halign(Gtk.Align.CENTER)
        self.slide_title.set_wrap(True)
        self.slide_title.set_max_width_chars(40)
        self.slide_title.set_justify(Gtk.Justification.CENTER)
        text_container.append(self.slide_title)

        # Slide description
        self.slide_description = Gtk.Label()
        self.slide_description.add_css_class("slide_description")
        self.slide_description.set_halign(Gtk.Align.CENTER)
        self.slide_description.set_wrap(True)
        self.slide_description.set_max_width_chars(50)
        self.slide_description.set_justify(Gtk.Justification.CENTER)
        text_container.append(self.slide_description)

        self.content_box.append(text_container)
        carousel_row.append(self.content_box)

        # Right arrow button
        self.right_arrow = Gtk.Button()
        self.right_arrow.set_icon_name("go-next-symbolic")
        self.right_arrow.add_css_class("carousel_arrow")
        self.right_arrow.set_valign(Gtk.Align.CENTER)
        self.right_arrow.connect("clicked", self.on_next_slide)
        carousel_row.append(self.right_arrow)

        self.main_container.append(carousel_row)

        # Continue button
        self.btn_continue = Gtk.Button(label=_("Continue"))
        self.btn_continue.add_css_class("suggested-action")
        self.btn_continue.add_css_class("continue_button")
        self.btn_continue.set_size_request(180, 45)
        self.btn_continue.set_halign(Gtk.Align.CENTER)
        self.btn_continue.set_margin_top(30) # Standardized
        
        # Add hover effects
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self.on_button_hover_enter)
        hover_controller.connect("leave", self.on_button_hover_leave)
        self.btn_continue.add_controller(hover_controller)
        
        self.main_container.append(self.btn_continue)

        # Load first slide
        self.update_slide_content()
        
        # Start auto-advance timer
        self.start_auto_advance()

        # Entrance animation
        self.main_container.set_opacity(0)
        self.connect("map", self.on_widget_mapped)

    def create_placeholder_image(self):
        """Load actual image or create placeholder if image not found"""
        slide = self.slides[self.current_slide_index]
        image_path = slide["image_path"]
        
        # Try to load the actual image file
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_image_path = os.path.join(script_dir, image_path)
            
            # Check if file exists
            if os.path.exists(full_image_path):
                # Load the actual image
                self.slide_image.set_filename(full_image_path)
                return
                
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
        
        # If image loading fails, create a Cairo placeholder
        import cairo
        
        # Reduced size to match widget constraints (was 960x540)
        width, height = 480, 270
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
        ctx = cairo.Context(surface)
        
        # Set background color (light blue gradient)
        gradient = cairo.LinearGradient(0, 0, width, height)
        gradient.add_color_stop_rgb(0, 0.8, 0.85, 0.95)
        gradient.add_color_stop_rgb(1, 0.6, 0.75, 0.9)
        ctx.set_source(gradient)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()
        
        # Add border
        ctx.set_source_rgb(0.4, 0.5, 0.7)
        ctx.set_line_width(3)
        ctx.rectangle(1.5, 1.5, width - 3, height - 3)
        ctx.stroke()
        
        # Add placeholder text
        ctx.set_source_rgb(0.2, 0.3, 0.5)
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24) # Reduced font
        text = f"Image not found"
        text_extents = ctx.text_extents(text)
        x = (width - text_extents.width) / 2
        y = (height + text_extents.height) / 2 - 15
        ctx.move_to(x, y)
        ctx.show_text(text)
        
        # Add subtitle
        ctx.set_font_size(14) # Reduced font
        subtitle = f"Looking for: {image_path}"
        text_extents = ctx.text_extents(subtitle)
        x = (width - text_extents.width) / 2
        y = y + 30
        ctx.move_to(x, y)
        ctx.show_text(subtitle)
        
        # Convert to GdkPixbuf and set to image
        pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, width, height)
        self.slide_image.set_pixbuf(pixbuf)

    def setup_custom_css(self):
        """Setup enhanced CSS for modern look and animations"""
        css_provider = Gtk.CssProvider()
        css_data = """
        .main_widget_container {
            transition: all 0.8s ease;
        }
        
        .main_title {
            color: @theme_fg_color;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        }
        
        .content_box {
            background: @theme_base_color;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            transition: all 0.4s ease;
        }
        
        .slide_image {
            border-radius: 12px;
            transition: all 0.4s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .slide_title {
            font-size: 20px;
            font-weight: bold;
            color: @theme_fg_color;
            margin-top: 10px;
        }
        
        .slide_description {
            color: @theme_unfocused_fg_color;
            font-size: 15px;
            line-height: 1.5;
        }
        
        .carousel_arrow {
            min-width: 50px;
            min-height: 50px;
            border-radius: 25px;
            background: @theme_bg_color;
            border: 2px solid @borders;
            transition: all 0.3s ease;
            font-size: 20px;
        }
        
        .carousel_arrow:hover {
            background: @theme_selected_bg_color;
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        .carousel_arrow:active {
            transform: scale(0.95);
        }
        
        .continue_button {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            box-shadow: 0 4px 12px rgba(201, 148, 218, 0.3);
        }
        
        .continue_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(201, 148, 218, 0.4);
        }
        
        .continue_button:active {
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
        
        /* Fade animations */
        .fade_out {
            opacity: 0;
            transform: translateX(-20px);
        }
        
        .fade_in {
            opacity: 1;
            transform: translateX(0);
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
        if not self.animation_played:
            GLib.timeout_add(200, self.start_entrance_animation)
            self.animation_played = True
        # Start auto-advance when widget becomes visible
        GLib.timeout_add(1000, lambda: self.start_auto_advance() or False)
        
    
    def on_widget_unmapped(self, widget):
        """Called when widget is unmapped (becomes hidden)"""
        # Stop auto-advance when widget is hidden
        self.stop_auto_advance()
    
    def start_entrance_animation(self):
        """Start the smooth entrance animation"""
        def animation_callback(value, data):
            self.main_container.set_opacity(value)
        
        target = Adw.CallbackAnimationTarget.new(animation_callback, None)
        animation = Adw.TimedAnimation.new(
            self.main_container,
            0.0, 1.0, 800, target
        )
        animation.set_easing(Adw.Easing.EASE_OUT_CUBIC)
        animation.play()
        
        return False

    def update_slide_content(self):
        """Update the displayed slide content"""
        if not self.slides:
            return
            
        slide = self.slides[self.current_slide_index]
        
        # Update text content
        self.slide_title.set_markup(f'<span size="large" weight="bold">{slide["title"]}</span>')
        self.slide_description.set_text(slide["description"])
        
        # Update image (recreate placeholder with current slide number)
        self.create_placeholder_image()

    def animate_slide_transition(self, direction="next"):
        """Animate transition between slides"""
        if self.animation_in_progress:
            return
            
        self.animation_in_progress = True
        
        # Fade out current content
        def fade_out_callback(value, data):
            self.content_box.set_opacity(1 - value)
        
        fade_out_target = Adw.CallbackAnimationTarget.new(fade_out_callback, None)
        fade_out_animation = Adw.TimedAnimation.new(
            self.content_box, 0.0, 1.0, 250, fade_out_target
        )
        fade_out_animation.set_easing(Adw.Easing.EASE_IN_CUBIC)
        
        def on_fade_out_complete(animation):
            # Update content
            self.update_slide_content()
            
            # Fade in new content
            def fade_in_callback(value, data):
                self.content_box.set_opacity(value)
            
            fade_in_target = Adw.CallbackAnimationTarget.new(fade_in_callback, None)
            fade_in_animation = Adw.TimedAnimation.new(
                self.content_box, 0.0, 1.0, 350, fade_in_target
            )
            fade_in_animation.set_easing(Adw.Easing.EASE_OUT_CUBIC)
            
            def on_fade_in_complete(anim):
                self.animation_in_progress = False
            
            fade_in_animation.connect("done", on_fade_in_complete)
            fade_in_animation.play()
        
        fade_out_animation.connect("done", on_fade_out_complete)
        fade_out_animation.play()

    def on_previous_slide(self, button):
        """Handle previous slide button click"""
        self.stop_auto_advance()
        self.current_slide_index = (self.current_slide_index - 1) % len(self.slides)
        self.animate_slide_transition("previous")
        self.start_auto_advance()

    def on_next_slide(self, button):
        """Handle next slide button click"""
        self.stop_auto_advance()
        self.current_slide_index = (self.current_slide_index + 1) % len(self.slides)
        self.animate_slide_transition("next")
        self.start_auto_advance()

    def on_button_hover_enter(self, controller, x, y):
        """Enhanced hover enter effect for continue button"""
        self.btn_continue.add_css_class("pulse-animation")

    def on_button_hover_leave(self, controller):
        """Enhanced hover leave effect for continue button"""
        self.btn_continue.remove_css_class("pulse-animation")

    def start_auto_advance(self):
        """Start the auto-advance timer"""
        if self.auto_advance_timer:
            GLib.source_remove(self.auto_advance_timer)
        self.auto_advance_timer = GLib.timeout_add_seconds(3, self.auto_advance)

    def stop_auto_advance(self):
        """Stop the auto-advance timer"""
        if self.auto_advance_timer:
            GLib.source_remove(self.auto_advance_timer)
            self.auto_advance_timer = None

    def auto_advance(self):
        """Auto-advance to next slide"""
        # Don't auto-advance if any animation is running from user interaction
        self.current_slide_index = (self.current_slide_index + 1) % len(self.slides)
        self.animate_slide_transition()
        return True

    def add_slide(self, title, description, image_path):
        """Add a new slide to the carousel"""
        new_slide = {
            "title": _(title),
            "description": _(description),
            "image_path": image_path
        }
        self.slides.append(new_slide)

    def remove_slide(self, index):
        """Remove a slide from the carousel"""
        if 0 <= index < len(self.slides) and len(self.slides) > 1:
            self.slides.pop(index)
            
            # Adjust current index if necessary
            if self.current_slide_index >= len(self.slides):
                self.current_slide_index = len(self.slides) - 1
            
            self.update_slide_content()


class WhatsNewApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.linexin.installer.whatsnew")
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("What's New - LineXin OS")
        self.win.set_default_size(900, 700)  # Same window size as requested
        
        self.whats_new_widget = WhatsNewWidget()
        self.win.set_content(self.whats_new_widget)
        self.win.present()


if __name__ == "__main__":
    app = WhatsNewApp()
    app.run(None)