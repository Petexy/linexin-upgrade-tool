#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
import os
import configparser
import shutil
import subprocess
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk, GLib

from simple_localization_manager import get_localization_manager, _


class ThemePicker(Gtk.Box):

    def __init__(self, on_continue_callback=None, **kwargs):
        super().__init__(**kwargs)

        print("DEBUG: Starting ThemePicker widget")

        # Store callback
        self.on_continue_callback = on_continue_callback
        self.selected_option = 0  # Default to first box (use new theme)
        self.animation_played = False

        # Auto-register for translation updates
        get_localization_manager().register_widget(self)

        # Basic widget setup
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(20)
        self.set_valign(Gtk.Align.CENTER)
        self.set_vexpand(True)
        self.set_margin_start(40)
        self.set_margin_end(40)

        # Setup CSS first
        self.setup_css()

        # Title
        title = Gtk.Label()
        title.set_markup(f'<span size="x-large" weight="bold">{_("Choose Your Option")}</span>')
        title.set_halign(Gtk.Align.CENTER)
        title.set_margin_bottom(10)
        self.append(title)

        # Get script directory for icons
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Choose screenshots based on current desktop environment
        current_de = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        is_plasma = "KDE" in current_de
        if is_plasma:
            icon1, icon2 = "screen1_update3.png", "screen2_update3.png"
        else:
            icon1, icon2 = "screen3_update3.png", "screen4_update3.png"

        # Define the two options
        self.options = [
            {
                "name": _("Use new Linexin theme"),
                "description": _("Apply the latest Linexin look and feel to your desktop."),
                "icon": icon1,
            },
            {
                "name": _("Keep current theme"),
                "description": _("Do not change your current theme settings."),
                "icon": icon2,
            }
        ]

        # Create options container
        options_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        options_container.set_halign(Gtk.Align.CENTER)
        options_container.set_homogeneous(True)

        self.option_boxes = []

        for i, option in enumerate(self.options):
            option_box = self.create_option_box(option, i, script_dir)
            options_container.append(option_box)
            self.option_boxes.append(option_box)

        self.append(options_container)

        # Set first box as selected by default
        self.update_selection(0)

        navigation_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        navigation_btns.set_halign(Gtk.Align.CENTER)
        navigation_btns.set_margin_top(30)

        # Continue button
        self.continue_btn = Gtk.Button()
        self.continue_btn.set_label(_("Continue"))
        self.continue_btn.add_css_class("suggested-action")
        self.continue_btn.add_css_class("continue_button")
        self.continue_btn.set_size_request(160, 40)
        self.continue_btn.set_halign(Gtk.Align.CENTER)
        self.continue_btn.set_margin_end(10)
        self.continue_btn.connect("clicked", self.on_continue_clicked)

        self.back_btn = Gtk.Button()
        self.back_btn.set_label(_("Back"))
        self.back_btn.add_css_class("back_button")
        self.back_btn.set_size_request(160, 40)
        self.back_btn.set_halign(Gtk.Align.CENTER)
        self.back_btn.set_margin_end(10)

        # Hover effects
        continue_hover = Gtk.EventControllerMotion()
        continue_hover.connect("enter", lambda c, x, y: self.continue_btn.add_css_class("pulse-animation"))
        continue_hover.connect("leave", lambda c: self.continue_btn.remove_css_class("pulse-animation"))
        self.continue_btn.add_controller(continue_hover)

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

        print("DEBUG: ThemePicker widget initialization complete")

    # ---- Helpers ----

    @staticmethod
    def _has_kinexin_desktop():
        """Check if kinexin-desktop package is installed."""
        try:
            result = subprocess.run(
                ["pacman", "-Q", "kinexin-desktop"],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    # ---- Option box creation ----

    def create_option_box(self, option, index, script_dir):
        main_box = Gtk.Button()
        main_box.add_css_class("option_box")
        main_box.set_size_request(240, 320)
        main_box.connect("clicked", lambda btn, idx=index: self.on_option_selected(idx))

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(15)
        content_box.set_margin_end(15)

        icon_container = Gtk.Box()
        icon_container.set_size_request(210, 210)
        icon_container.set_halign(Gtk.Align.CENTER)
        icon_container.set_valign(Gtk.Align.CENTER)

        icon_loaded = False
        icon_paths = [
            os.path.join(script_dir, option["icon"]),
            os.path.join(script_dir, "images", option["icon"])
        ]

        for path in icon_paths:
            if os.path.isfile(path) and os.access(path, os.R_OK):
                try:
                    texture = Gdk.Texture.new_from_filename(path)
                    icon = Gtk.Picture.new_for_paintable(texture)
                    icon.set_content_fit(Gtk.ContentFit.CONTAIN)
                    icon.set_size_request(210, 210)
                    icon.add_css_class("option_icon_image")
                    icon_container.append(icon)
                    icon_loaded = True
                    break
                except Exception as e:
                    print(f"DEBUG: Failed to load {path}: {e}")

        if not icon_loaded:
            fallback = Gtk.Box()
            fallback.set_size_request(210, 210)
            fallback.add_css_class("large_fallback_icon")
            fallback_label = Gtk.Label()
            fallback_label.set_text("🎨" if index == 0 else "🖥️")
            fallback_label.add_css_class("fallback_emoji")
            fallback.set_halign(Gtk.Align.CENTER)
            fallback.set_valign(Gtk.Align.CENTER)
            overlay = Gtk.Overlay()
            overlay.set_child(fallback)
            overlay.add_overlay(fallback_label)
            icon_container.append(overlay)

        content_box.append(icon_container)

        name_label = Gtk.Label()
        name_label.set_markup(f'<span weight="bold" size="large">{option["name"]}</span>')
        name_label.set_halign(Gtk.Align.CENTER)
        name_label.set_wrap(True)
        name_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(name_label)

        desc_label = Gtk.Label()
        desc_label.set_text(option["description"])
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.set_wrap(True)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.add_css_class("option_description")
        content_box.append(desc_label)

        main_box.set_child(content_box)
        main_box.option_index = index
        return main_box

    # ---- Selection handling ----

    def on_option_selected(self, index):
        print(f"DEBUG: Option {index} selected: {self.options[index]['name']}")
        self.selected_option = index
        self.update_selection(index)

    def update_selection(self, selected_index):
        for i, box in enumerate(self.option_boxes):
            if i == selected_index:
                box.add_css_class("selected")
                box.remove_css_class("unselected")
            else:
                box.add_css_class("unselected")
                box.remove_css_class("selected")

    # ---- Continue / password flow ----

    def on_continue_clicked(self, button):
        self._prompt_for_password()

    def _prompt_for_password(self):
        root = self.get_root()
        pass_dialog = Adw.MessageDialog(
            transient_for=root,
            heading=_("Authentication Required"),
            body=_("Please enter your password to modify system packages.")
        )

        self.password_entry = Gtk.PasswordEntry()
        self.password_entry.set_hexpand(True)
        self.password_entry.connect("activate", lambda entry: pass_dialog.response("continue"))
        pass_dialog.set_extra_child(self.password_entry)

        pass_dialog.add_response("cancel", _("Cancel"))
        pass_dialog.add_response("continue", _("Continue"))
        pass_dialog.set_default_response("continue")

        pass_dialog.connect("response", self._on_password_entered)
        pass_dialog.present()

    def _on_password_entered(self, dialog, response):
        password = self.password_entry.get_text()
        dialog.close()

        if response == "continue":
            if password:
                if self._validate_password(password):
                    self._perform_update(password)
                else:
                    self._show_error(_("Incorrect password. Please try again."))
            else:
                self._show_error(_("Password cannot be empty."))

    def _validate_password(self, password):
        try:
            cmd = f"echo '{password}' | sudo -S -v -k"
            subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    def _show_error(self, message):
        root = self.get_root()
        dialog = Adw.MessageDialog(
            transient_for=root,
            heading=_("Error"),
            body=message
        )
        dialog.add_response("ok", _("OK"))
        dialog.present()

    # ---- Progress dialog ----

    def _create_progress_dialog(self):
        root = self.get_root()
        self.progress_dialog = Adw.MessageDialog(
            transient_for=root,
            heading=_("Updating System Components"),
            body=_("Please wait while the system is being updated...")
        )

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_halign(Gtk.Align.CENTER)

        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(32, 32)
        self.spinner.start()
        content_box.append(self.spinner)

        self.status_label = Gtk.Label(label=_("Initializing..."))
        content_box.append(self.status_label)

        self.progress_dialog.set_extra_child(content_box)
        self.progress_dialog.present()

    def _update_progress(self, message):
        if hasattr(self, 'status_label'):
            self.status_label.set_label(message)

    # ---- Core update logic ----

    def _perform_update(self, password):
        self._create_progress_dialog()

        has_kinexin = self._has_kinexin_desktop()
        apply_theme = self.selected_option == 0

        def run_ops():
            try:
                # 1. Install linexin-hello (always)
                packages = "linexin-hello"
                if has_kinexin:
                    packages += " kinexin-deco"

                GLib.idle_add(self._update_progress, _("Installing new packages..."))
                print(f"DEBUG: Installing packages: {packages}")
                install_cmd = f"echo '{password}' | sudo -S pacman -S --noconfirm --overwrite '*' {packages}"
                subprocess.run(install_cmd, shell=True, check=True)

                # 2. Apply theme if user chose option 0
                if apply_theme:
                    GLib.idle_add(self._update_progress, _("Applying new theme..."))
                    print("DEBUG: Applying new Linexin theme")
                    self._apply_theme(has_kinexin)

                    # Allow flatpak apps to read the GTK theme configs
                    for gtk_ver in ("gtk-4.0", "gtk-3.0"):
                        flatpak_cmd = f"echo '{password}' | sudo -S flatpak override --filesystem=xdg-config/{gtk_ver}:ro"
                        subprocess.run(flatpak_cmd, shell=True, check=True)
                        print(f"DEBUG: flatpak override set for {gtk_ver}")

                # 3. Clear sudo cache
                subprocess.run("sudo -k", shell=True)

                print("DEBUG: Update completed successfully")
                GLib.idle_add(self._on_update_success, password)

            except subprocess.CalledProcessError as e:
                print(f"ERROR: Update failed: {e}")
                subprocess.run("sudo -k", shell=True)
                GLib.idle_add(self._on_update_error, str(e))

        thread = threading.Thread(target=run_ops, daemon=True)
        thread.start()

    def _apply_theme(self, has_kinexin):
        """Copy GTK theme dirs from skel and optionally update kwinrc."""
        home = os.path.expanduser("~")
        config_dir = os.path.join(home, ".config")

        # Copy gtk-3.0 and gtk-4.0 from /etc/skel/.config
        for folder in ("gtk-3.0", "gtk-4.0"):
            src = os.path.join("/etc/skel/.config", folder)
            dst = os.path.join(config_dir, folder)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"DEBUG: Copied {src} -> {dst}")
            else:
                print(f"DEBUG: Skel source not found: {src}")

        # Update kwinrc for Kinexin users
        if has_kinexin:
            kwinrc_path = os.path.join(config_dir, "kwinrc")
            if os.path.isfile(kwinrc_path):
                self._update_kwinrc(kwinrc_path)
            else:
                print(f"DEBUG: kwinrc not found at {kwinrc_path}, skipping")

    @staticmethod
    def _update_kwinrc(kwinrc_path):
        """Change library= in [org.kde.kdecoration2] to kinexin-deco-kwin."""
        config = configparser.ConfigParser(interpolation=None)
        # Preserve case of option names
        config.optionxform = str
        config.read(kwinrc_path)

        section = "org.kde.kdecoration2"
        if config.has_section(section):
            config.set(section, "library", "kinexin-deco-kwin")
            with open(kwinrc_path, "w") as f:
                config.write(f, space_around_delimiters=False)
            print(f"DEBUG: Updated library= in [{section}] to kinexin-deco-kwin")
        else:
            print(f"DEBUG: Section [{section}] not found in kwinrc, skipping")

    # ---- Completion handlers ----

    def _on_update_success(self, password):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        selected_option = self.options[self.selected_option]
        print(f"DEBUG: Update finished with selection: {selected_option['name']}")

        if self.on_continue_callback:
            self.on_continue_callback(self.selected_option, selected_option, password)
        else:
            print("DEBUG: No continue callback provided")

    def _on_update_error(self, error_message):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        self._show_error(_("Failed to update packages: ") + error_message)

    # ---- Selection getter ----

    def get_selected_option(self):
        return self.selected_option, self.options[self.selected_option]

    # ---- Animation ----

    def on_widget_mapped(self, widget):
        if not self.animation_played:
            GLib.timeout_add(200, self.start_animation)
            self.animation_played = True

    def start_animation(self):
        def animate(value, data):
            self.set_opacity(value)
        target = Adw.CallbackAnimationTarget.new(animate, None)
        animation = Adw.TimedAnimation.new(self, 0.0, 1.0, 1200, target)
        animation.set_easing(Adw.Easing.EASE_OUT_QUAD)
        animation.play()
        return False

    # ---- CSS ----

    def setup_css(self):
        css_provider = Gtk.CssProvider()
        css_data = """
        .option_box {
            background: @theme_base_color;
            border: 2px solid rgba(0,0,0,0.1);
            border-radius: 12px;
            margin: 8px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }

        .option_box:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            background: alpha(@theme_base_color, 0.95);
        }

        .option_box.selected {
            border-color: @accent_color;
            background: alpha(@accent_color, 0.1);
            transform: scale(1.02);
            box-shadow: 0 6px 25px alpha(@accent_color, 0.3);
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
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .option_icon_image {
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .option_icon_image:hover, .large_fallback_icon:hover {
            transform: scale(1.05);
        }

        .fallback_emoji {
            font-size: 96px;
            color: white;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .option_description {
            color: alpha(@theme_fg_color, 0.8);
            font-size: 0.95em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .back_button {
            border-radius: 20px;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        .back_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px alpha(@theme_bg_color, 0.3);
        }

        .back_button:active {
            transform: translateY(0px);
        }

        .continue_button {
            border-radius: 20px;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        .continue_button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px alpha(@accent_color, 0.3);
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
