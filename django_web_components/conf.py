from django.conf import settings

SETTINGS_KEY = "WEB_COMPONENTS"

DEFAULT_SLOT_NAME = "inner_block"
DEFAULT_COMPONENT_TAG_FORMATTER = "django_web_components.tag_formatter.ComponentTagFormatter"


class AppSettings:
    @property
    def settings(self):
        return getattr(settings, SETTINGS_KEY, {})

    @property
    def DEFAULT_SLOT_NAME(self):
        return self.settings.get("DEFAULT_SLOT_NAME", DEFAULT_SLOT_NAME)

    @property
    def DEFAULT_COMPONENT_TAG_FORMATTER(self):
        return self.settings.get("DEFAULT_COMPONENT_TAG_FORMATTER", DEFAULT_COMPONENT_TAG_FORMATTER)


app_settings = AppSettings()
