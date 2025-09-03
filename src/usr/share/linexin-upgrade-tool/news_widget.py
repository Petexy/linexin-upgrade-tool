
import gi
import os
import gettext
import locale

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk, GLib

# --- i18n Setup ---
WIDGET_NAME = "linexin-installer-whats-new-widget"
LOCALE_DIR = "/usr/share/locale"
locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain(WIDGET_NAME, LOCALE_DIR)
gettext.bindtextdomain(WIDGET_NAME, LOCALE_DIR)
gettext.textdomain(WIDGET_NAME)
_ = gettext.gettext


class WhatsNewWidget(Gtk.Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.animation_played = False 

        # --- Carousel Data (Easy to modify) ---
        self.slides = [
            {
                "title": "Completely revamped installation process",
                "description": "Tired of seeing the same installer for every Linux distro? No worries! Linexin now uses proprietary installer!",
                "image_path": "1.png"
            },
            {
                "title": "Support for Legacy Boot and Dual Boot",
                "description": "Now you can install Linexin on older PCs as well as install it along other systems easily.",
                "image_path": "2.png"
            },
            {
                "title": "Better AppImage support",
                "description": "The AppImages are now handled using Gear Lever by default (older apps needs to be reinstalled from Applications folder)",
                "image_path": "3.png"
            },
            {
                "title": "Unified Linexin Center",
                "description": "All of the Linexin specific applications are now in one simple app called Linexin Center. No more clutter!",
                "image_path": "4.png"
            },
            {
                "title": "More tools",
                "description": "There are plenty of new applications that will make the Linexin experience better for new users.",
                "image_path": "5.png"
            }
        ]
        
        self.current_slide_index = 0
        self.auto_advance_timer = None
        self.animation_in_progress = False

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        # Add CSS for enhanced styling
        self.setup_custom_css()

        # Create main container
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_container.set_margin_top(40)
        self.main_container.set_margin_bottom(40)
        self.main_container.set_margin_start(40)
        self.main_container.set_margin_end(40)
        self.main_container.set_valign(Gtk.Align.CENTER)
        self.main_container.set_halign(Gtk.Align.CENTER)
        self.main_container.add_css_class("main_widget_container")

        # Title section - just the main title, larger
        title_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        title_container.set_halign(Gtk.Align.CENTER)

        self.main_title = Gtk.Label()
        self.main_title.set_markup(f'<span size="xx-large" weight="bold">{_("What has changed?")}</span>')
        self.main_title.add_css_class("main_title")
        self.main_title.set_halign(Gtk.Align.CENTER)
        title_container.append(self.main_title)

        self.main_container.append(title_container)

        # Carousel container with arrows and content
        carousel_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        carousel_container.set_halign(Gtk.Align.CENTER)
        carousel_container.set_valign(Gtk.Align.CENTER)

        # Left arrow button
        self.left_arrow = Gtk.Button()
        self.left_arrow.set_icon_name("go-previous-symbolic")
        self.left_arrow.add_css_class("carousel_arrow")
        self.left_arrow.set_valign(Gtk.Align.CENTER)
        self.left_arrow.connect("clicked", self.on_previous_slide)
        carousel_container.append(self.left_arrow)

        # Content box (image + text) - much larger now
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.content_box.set_size_request(980, 620)  # Large enough for 960x540 image plus text
        self.content_box.set_halign(Gtk.Align.CENTER)
        self.content_box.set_valign(Gtk.Align.CENTER)
        self.content_box.add_css_class("content_box")

        # Image container - much larger
        self.image_container = Gtk.Box(halign=Gtk.Align.CENTER)
        self.slide_image = Gtk.Picture()
        self.slide_image.set_size_request(960, 540)  # Full HD resolution
        self.slide_image.set_can_shrink(True)
        self.slide_image.set_halign(Gtk.Align.CENTER)
        self.slide_image.add_css_class("slide_image")
        
        # Create placeholder image
        self.create_placeholder_image()
        self.image_container.append(self.slide_image)
        self.content_box.append(self.image_container)

        # Text container
        text_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        text_container.set_halign(Gtk.Align.CENTER)
        text_container.set_margin_top(10)

        # Slide title
        self.slide_title = Gtk.Label()
        self.slide_title.add_css_class("slide_title")
        self.slide_title.set_halign(Gtk.Align.CENTER)
        self.slide_title.set_wrap(True)
        text_container.append(self.slide_title)

        # Slide description
        self.slide_description = Gtk.Label()
        self.slide_description.add_css_class("slide_description")
        self.slide_description.set_halign(Gtk.Align.CENTER)
        self.slide_description.set_wrap(True)
        self.slide_description.set_max_width_chars(60)
        text_container.append(self.slide_description)

        self.content_box.append(text_container)
        carousel_container.append(self.content_box)

        # Right arrow button
        self.right_arrow = Gtk.Button()
        self.right_arrow.set_icon_name("go-next-symbolic")
        self.right_arrow.add_css_class("carousel_arrow")
        self.right_arrow.set_valign(Gtk.Align.CENTER)
        self.right_arrow.connect("clicked", self.on_next_slide)
        carousel_container.append(self.right_arrow)

        self.main_container.append(carousel_container)

        # Continue button
        button_container = Gtk.Box(halign=Gtk.Align.CENTER, spacing=20)
        button_container.set_margin_top(20)
        
        self.btn_continue = Gtk.Button(label=_("Continue"))
        self.btn_continue.add_css_class("suggested-action")
        self.btn_continue.add_css_class("continue_button")
        self.btn_continue.set_size_request(180, 45)
        
        # Add hover effects
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self.on_button_hover_enter)
        hover_controller.connect("leave", self.on_button_hover_leave)
        self.btn_continue.add_controller(hover_controller)
        
        button_container.append(self.btn_continue)
        self.main_container.append(button_container)

        self.append(self.main_container)

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
        
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 960, 540)
        ctx = cairo.Context(surface)
        
        # Set background color (light blue gradient)
        gradient = cairo.LinearGradient(0, 0, 960, 540)
        gradient.add_color_stop_rgb(0, 0.8, 0.85, 0.95)
        gradient.add_color_stop_rgb(1, 0.6, 0.75, 0.9)
        ctx.set_source(gradient)
        ctx.rectangle(0, 0, 960, 540)
        ctx.fill()
        
        # Add border
        ctx.set_source_rgb(0.4, 0.5, 0.7)
        ctx.set_line_width(3)
        ctx.rectangle(1.5, 1.5, 957, 537)
        ctx.stroke()
        
        # Add placeholder text
        ctx.set_source_rgb(0.2, 0.3, 0.5)
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(48)
        text = f"Image not found"
        text_extents = ctx.text_extents(text)
        x = (960 - text_extents.width) / 2
        y = (540 + text_extents.height) / 2 - 30
        ctx.move_to(x, y)
        ctx.show_text(text)
        
        # Add subtitle
        ctx.set_font_size(24)
        subtitle = f"Looking for: {image_path}"
        text_extents = ctx.text_extents(subtitle)
        x = (960 - text_extents.width) / 2
        y = y + 60
        ctx.move_to(x, y)
        ctx.show_text(subtitle)
        
        # Convert to GdkPixbuf and set to image
        pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, 960, 540)
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
            "title": title,
            "description": description,
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