import re
from typing import Union

from django import template
from django.template import TemplateSyntaxError, NodeList
from django.template.base import FilterExpression, Token, Parser
from django.utils.regex_helper import _lazy_re_compile
from django.utils.safestring import SafeString

from django_web_components.attributes import (
    AttributeBag,
    attributes_to_string,
    merge_attributes,
    split_attributes,
    append_attributes,
)
from django_web_components.component import (
    render_component,
    get_component_tag_formatter,
)
from django_web_components.conf import app_settings
from django_web_components.utils import token_kwargs

register = template.Library()


def create_component_tag(component_name: str):
    def do_component(parser: Parser, token: Token):
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
        special, attrs = split_attributes(raw_attributes)

        # process the slots
        slots = {}

        # All child nodes that are not inside a slot will be added to a default slot
        default_slot_name = app_settings.DEFAULT_SLOT_NAME
        default_slot = SlotNode(
            name=default_slot_name,
            nodelist=NodeList(),
            unresolved_attributes={},
            special=special,
        )
        slots[default_slot_name] = SlotNodeList()

        for node in nodelist:
            if isinstance(node, SlotNode):
                slot_name = node.name

                # initialize the slot
                if slot_name not in slots:
                    slots[slot_name] = SlotNodeList()

                slots[slot_name].append(node)
            else:
                # otherwise add the node to the default slot
                default_slot.nodelist.append(node)

        # add the default slot only if it's not empty
        if len(default_slot.nodelist) > 0:
            slots[default_slot_name].append(default_slot)

        return ComponentNode(
            name=component_name,
            unresolved_attributes=attrs,
            slots=slots,
        )

    return do_component


class ComponentNode(template.Node):
    name: str
    unresolved_attributes: dict
    slots: dict

    def __init__(self, name: str = None, unresolved_attributes: dict = None, slots: dict = None):
        self.name = name or ""
        self.unresolved_attributes = unresolved_attributes or {}
        self.slots = slots or {}

    def render(self, context):
        # We may need to access the slot's attributes inside the component's template,
        # so we need to resolve them
        #
        # We also clone the SlotNodes to make sure we don't have thread-safety issues since
        # we are storing the attributes on the node itself
        slots = {}
        for slot_name, slot_list in self.slots.items():
            # initialize the slot
            if slot_name not in slots:
                slots[slot_name] = SlotNodeList()

            for slot in slot_list:
                if isinstance(slot, SlotNode):
                    # clone the SlotNode
                    cloned_slot = SlotNode(
                        name=slot.name,
                        nodelist=slot.nodelist,
                        unresolved_attributes=slot.unresolved_attributes,
                        special=slot.special,
                    )
                    # resolve its attributes so that they can be accessed from the component template
                    cloned_slot.resolve_attributes(context)

                    slots[slot_name].append(cloned_slot)
                else:
                    slots[slot_name].append(slot)

        attributes = AttributeBag({key: value.resolve(context) for key, value in self.unresolved_attributes.items()})

        return render_component(
            name=self.name,
            attributes=attributes,
            slots=slots,
            context=context,
        )


@register.tag("slot")
def do_slot(parser: Parser, token: Token):
    tag_name, *remaining_bits = token.split_contents()

    if len(remaining_bits) < 1:
        raise TemplateSyntaxError("'%s' tag takes at least one argument, the slot name" % tag_name)

    slot_name = remaining_bits.pop(0).strip('"')

    # Bits that are not keyword args are interpreted as `True` values
    all_bits = [bit if "=" in bit else f"{bit}=True" for bit in remaining_bits]
    raw_attributes = token_kwargs(all_bits, parser)
    special, attrs = split_attributes(raw_attributes)

    nodelist = parser.parse(("endslot",))
    parser.delete_first_token()

    return SlotNode(
        name=slot_name,
        nodelist=nodelist,
        unresolved_attributes=attrs,
        special=special,
    )


class SlotNode(template.Node):
    name: str
    nodelist: NodeList
    unresolved_attributes: dict
    attributes: dict
    special: dict

    def __init__(
        self, name: str = None, nodelist: NodeList = None, unresolved_attributes: dict = None, special: dict = None
    ):
        self.name = name or ""
        self.nodelist = nodelist or NodeList()
        self.unresolved_attributes = unresolved_attributes or {}
        self.special = special or {}
        # Will be set by the ComponentNode
        self.attributes = AttributeBag()

    def resolve_attributes(self, context):
        self.attributes = AttributeBag(
            {key: value.resolve(context) for key, value in self.unresolved_attributes.items()}
        )

    def render(self, context):
        attributes = AttributeBag({key: value.resolve(context) for key, value in self.unresolved_attributes.items()})

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
def do_render_slot(parser: Parser, token: Token):
    tag_name, *remaining_bits = token.split_contents()
    if not remaining_bits:
        raise TemplateSyntaxError("'%s' tag takes at least one argument, the slot" % tag_name)

    if len(remaining_bits) > 2:
        raise TemplateSyntaxError("'%s' tag takes at most two arguments, the slot and the argument" % tag_name)

    values = [parser.compile_filter(bit) for bit in remaining_bits]

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

        if isinstance(slot, NodeList):
            return SafeString("".join([self.render_slot(node, argument, context) for node in slot]))

        return self.render_slot(slot, argument, context)

    def render_slot(self, slot, argument, context):
        if isinstance(slot, SlotNode):
            let = slot.special.get(":let", None)
            if let:
                let = let.resolve(context, ignore_failures=True)

            # if we were passed an argument and the :let attribute is defined,
            # add the argument to the context with the new name
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
        [\w\-\:\@\.\_]+
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
def do_merge_attrs(parser: Parser, token: Token):
    tag_name, *remaining_bits = token.split_contents()
    if not remaining_bits:
        raise TemplateSyntaxError("'%s' tag takes at least one argument, the attributes" % tag_name)

    attributes = parser.compile_filter(remaining_bits[0])
    attr_list = remaining_bits[1:]

    default_attrs = []
    append_attrs = []
    for pair in attr_list:
        match = attribute_re.match(pair)
        if not match:
            raise TemplateSyntaxError(
                "Malformed arguments to '%s' tag. You must pass the attributes in the form attr=\"value\"." % tag_name
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

        default_attrs = {key: value.resolve(context) for key, value in self.default_attrs}

        append_attrs = {key: value.resolve(context) for key, value in self.append_attrs}

        attrs = merge_attributes(
            default_attrs,
            bound_attributes,
        )
        attrs = append_attributes(attrs, append_attrs)

        return attributes_to_string(attrs)
