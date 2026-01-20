#!/usr/bin/env python3
import gettext
import locale
import os
import sys
import importlib
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GObject

class SimpleLocalizationManager(GObject.GObject):
    """
    A robust, singleton localization manager that monkey-patches Gtk and Adw widgets
    to provide automatic translation support.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimpleLocalizationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
            
        super().__init__()
        self._initialized = True
        
        # Paths
        self.base_dir = Path(__file__).parent.absolute()
        self.translations_dir = self.base_dir / "translations"
        
        # State
        self.translations = {}
        self.current_language = "en_US.UTF-8"
        self.org_texts = {} # Store original English texts: {widget: {prop: text}}
        
        # Load translations
        self.load_translations()
        
        # Detect system language
        self.current_language = self._detect_system_language()
        print(f"LocalizationManager initialized. Language: {self.current_language}")
        
        # Apply patches immediately
        self._apply_patches()

    def load_translations(self):
        """Load all available translation modules."""
        if not self.translations_dir.exists():
            print(f"Warning: Translations directory not found at {self.translations_dir}")
            return

        sys.path.insert(0, str(self.base_dir))
        
        # Scan for .py files in translations dir
        for file in self.translations_dir.glob("*.py"):
            if file.name.startswith("__") or file.name == "update_translations_tool_v2.py" or file.name == "fix_indentation.py":
                continue
                
            lang_code = file.stem # e.g. "pl_PL"
            # Normalize to our internal format with .UTF-8 if needed, but file names are usually just lang_country
            # We map filename -> full locale code if possible, or just use filename as key
            
            # Map common filenames to full locale codes for consistency with system detection
            locale_map_rev = {
                'en_US': 'en_US.UTF-8', 'pl_PL': 'pl_PL.UTF-8', 'de_DE': 'de_DE.UTF-8',
                'fr_FR': 'fr_FR.UTF-8', 'es_ES': 'es_ES.UTF-8', 'pt_BR': 'pt_BR.UTF-8',
                'ru_RU': 'ru_RU.UTF-8', 'zh_CN': 'zh_CN.UTF-8', 'hi_IN': 'hi_IN.UTF-8',
                'en_GB': 'en_GB.UTF-8', 'en_AU': 'en_AU.UTF-8', 'en_CA': 'en_CA.UTF-8'
            }
            
            full_code = locale_map_rev.get(lang_code, f"{lang_code}.UTF-8")
            
            try:
                module = importlib.import_module(f"translations.{lang_code}")
                if hasattr(module, 'translations'):
                    self.translations[full_code] = module.translations
                    # Also map simpler code for fallback lookup
                    self.translations[lang_code] = module.translations
                    print(f"Loaded translations for {lang_code}")
            except Exception as e:
                print(f"Failed to load translations for {lang_code}: {e}")

    def _detect_system_language(self):
        """Detect system language with robust fallback."""
        try:
            sys_loc = locale.getdefaultlocale()[0]
            if not sys_loc:
                sys_loc = os.environ.get('LANG', 'en_US').split('.')[0]
            
            # Normalize
            if sys_loc == 'C': sys_loc = 'en_US'
            
            # Try exact match with UTF-8
            utf8_loc = f"{sys_loc}.UTF-8"
            if utf8_loc in self.translations:
                return utf8_loc
            
            # Try exact match without UTF-8
            if sys_loc in self.translations:
                # Find the full key that stores it
                for k in self.translations:
                    if k.startswith(sys_loc):
                        return k
                        
            # Try base language (e.g. 'de' from 'de_AT')
            base = sys_loc.split('_')[0]
            for k in self.translations:
                if k.startswith(base + '_'):
                    return k
                    
        except Exception as e:
            print(f"Language detection error: {e}")
            
        return "en_US.UTF-8"

    def get_text(self, text):
        """
        Translate the given text. 
        Detailed logic:
        1. If text is empty or not string, return as is.
        2. Look up in current language.
        3. If not found, look up in en_US (to ensure we verify key existence).
        4. If not found anywhere, return original text.
        """
        if not text or not isinstance(text, str):
            return text
            
        current_dict = self.translations.get(self.current_language, {})
        
        if text in current_dict:
            return current_dict[text]
            
        # Fallback for "invisible" keys? 
        # Sometimes keys in code are English, but we might have a dedicated en_US dictionary 
        # that maps "Key" -> "Value". If we are in English, we want "Value".
        if self.current_language.startswith("en_"):
             en_dict = self.translations.get("en_US.UTF-8", {})
             if text in en_dict:
                 return en_dict[text]

        return text

    def _store_original(self, obj, prop, text):
        """Store the original English text for a property to allow re-translation."""
        if not text: return
        
        # We only store if we haven't stored it yet (first set is usually the init/English one)
        # OR if we explicitly detect it's a valid English key (which means it's a raw string from code)
        
        # Simplest robust approach:
        # If we don't have an original for this prop, store `text`.
        # When translating, we use the stored original to look up the new target.
        
        oid = id(obj)
        if oid not in self.org_texts:
            self.org_texts[oid] = {}
        
        if prop not in self.org_texts[oid]:
             self.org_texts[oid][prop] = text

    def _get_original(self, obj, prop):
        return self.org_texts.get(id(obj), {}).get(prop)

    # --- MONKEY PATCHING ---
    
    def _apply_patches(self):
        """Apply all monkey patches."""
        self._patch_gtk_label()
        self._patch_gtk_button()
        self._patch_gtk_window() # Covers Adw.Window too
        self._patch_adw_preferences_group()
        self._patch_adw_action_row() # Covers ExpanderRow
        self._patch_adw_status_page()
        self._patch_adw_window_title()
        self._patch_adw_message_dialog()
        self._patch_adw_toast()
        self._patch_adw_about_window()
        print("Localization patches applied.")

    def _patch_gtk_label(self):
        original_init = Gtk.Label.__init__
        original_set_text = Gtk.Label.set_text
        original_set_markup = Gtk.Label.set_markup
        
        def patched_init(self_obj, **kwargs):
            if 'label' in kwargs:
                # Capture original
                self._store_original(self_obj, 'label', kwargs['label'])
                kwargs['label'] = self.get_text(kwargs['label'])
            original_init(self_obj, **kwargs)

        def patched_set_text(self_obj, text):
            self._store_original(self_obj, 'label', text)
            translated = self.get_text(text)
            original_set_text(self_obj, translated)
            
        def patched_set_markup(self_obj, markup):
            # Markup is tricky. We assume markup structure contains the text keys.
            # For robust simple usage, we scan for >text<
            # But mostly we just translate if it's a known full string with markup in the dict.
            self._store_original(self_obj, 'markup', markup)
            
            # 1. Try translating entire markup string
            translated = self.get_text(markup)
            if translated != markup:
                 original_set_markup(self_obj, translated)
                 return

            # 2. Heuristic: Replace content between tags if it matches a key
            # Simple approach: If markup contains a key we know, replace it.
            # This is expensive to scan ALL keys. 
            # Better: if user calls set_markup(_("<b>Bold</b>")), it's already translated.
            # So we usually just pass it through if get_text didn't hit.
            original_set_markup(self_obj, markup)

        Gtk.Label.__init__ = patched_init
        Gtk.Label.set_text = patched_set_text
        Gtk.Label.set_markup = patched_set_markup

    def _patch_gtk_button(self):
        original_init = Gtk.Button.__init__
        original_set_label = Gtk.Button.set_label
        
        def patched_init(self_obj, **kwargs):
            if 'label' in kwargs:
                self._store_original(self_obj, 'label', kwargs['label'])
                kwargs['label'] = self.get_text(kwargs['label'])
            original_init(self_obj, **kwargs)
            
        def patched_set_label(self_obj, label):
            self._store_original(self_obj, 'label', label)
            original_set_label(self_obj, self.get_text(label))
            
        Gtk.Button.__init__ = patched_init
        Gtk.Button.set_label = patched_set_label

    def _patch_gtk_window(self):
        # Covers Gtk.Window, Adw.Window, Adw.ApplicationWindow
        original_init = Gtk.Window.__init__
        original_set_title = Gtk.Window.set_title
        
        def patched_init(self_obj, **kwargs):
            if 'title' in kwargs:
                self._store_original(self_obj, 'title', kwargs['title'])
                kwargs['title'] = self.get_text(kwargs['title'])
            original_init(self_obj, **kwargs)
            
        def patched_set_title(self_obj, title):
            self._store_original(self_obj, 'title', title)
            original_set_title(self_obj, self.get_text(title))
            
        Gtk.Window.__init__ = patched_init
        Gtk.Window.set_title = patched_set_title

    def _patch_adw_preferences_group(self):
        original_init = Adw.PreferencesGroup.__init__
        original_set_title = Adw.PreferencesGroup.set_title
        original_set_desc = Adw.PreferencesGroup.set_description
        
        def patched_init(self_obj, **kwargs):
            if 'title' in kwargs:
                self._store_original(self_obj, 'title', kwargs['title'])
                kwargs['title'] = self.get_text(kwargs['title'])
            if 'description' in kwargs:
                self._store_original(self_obj, 'description', kwargs['description'])
                kwargs['description'] = self.get_text(kwargs['description'])
            original_init(self_obj, **kwargs)
            
        def patched_set_title(self_obj, title):
            self._store_original(self_obj, 'title', title)
            original_set_title(self_obj, self.get_text(title))

        def patched_set_desc(self_obj, desc):
            self._store_original(self_obj, 'description', desc)
            original_set_desc(self_obj, self.get_text(desc))
            
        Adw.PreferencesGroup.__init__ = patched_init
        Adw.PreferencesGroup.set_title = patched_set_title
        Adw.PreferencesGroup.set_description = patched_set_desc

    def _patch_adw_action_row(self):
        original_init = Adw.ActionRow.__init__
        original_set_title = Adw.ActionRow.set_title
        original_set_subtitle = Adw.ActionRow.set_subtitle
        
        def patched_init(self_obj, **kwargs):
            if 'title' in kwargs:
                self._store_original(self_obj, 'title', kwargs['title'])
                kwargs['title'] = self.get_text(kwargs['title'])
            if 'subtitle' in kwargs:
                self._store_original(self_obj, 'subtitle', kwargs['subtitle'])
                kwargs['subtitle'] = self.get_text(kwargs['subtitle'])
            original_init(self_obj, **kwargs)

        def patched_set_title(self_obj, title):
            self._store_original(self_obj, 'title', title)
            original_set_title(self_obj, self.get_text(title))

        def patched_set_subtitle(self_obj, subtitle):
            self._store_original(self_obj, 'subtitle', subtitle)
            original_set_subtitle(self_obj, self.get_text(subtitle))

        Adw.ActionRow.__init__ = patched_init
        Adw.ActionRow.set_title = patched_set_title
        Adw.ActionRow.set_subtitle = patched_set_subtitle

    def _patch_adw_status_page(self):
        original_init = Adw.StatusPage.__init__
        original_set_title = Adw.StatusPage.set_title
        original_set_desc = Adw.StatusPage.set_description
        
        def patched_init(self_obj, **kwargs):
            if 'title' in kwargs:
                self._store_original(self_obj, 'title', kwargs['title'])
                kwargs['title'] = self.get_text(kwargs['title'])
            if 'description' in kwargs:
                self._store_original(self_obj, 'description', kwargs['description'])
                kwargs['description'] = self.get_text(kwargs['description'])
            original_init(self_obj, **kwargs)

        def patched_set_title(self_obj, title):
            self._store_original(self_obj, 'title', title)
            original_set_title(self_obj, self.get_text(title))

        def patched_set_desc(self_obj, desc):
            self._store_original(self_obj, 'description', desc)
            original_set_desc(self_obj, self.get_text(desc))
            
        Adw.StatusPage.__init__ = patched_init
        Adw.StatusPage.set_title = patched_set_title
        Adw.StatusPage.set_description = patched_set_desc

    def _patch_adw_window_title(self):
        original_init = Adw.WindowTitle.__init__
        original_set_title = Adw.WindowTitle.set_title
        original_set_subtitle = Adw.WindowTitle.set_subtitle
        
        # Adw.WindowTitle init is weird, mostly uses properties. 
        # But let's safe guard.
        def patched_init(self_obj, **kwargs):
            if 'title' in kwargs:
                 self._store_original(self_obj, 'title', kwargs['title'])
                 kwargs['title'] = self.get_text(kwargs['title'])
            if 'subtitle' in kwargs:
                 self._store_original(self_obj, 'subtitle', kwargs['subtitle'])
                 kwargs['subtitle'] = self.get_text(kwargs['subtitle'])
            original_init(self_obj, **kwargs)

        def patched_set_title(self_obj, title):
            self._store_original(self_obj, 'title', title)
            original_set_title(self_obj, self.get_text(title))
            
        def patched_set_subtitle(self_obj, subtitle):
            self._store_original(self_obj, 'subtitle', subtitle)
            original_set_subtitle(self_obj, self.get_text(subtitle))

        Adw.WindowTitle.__init__ = patched_init
        Adw.WindowTitle.set_title = patched_set_title
        Adw.WindowTitle.set_subtitle = patched_set_subtitle

    def _patch_adw_message_dialog(self):
        original_init = Adw.MessageDialog.__init__
        original_set_heading = Adw.MessageDialog.set_heading
        original_set_body = Adw.MessageDialog.set_body
        original_add_response = Adw.MessageDialog.add_response
        
        def patched_init(self_obj, **kwargs):
            if 'heading' in kwargs:
                self._store_original(self_obj, 'heading', kwargs['heading'])
                kwargs['heading'] = self.get_text(kwargs['heading'])
            if 'body' in kwargs:
                self._store_original(self_obj, 'body', kwargs['body'])
                kwargs['body'] = self._translate_body_smart(kwargs['body'])
            original_init(self_obj, **kwargs)

        def patched_set_heading(self_obj, heading):
            self._store_original(self_obj, 'heading', heading)
            original_set_heading(self_obj, self.get_text(heading))
            
        def patched_set_body(self_obj, body):
            self._store_original(self_obj, 'body', body)
            original_set_body(self_obj, self._translate_body_smart(body))
            
        def patched_add_response(self_obj, id, label):
            # Responses are stored internally, hard to track via property.
            # But we can just translate the label on the way in.
            if label:
                label = self.get_text(label)
            original_add_response(self_obj, id, label)

        Adw.MessageDialog.__init__ = patched_init
        Adw.MessageDialog.set_heading = patched_set_heading
        Adw.MessageDialog.set_body = patched_set_body
        Adw.MessageDialog.add_response = patched_add_response
        
    def _translate_body_smart(self, body):
        """Preserve bullets and newlines when translating body."""
        if not body: return body
        lines = body.splitlines()
        translated_lines = []
        for line in lines:
            if not line.strip():
                translated_lines.append(line)
                continue
            
            prefix = ""
            content = line
            # Check for bullets
            if line.lstrip().startswith("• "):
                prefix = "• "
                content = line.lstrip()[2:]
            
            trans = self.get_text(content.strip())
            # Reconstruct
            translated_lines.append(f"{prefix}{trans}")
            
        return "\n".join(translated_lines)

    def _patch_adw_toast(self):
        original_init = Adw.Toast.__init__
        original_set_title = Adw.Toast.set_title
        
        def patched_init(self_obj, **kwargs):
            if 'title' in kwargs:
                self._store_original(self_obj, 'title', kwargs['title'])
                kwargs['title'] = self.get_text(kwargs['title'])
            original_init(self_obj, **kwargs)
            
        def patched_set_title(self_obj, title):
            self._store_original(self_obj, 'title', title)
            original_set_title(self_obj, self.get_text(title))
            
        Adw.Toast.__init__ = patched_init
        Adw.Toast.set_title = patched_set_title
        
    def _patch_adw_about_window(self):
        original_init = Adw.AboutWindow.__init__
        original_set_app = Adw.AboutWindow.set_application_name
        original_set_dev = Adw.AboutWindow.set_developer_name
        original_set_comments = Adw.AboutWindow.set_comments
        
        def patched_init(self_obj, **kwargs):
            for k in ['application_name', 'developer_name', 'comments']:
                if k in kwargs:
                    self._store_original(self_obj, k, kwargs[k])
                    kwargs[k] = self.get_text(kwargs[k])
            original_init(self_obj, **kwargs)
            
        def patched_set_app(self_obj, name):
            self._store_original(self_obj, 'application_name', name)
            original_set_app(self_obj, self.get_text(name))
            
        def patched_set_dev(self_obj, name):
            self._store_original(self_obj, 'developer_name', name)
            original_set_dev(self_obj, self.get_text(name))
            
        def patched_set_comments(self_obj, comments):
            self._store_original(self_obj, 'comments', comments)
            original_set_comments(self_obj, self.get_text(comments))
            
        Adw.AboutWindow.__init__ = patched_init
        Adw.AboutWindow.set_application_name = patched_set_app
        Adw.AboutWindow.set_developer_name = patched_set_dev
        Adw.AboutWindow.set_comments = patched_set_comments

    # --- PUBLIC API ---

    def register_widget(self, widget):
        """
        No-op in new architecture as patching is automatic globally.
        Kept for backward compatibility.
        """
        pass

# Global Instance
_manager_instance = None

def get_localization_manager():
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SimpleLocalizationManager()
    return _manager_instance

def _(text):
    return get_localization_manager().get_text(text)