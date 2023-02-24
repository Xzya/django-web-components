from typing import Tuple

from django.utils.html import format_html, conditional_escape
from django.utils.safestring import mark_safe, SafeString


class AttributeBag(dict):
    def __str__(self):
        """
        Convert the attributes into a single HTML string.
        """
        return attributes_to_string(self)


def attributes_to_string(attributes: dict) -> str:
    """
    Convert a dict of attributes to a string.
    """
    attr_list = []

    for key, value in attributes.items():
        if value is not None and value is not True:
            attr_list.append(format_html('{}="{}"', key, value))
        else:
            attr_list.append(conditional_escape(key))

    return mark_safe(SafeString(" ").join(attr_list))


def merge_attributes(attributes: dict, attribute_defaults: dict = None, append_attributes: dict = None) -> dict:
    """
    Merge additional attributes / values into the attribute bag.
    """
    appendable_keys = ("class",)

    attrs = AttributeBag(attribute_defaults) if attribute_defaults else AttributeBag()

    for key, value in attributes.items():
        # append the value if it's one of the appendable keys
        if key in appendable_keys and key in attrs:
            attrs[key] += " " + value
        else:
            attrs[key] = value

    if append_attributes:
        for key, value in append_attributes.items():
            if key in attrs:
                attrs[key] += " " + value
            else:
                attrs[key] = value

    return attrs


def split_attributes(attributes: dict) -> Tuple[dict, dict]:
    """
    Splits the given attributes into "special" attributes (like :let) and normal attributes.
    """
    special_attrs = (":let",)

    attrs = {}
    special = {}
    for key, value in attributes.items():
        if key in special_attrs:
            special[key] = value
        else:
            attrs[key] = value

    return special, attrs
