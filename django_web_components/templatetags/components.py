import re
from typing import Union

from django import template
from django.template import TemplateSyntaxError, NodeList
from django.template.base import FilterExpression
from django.utils.regex_helper import _lazy_re_compile

from django_web_components.component import (
    AttributeBag,
    token_kwargs,
    render_component,
    get_component_tag_formatter,
    attributes_to_string,
    merge_attributes,
)
from django_web_components.conf import app_settings

register = template.Library()


def create_component_tag(component_name):
    def do_component(parser, token):
        tag_name, *remaining_bits = token.split_contents()

        formatter = get_component_tag_formatter()

        # If this is a block tag, expect the closing tag
        if tag_name == formatter.format_block_start_tag(component_name):
            nodelist = parser.parse((formatter.format_block_end_tag(component_name),))
            parser.delete_first_token()
        else:
            nodelist = NodeList()

        # Bits that are not keyword args are interpreted as `True` values
        all_bits = [bit if "=" in bit else f"{bit}=True" for bit in remaining_bits]
        raw_attributes = token_kwargs(all_bits, parser)

        # process the slots
        slots = {}
        for node in nodelist:
            if isinstance(node, SlotNode):
                slot_name = node.name
            else:
                # non SlotNodes are considered as part of the default slot
                slot_name = app_settings.DEFAULT_SLOT_NAME
                # TODO: Should we ignore TextNodes with whitespace?

            # initialize the slot
            if slot_name not in slots:
                slots[slot_name] = SlotNodeList()

            # add the slot to the component
            slots[slot_name].append(node)

        return ComponentNode(
            name=component_name,
            attributes=raw_attributes,
            slots=slots,
        )

    return do_component


class ComponentNode(template.Node):
    def __init__(self, name, attributes, slots):
        self.name = name
        self.attributes = attributes
        self.slots = slots

    def render(self, context):
        # We may need to access the slot's attributes inside the component's template,
        # so we need to resolve them
        # TODO: is this thread safe?
        for slot_name, slots in self.slots.items():
            for slot in slots:
                if isinstance(slot, SlotNode):
                    slot.resolve_attributes(context)

        attributes = AttributeBag({key: value.resolve(context) for key, value in self.attributes.items()})

        return render_component(
            name=self.name,
            attributes=attributes,
            slots=self.slots,
            context=context,
        )


@register.tag("slot")
def do_slot(parser, token):
    tag_name, *remaining_bits = token.split_contents()

    if len(remaining_bits) < 1:
        raise TemplateSyntaxError("'%s' takes at least one argument, the slot name." % tag_name)

    slot_name = remaining_bits.pop(0).strip('"')

    # Bits that are not keyword args are interpreted as `True` values
    all_bits = [bit if "=" in bit else f"{bit}=True" for bit in remaining_bits]
    raw_attributes = token_kwargs(all_bits, parser)

    nodelist = parser.parse(parse_until=["endslot"])
    parser.delete_first_token()

    return SlotNode(slot_name, nodelist, raw_attributes)


class SlotNode(template.Node):
    def __init__(self, name: str = None, nodelist: NodeList = None, attributes: dict = None):
        self.name = name or ""
        self.nodelist = nodelist or NodeList()
        self.raw_attributes = attributes
        self.attributes = {}

    def resolve_attributes(self, context):
        self.attributes = AttributeBag({key: value.resolve(context) for key, value in self.raw_attributes.items()})

    def render(self, context):
        attributes = AttributeBag({key: value.resolve(context) for key, value in self.raw_attributes.items()})

        extra_context = {
            "attributes": attributes,
        }

        with context.update(extra_context):
            return self.nodelist.render(context)


class SlotNodeList(NodeList):
    @property
    def attributes(self) -> dict:
        if len(self) == 1 and hasattr(self[0], "attributes"):
            return self[0].attributes
        return AttributeBag()


@register.tag("render_slot")
def do_render_slot(parser, token):
    bits = token.split_contents()[1:]
    if not bits:
        raise TemplateSyntaxError("'render_slot' statement requires at least one argument")

    if len(bits) > 2:
        raise TemplateSyntaxError("'render_slot' statement requires at most two arguments")

    values = [parser.compile_filter(bit) for bit in bits]

    if len(values) == 2:
        [slot, argument] = values
    else:
        slot = values.pop()
        argument = None

    return RenderSlotNode(slot, argument)


class RenderSlotNode(template.Node):
    def __init__(self, slot: FilterExpression, argument: Union[FilterExpression, None] = None):
        self.slot = slot
        self.argument = argument

    def render(self, context):
        argument = None
        if self.argument:
            argument = self.argument.resolve(context, ignore_failures=True)

        slot = self.slot.resolve(context, ignore_failures=True)
        if slot is None:
            return ""

        if isinstance(slot, SlotNode):
            let = slot.attributes.get("let", None)
            if let and not argument:
                raise TemplateSyntaxError(
                    "'let' was defined on the slot but no argument was passed " "to 'render_slot'"
                )

            if let and argument:
                with context.update(
                    {
                        let: argument,
                    }
                ):
                    return slot.render(context)

        return slot.render(context)


attribute_re = _lazy_re_compile(
    r"""
    (?P<attr>
        [@\w:_\.-]+
    )
    (?P<sign>
        \+?=
    )
    (?P<value>
    ['"]? # start quote
        [^"']*
    ['"]? # end quote
    )
    """,
    re.VERBOSE | re.UNICODE,
)


@register.tag("merge_attrs")
def do_merge_attrs(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument, the attributes." % bits[0])
    attributes = parser.compile_filter(bits[1])
    attr_list = bits[2:]

    default_attrs = []
    append_attrs = []
    for pair in attr_list:
        match = attribute_re.match(pair)
        if not match:
            raise TemplateSyntaxError(
                "Malformed arguments to '%s' tag. You must pass the attributes " 'in the form attr="value".' % bits[0]
            )
        dct = match.groupdict()
        attr, sign, value = (
            dct["attr"],
            dct["sign"],
            parser.compile_filter(dct["value"]),
        )
        if sign == "=":
            default_attrs.append((attr, value))
        elif sign == "+=":
            append_attrs.append((attr, value))
        else:
            raise TemplateSyntaxError("Unknown sign '%s' for attribute '%s'" % (sign, attr))

    return MergeAttrsNode(attributes, default_attrs, append_attrs)


class MergeAttrsNode(template.Node):
    def __init__(self, attributes, default_attrs, append_attrs):
        self.attributes = attributes
        self.default_attrs = default_attrs
        self.append_attrs = append_attrs

    def render(self, context):
        bound_attributes: dict = self.attributes.resolve(context)

        attribute_defaults = {key: value.resolve(context) for key, value in self.default_attrs}

        append_attributes = {key: value.resolve(context) for key, value in self.append_attrs}

        attrs = merge_attributes(
            attributes=bound_attributes,
            attribute_defaults=attribute_defaults,
            append_attributes=append_attributes,
        )

        return attributes_to_string(attrs)
