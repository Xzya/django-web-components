from django.utils.module_loading import import_string

from django_web_components.conf import app_settings


class ComponentTagFormatter:
    """
    The default component tag formatter.
    """

    def format_block_start_tag(self, name: str) -> str:
        """
        Formats the start tag of a block component.
        """
        return name

    def format_block_end_tag(self, name: str) -> str:
        """
        Formats the end tag of a block component.
        """
        return f"end{name}"

    def format_inline_tag(self, name: str) -> str:
        """
        Formats the tag of an inline component.
        """
        return f"#{name}"


def get_component_tag_formatter():
    """
    Returns an instance of the currently configured component tag formatter.
    """
    return import_string(app_settings.DEFAULT_COMPONENT_TAG_FORMATTER)()
