import inspect

from django.conf import settings as django_settings
from django.db import models


class Settings:
    """Utility class used to load and save settings, can be used as model.

    Some members are excluded from being configuration:
    - Protected/private members;
    - On django model, "objects" and "Meta";
    - Class declaration and callables

    Example:

        ```
        class MySettings(Settings):
            a = 13
            b = 12

        my_settings = MySettings().load('MY_SETTINGS_KEY')
        print(my_settings.a, my_settings.get('b'))
        ```

    This will load values from django project settings.
    """

    def load(self, key, module=None):
        """Load settings from module's item specified by its member name. When
        no module is provided, uses ``django.conf.settings``.

        :param str key: module member name.
        :param module: configuration object.
        :returns self
        """
        if module is None:
            module = django_settings
        settings = getattr(module, key, None)
        if settings:
            self.update(settings)
        return self

    def update(self, settings):
        """Update self's values from provided settings. ``settings`` can be an
        iterable of ``(key, value)``.

        :param dict|Settings|iterable settings: value to update from.
        """
        if isinstance(settings, (dict, Settings)):
            settings = settings.items()
        for key, value in settings:
            if hasattr(self, key) and self.is_config_item(key, value):
                setattr(self, key, value)

    def get(self, key, default=None):
        """Return settings' value for provided key."""
        return getattr(self, key, default)

    def items(self):
        """Iterate over items members, as tupple of ``key, value``."""
        for key in dir(self):
            value = getattr(self, key)
            if self.is_config_item(key, value):
                yield key, value

    def is_config_item(self, key, value):
        """Return True if key/value item is a configuration setting."""
        if key.startswith("_") or callable(value) or inspect.isclass(value):
            return False
        if isinstance(self, models.Model) and key == "object":
            return False
        return True
