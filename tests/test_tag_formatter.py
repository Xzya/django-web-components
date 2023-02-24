from django.template import Context, Template
from django.test import TestCase

from django_web_components import component
from django_web_components.tag_formatter import ComponentTagFormatter


class CustomComponentTagFormatter(ComponentTagFormatter):
    def format_block_start_tag(self, name: str) -> str:
        return f"#{name}"

    def format_block_end_tag(self, name: str) -> str:
        return f"/{name}"

    def format_inline_tag(self, name: str) -> str:
        return f"_{name}"


class ComponentTagFormatterTest(TestCase):
    def setUp(self) -> None:
        component.registry.clear()

    def test_can_change_component_block_tags(self):
        with self.settings(
            WEB_COMPONENTS={
                "DEFAULT_COMPONENT_TAG_FORMATTER": "tests.test_tag_formatter.CustomComponentTagFormatter",
            },
        ):

            @component.register("hello")
            def dummy(context):
                return Template("""<div>{% render_slot slots.inner_block %}</div>""").render(context)

            self.assertHTMLEqual(
                Template(
                    """
                    {% #hello %}Hello, world!{% /hello %}
                    """
                ).render(Context({})),
                """
                <div>Hello, world!</div>
                """,
            )

    def test_can_change_component_inline_tag(self):
        with self.settings(
            WEB_COMPONENTS={
                "DEFAULT_COMPONENT_TAG_FORMATTER": "tests.test_tag_formatter.CustomComponentTagFormatter",
            },
        ):

            @component.register("hello")
            def dummy(context):
                return Template("""<div>Hello, world!</div>""").render(context)

            self.assertHTMLEqual(
                Template(
                    """
                    {% _hello %}
                    """
                ).render(Context({})),
                """
                <div>Hello, world!</div>
                """,
            )
