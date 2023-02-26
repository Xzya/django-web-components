from types import FunctionType
from typing import Union

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.template import loader

from django_web_components.attributes import AttributeBag
from django_web_components.registry import ComponentRegistry
from django_web_components.tag_formatter import get_component_tag_formatter


class Component:
    """
    Base class for components.
    """

    template_name: str = None
    attributes: AttributeBag
    slots: dict

    def __init__(
        self,
        attributes: dict = None,
        slots: dict = None,
    ):
        self.attributes = attributes or AttributeBag()
        self.slots = slots or {}

    def get_context_data(self, **kwargs) -> dict:
        return {}

    def get_template_name(self) -> Union[str, list, tuple]:
        if not self.template_name:
            raise ImproperlyConfigured(f"Template name is not set for Component {self.__class__.__name__}")

        return self.template_name

    def render(self, context) -> str:
        template_name = self.get_template_name()

        return loader.render_to_string(template_name, context.flatten())


def render_component(*, name: str, attributes: dict, slots: dict, context: template.Context) -> str:
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


# Global component registry
registry = ComponentRegistry()


def register(name=None, component=None, target_register: template.Library = None):
    """
    Register a component.
    """
    from django_web_components.templatetags.components import (
        register as tag_register,
    )

    # use the default library if none is passed
    if target_register is None:
        target_register = tag_register

    def decorator(component):
        return _register(name=component.__name__, component=component, target_register=target_register)

    def decorator_with_custom_name(component):
        return _register(name=name, component=component, target_register=target_register)

    if name is None and component is None:
        # @register()
        return decorator

    elif name is not None and component is None:
        if callable(name):
            # @register or register(alert)
            return decorator(name)
        else:
            # @register("alert") or @register(name="alert")
            return decorator_with_custom_name

    elif name is not None and component is not None:
        # register("alert", alert)
        return _register(name=name, component=component, target_register=target_register)

    else:
        raise ValueError("Unsupported arguments to component.register: (%r, %r)" % (name, component))


def _register(name: str, component, target_register: template.Library):
    from django_web_components.templatetags.components import (
        create_component_tag,
    )

    # add the component to the registry
    registry.register(name=name, component=component)

    formatter = get_component_tag_formatter()

    # register the inline tag
    target_register.tag(formatter.format_inline_tag(name), create_component_tag(name))

    # register the block tag
    target_register.tag(formatter.format_block_start_tag(name), create_component_tag(name))

    return component
