from django.conf import settings
from importlib import import_module
from django.core.exceptions import ImproperlyConfigured

DEFAULTS = {
    "GLOBAL_SERIALIZER": "drf_globalresponse.serializers.GlobalResponseSerializer",
    "DATA_FIELD": "data",
}

IMPORT_STRING = ["GLOBAL_SERIALIZER"]


def perform_import(val, setting_name):
    """
    Import a class or function from a string path.
    """
    if isinstance(val, str):
        try:
            module_path, class_name = val.rsplit(".", 1)
            module = import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ImproperlyConfigured(
                f"Could not import '{val}' for setting '{setting_name}': {e}"
            )
    return val


class AppSettings:
    def __init__(self, defaults=None, import_strings=None):
        self.defaults = defaults or {}
        self.import_strings = import_strings or []

        # Merge user settings with defaults
        self._user_settings = getattr(settings, "GLOBALRESPONSE_SETTINGS", {})
        self._merged_settings = self._deep_merge(self.defaults, self._user_settings)

    def _deep_merge(self, defaults, user_settings):
        """
        Recursively merge user settings into defaults.
        """
        merged = defaults.copy()
        for key, value in user_settings.items():
            if isinstance(value, dict) and key in merged:
                merged[key] = self._deep_merge(merged.get(key, {}), value)
            else:
                merged[key] = value
        return merged

    def __getattr__(self, name):
        if name not in self._merged_settings:
            raise AttributeError(f"Invalid setting: '{name}'")

        val = self._merged_settings[name]

        if name in self.import_strings:
            return perform_import(val, name)

        if isinstance(val, dict):
            return AppSettings(val, self.import_strings)

        return val


app_settings = AppSettings(DEFAULTS, IMPORT_STRING)
