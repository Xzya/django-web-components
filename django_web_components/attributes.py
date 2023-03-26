from typing import Tuple, Union

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
        if value is None or value is False:
            continue
        if value is True:
            attr_list.append(conditional_escape(key))
        else:
            attr_list.append(format_html('{}="{}"', key, value))

    return mark_safe(SafeString(" ").join(attr_list))


def merge_attributes(*args: dict) -> dict:
    """
    Merges the input dictionaries and returns a new dictionary.

    Notes:
    ------
    The merge process is performed as follows:
    - "class" values are normalized / concatenated
    - Other values are added to the final dictionary as is
    """
    result = AttributeBag()

    for to_merge in args:
        for key, value in to_merge.items():
            if key == "class":
                klass = result.get("class")
                if klass != value:
                    result["class"] = normalize_class([klass, value])
            elif key != "":
                result[key] = value

    return result


def append_attributes(*args: dict) -> dict:
    """
    Merges the input dictionaries and returns a new dictionary.

    If a key is present in multiple dictionaries, its values are concatenated with a space character
    as separator in the final dictionary.
    """
    result = AttributeBag()

    for to_merge in args:
        for key, value in to_merge.items():
            if key in result:
                result[key] += " " + value
            else:
                result[key] = value

    return result


def normalize_class(value: Union[str, list, tuple, dict]) -> str:
    """
    Normalizes the given class value into a string.

    Notes:
    ------
    The normalization process is performed as follows:
    - If the input value is a string, it is returned as is.
    - If the input value is a list or a tuple, its elements are recursively normalized and concatenated
      with a space character as separator.
    - If the input value is a dictionary, its keys are concatenated with a space character as separator
      only if their corresponding values are truthy.
    """
    result = ""

    if isinstance(value, str):
        result = value
    elif isinstance(value, (list, tuple)):
        for v in value:
            normalized = normalize_class(v)
            if normalized:
                result += normalized + " "
    elif isinstance(value, dict):
        for key, val in value.items():
            if val:
                result += key + " "

    return result.strip()


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
