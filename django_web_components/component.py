from types import FunctionType
from typing import Union

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.template import loader
from django.utils.html import conditional_escape, format_html
from django.utils.module_loading import import_string
from django.utils.regex_helper import _lazy_re_compile
from django.utils.safestring import mark_safe, SafeString

from django_web_components.conf import app_settings
from django_web_components.registry import ComponentRegistry

# Global component registry
registry = ComponentRegistry()


def register(name: str, target_register: template.Library = None):
    """
    Class decorator to register a component.
    """
    from django_web_components.templatetags.components import (
        register as tag_register,
        create_component_tag,
    )

    if target_register is None:
        target_register = tag_register

    def decorator(component):
        registry.register(name=name, component=component)

        formatter = get_component_tag_formatter()

        # Inline component
        target_register.tag(formatter.format_inline_tag(name), create_component_tag(name))

        # Block component
        target_register.tag(formatter.format_block_start_tag(name), create_component_tag(name))

        return component

    return decorator


class Component:
    template_name = None
    attributes: "AttributeBag"
    slots: dict

    def __init__(
        self,
        attributes: "AttributeBag" = None,
        slots: dict = None,
    ):
        self.attributes = attributes or AttributeBag()
        self.slots = slots or {}

    def get_context_data(self, **kwargs) -> dict:
        # TODO: do we need kwargs here?
        return {}

    def get_template_name(self) -> Union[str, list, tuple]:
        if not self.template_name:
            raise ImproperlyConfigured(f"Template name is not set for Component {self.__class__.__name__}")

        return self.template_name

    def render(self, context) -> str:
        template_name = self.get_template_name()

        return loader.render_to_string(template_name, context)


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


def render_component(*, name: str, attributes: dict, slots: dict, context: template.Context):
    """
    Render the component with the given name.
    """
    extra_context = {
        "attributes": attributes,
        "slots": slots,
    }

    component_class = registry.get(name)

    # handle function components
    if isinstance(component_class, FunctionType):
        with context.push(extra_context):
            return component_class(context)

    # handle class based components
    component = component_class(
        attributes=attributes,
        slots=slots,
    )
    extra_context.update(component.get_context_data())

    with context.push(extra_context):
        return component.render(context)


kwarg_re = _lazy_re_compile(r"(?:([\w\-\:\@\.]+)=)?(.+)")


# This is the same as the original, but the regex is modified to accept
# special characters
def token_kwargs(bits, parser, support_legacy=False):
    """
    Parse token keyword arguments and return a dictionary of the arguments
    retrieved from the ``bits`` token list.

    `bits` is a list containing the remainder of the token (split by spaces)
    that is to be checked for arguments. Valid arguments are removed from this
    list.

    `support_legacy` - if True, the legacy format ``1 as foo`` is accepted.
    Otherwise, only the standard ``foo=1`` format is allowed.

    There is no requirement for all remaining token ``bits`` to be keyword
    arguments, so return the dictionary as soon as an invalid argument format
    is reached.
    """
    if not bits:
        return {}
    match = kwarg_re.match(bits[0])
    kwarg_format = match and match[1]
    if not kwarg_format:
        if not support_legacy:
            return {}
        if len(bits) < 3 or bits[1] != "as":
            return {}

    kwargs = {}
    while bits:
        if kwarg_format:
            match = kwarg_re.match(bits[0])
            if not match or not match[1]:
                return kwargs
            key, value = match.groups()
            del bits[:1]
        else:
            if len(bits) < 3 or bits[1] != "as":
                return kwargs
            key, value = bits[2], bits[0]
            del bits[:3]
        kwargs[key] = parser.compile_filter(value)
        if bits and not kwarg_format:
            if bits[0] != "and":
                return kwargs
            del bits[:1]
    return kwargs


class ComponentTagFormatter:
    def format_block_start_tag(self, name: str) -> str:
        return name

    def format_block_end_tag(self, name: str) -> str:
        return f"end{name}"

    def format_inline_tag(self, name: str) -> str:
        return f"#{name}"


def get_component_tag_formatter():
    return import_string(app_settings.DEFAULT_COMPONENT_TAG_FORMATTER)()
