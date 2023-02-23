from django.template import Context, Template
from django.test import TestCase

from django_web_components import component
from django_web_components.template import template_cache, CachedTemplate


class CachedTemplateTest(TestCase):
    def setUp(self) -> None:
        template_cache.clear()
        component.registry.clear()

    def test_caches_template(self):
        template = CachedTemplate("hello", name="test")

        self.assertEqual(
            template.render(Context()),
            "hello",
        )
        self.assertTrue("test" in template_cache)
        self.assertTrue(isinstance(template_cache["test"], Template))

    def test_doesnt_cache_template_if_no_name_given(self):
        template = CachedTemplate("hello")

        self.assertEqual(
            template.render(Context()),
            "hello",
        )
        self.assertTrue("test" not in template_cache)

    def test_uses_cached_template(self):
        template_cache["test"] = cached_template = Template("cached hello")

        template = CachedTemplate("hello", name="test")
        self.assertEqual(
            template.render(Context()),
            "cached hello",
        )
        self.assertTrue(template_cache["test"] is cached_template)

    def test_can_render_component(self):
        @component.register("hello")
        def dummy(context):
            return CachedTemplate(
                """<div>Hello, world!</div>""",
                name="hello",
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}{% endhello %}
                """
            ).render(Context()),
            """
            <div>Hello, world!</div>
            """,
        )
