from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template, NodeList
from django.template.base import TextNode
from django.test import TestCase

import django_web_components.attributes
from django_web_components import component
from django_web_components.component import (
    Component,
)
from django_web_components.templatetags.components import SlotNodeList, SlotNode


class ComponentTest(TestCase):
    def test_get_template_name_returns_template_name(self):
        class DummyComponent(Component):
            template_name = "foo.html"

        self.assertEqual(DummyComponent().get_template_name(), "foo.html")

    def test_get_template_name_raises_if_no_template_name_set(self):
        class DummyComponent(Component):
            pass

        with self.assertRaises(ImproperlyConfigured):
            DummyComponent().get_template_name()

    def test_renders_template(self):
        class DummyComponent(Component):
            template_name = "simple_template.html"

        self.assertHTMLEqual(
            DummyComponent().render(
                Context(
                    {
                        "message": "world",
                    }
                )
            ),
            """<div>Hello, world!</div>""",
        )


class ExampleComponentsTest(TestCase):
    def setUp(self) -> None:
        component.registry.clear()

    def test_component_with_inline_tag(self):
        @component.register("hello")
        def dummy(context):
            return Template("""<div>Hello, world!</div>""").render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% #hello %}
                """
            ).render(Context({})),
            """
            <div>Hello, world!</div>
            """,
        )

    def test_component_with_inline_tag_and_attributes(self):
        @component.register("hello")
        def dummy(context):
            return Template("""<div {{ attributes }}>Hello, world!</div>""").render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% #hello class="foo" x-on:click='bar' @click="baz" foo:bar.baz="foo" required %}
                """
            ).render(Context({})),
            """
            <div class="foo" x-on:click="bar" @click="baz" foo:bar.baz="foo" required>Hello, world!</div>
            """,
        )

    def test_simple_component(self):
        @component.register("hello")
        def dummy(context):
            return Template("""<div>Hello, world!</div>""").render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}{% endhello %}
                """
            ).render(Context({})),
            """
            <div>Hello, world!</div>
            """,
        )

    def test_component_with_name_with_colon(self):
        @component.register("hello:foo")
        def dummy(context):
            return Template("""<div>Hello, world!</div>""").render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello:foo %}{% endhello:foo %}
                """
            ).render(Context({})),
            """
            <div>Hello, world!</div>
            """,
        )

    def test_component_with_name_with_dot(self):
        @component.register("hello.foo")
        def dummy(context):
            return Template("""<div>Hello, world!</div>""").render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello.foo %}{% endhello.foo %}
                """
            ).render(Context({})),
            """
            <div>Hello, world!</div>
            """,
        )

    def test_component_with_context_passed_in(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>{{ message }}</div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% with message="hello" %}
                    {% hello message="hello" %}{% endhello %}
                {% endwith %}
                """
            ).render(Context({})),
            """
            <div>hello</div>
            """,
        )

    # Attributes

    def test_component_with_attributes(self):
        @component.register("hello")
        def dummy(context):
            return Template("""<div {{ attributes }}>Hello, world!</div>""").render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello class="foo" x-on:click='bar' @click="baz" foo:bar.baz="foo" required %}{% endhello %}
                """
            ).render(Context({})),
            """
            <div class="foo" x-on:click="bar" @click="baz" foo:bar.baz="foo" required>Hello, world!</div>
            """,
        )

    def test_component_with_empty_attributes(self):
        @component.register("hello")
        def dummy(context):
            return Template("""<div {{ attributes }}>Hello, world!</div>""").render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello class="" limit='' required %}{% endhello %}
                """
            ).render(Context({})),
            """
            <div class="" limit="" required>Hello, world!</div>
            """,
        )

    def test_attributes_from_context_variables(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div {{ attributes }}>
                    {% render_slot slots.inner_block %}
                </div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% with object_id="123" message="Hello" %}
                    {% hello id=object_id %}
                        <div>{{ message }}</div>
                    {% endhello %}
                {% endwith %}
                """
            ).render(Context({})),
            """
            <div id="123">
                <div>Hello</div>
            </div>
            """,
        )

    def test_attributes_with_defaults(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div {% merge_attrs attributes class="font-bold" @click="foo" %}></div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello id="123" class="some-class" %}{% endhello %}
                """
            ).render(Context({})),
            """
            <div id="123" class="font-bold some-class" @click="foo"></div>
            """,
        )

    # Slots

    def test_component_with_default_slot(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>{% render_slot slots.inner_block %}</div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}Hello{% endhello %}
                """
            ).render(Context({})),
            """
            <div>Hello</div>
            """,
        )

    def test_component_with_named_slot(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>
                    <div>{% render_slot slots.title %}</div>
                    <div>{% render_slot slots.inner_block %}</div>
                </div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}
                    {% slot title %}Title{% endslot %}
                    Default slot
                {% endhello %}
                """
            ).render(Context({})),
            """
            <div>
                <div>Title</div>
                <div>Default slot</div>
            </div>
            """,
        )

    def test_component_with_multiple_slots(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>
                    <h1>{% render_slot slots.title %}</h1>
                    <div>{% render_slot slots.body %}</div>
                    <div>{% render_slot slots.inner_block %}</div>
                </div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}
                    {% slot title %}Title{% endslot %}
                    {% slot body %}Body{% endslot %}
                    <span>Hello</span>
                {% endhello %}
                """
            ).render(Context({})),
            """
            <div>
                <h1>Title</h1>
                <div>Body</div>
                <div><span>Hello</span></div>
            </div>
            """,
        )

    def test_component_with_duplicate_slot(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <ul>
                    {% for row in slots.row %}
                        <li>{% render_slot row %}</li>
                    {% endfor %}
                </ul>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}
                    {% slot row %}Row 1{% endslot %}
                    {% slot row %}Row 2{% endslot %}
                    {% slot row %}Row 3{% endslot %}
                {% endhello %}
                """
            ).render(Context({})),
            """
            <ul>
                <li>Row 1</li>
                <li>Row 2</li>
                <li>Row 3</li>
            </ul>
            """,
        )

    def test_component_with_duplicate_slot_without_for_loop(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <ul>
                    {% render_slot slots.row %}
                </ul>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}
                    {% slot row %}
                        <li>Row 1</li>
                    {% endslot %}
                    {% slot row %}
                        <li>Row 2</li>
                    {% endslot %}
                    {% slot row %}
                        <li>Row 3</li>
                    {% endslot %}
                {% endhello %}
                """
            ).render(Context({})),
            """
            <ul>
                <li>Row 1</li>
                <li>Row 2</li>
                <li>Row 3</li>
            </ul>
            """,
        )

    def test_component_with_duplicate_slot_but_only_one_passed_in(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <ul>
                    {% for row in slots.row %}
                        <li>{% render_slot row %}</li>
                    {% endfor %}
                </ul>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}
                    {% slot row %}Row 1{% endslot %}
                {% endhello %}
                """
            ).render(Context({})),
            """
            <ul>
                <li>Row 1</li>
            </ul>
            """,
        )

    # Slot attributes

    def test_slots_with_attributes(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div {{ attributes }} foo="bar">
                    <h1 {{ slots.title.attributes }}>{% render_slot slots.title %}</h1>
                    <div {{ slots.body.attributes }}>{% render_slot slots.body %}</div>
                </div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello id="123" %}
                    {% slot title class="title" %}Title{% endslot %}
                    {% slot body class="foo" x-on:click='bar' @click="baz" foo:bar.baz="foo" required %}
                        Body
                    {% endslot %}
                {% endhello %}
                """
            ).render(Context({})),
            """
            <div id="123" foo="bar">
                <h1 class="title">Title</h1>
                <div class="foo" x-on:click="bar" @click="baz" foo:bar.baz="foo" required>Body</div>
            </div>
            """,
        )

    # Scoped slots

    def test_can_render_scoped_slots(self):
        @component.register("table")
        def table(context):
            return Template(
                """
                <table>
                    <tr>
                        {% for col in slots.column %}
                            <th>{{ col.attributes.label }}</th>
                        {% endfor %}
                    </tr>
                    {% for row in rows %}
                        <tr>
                            {% for col in slots.column %}
                                <td>
                                    {% render_slot col row %}
                                </td>
                            {% endfor %}
                        </tr>
                    {% endfor %}
                </table>
                """
            ).render(context)

        context = Context(
            {
                "rows": [
                    {
                        "name": "John",
                        "age": 31,
                    },
                    {
                        "name": "Bob",
                        "age": 51,
                    },
                    {
                        "name": "Alice",
                        "age": 27,
                    },
                ],
            }
        )

        # directly accessing the variable
        self.assertHTMLEqual(
            Template(
                """
                {% table %}
                    {% slot column label="Name" %}
                        {{ row.name }}
                    {% endslot %}
                    {% slot column label="Age" %}
                        {{ row.age }}
                    {% endslot %}
                {% endtable %}
                """
            ).render(context),
            """
            <table>
                <tr>
                    <th>Name</th>
                    <th>Age</th>
                </tr>
                <tr>
                    <td>John</td>
                    <td>31</td>
                </tr>
                <tr>
                    <td>Bob</td>
                    <td>51</td>
                </tr>
                <tr>
                    <td>Alice</td>
                    <td>27</td>
                </tr>
            </table>
            """,
        )

        # using ':let' to define the context variable
        self.assertHTMLEqual(
            Template(
                """
                {% table %}
                    {% slot column :let="user" label="Name" %}
                        {{ user.name }}
                    {% endslot %}
                    {% slot column :let="user" label="Age" %}
                        {{ user.age }}
                    {% endslot %}
                {% endtable %}
                """
            ).render(context),
            """
            <table>
                <tr>
                    <th>Name</th>
                    <th>Age</th>
                </tr>
                <tr>
                    <td>John</td>
                    <td>31</td>
                </tr>
                <tr>
                    <td>Bob</td>
                    <td>51</td>
                </tr>
                <tr>
                    <td>Alice</td>
                    <td>27</td>
                </tr>
            </table>
            """,
        )

    def test_scoped_slot_works_on_default_slot(self):
        @component.register("unordered_list")
        def unordered_list(context):
            context["entries"] = context["attributes"].pop("entries", [])
            return Template(
                """
                <ul>
                    {% for entry in entries %}
                        <li>
                            {% render_slot slots.inner_block entry %}
                        </li>
                    {% endfor %}
                </ul>
                """
            ).render(context)

        context = Context(
            {
                "entries": ["apples", "bananas", "cherries"],
            }
        )

        # directly accessing the variable
        self.assertHTMLEqual(
            Template(
                """
                {% unordered_list entries=entries %}
                    I like {{ entry }}!
                {% endunordered_list %}
                """
            ).render(context),
            """
            <ul>
                <li>I like apples!</li>
                <li>I like bananas!</li>
                <li>I like cherries!</li>
            </ul>
            """,
        )

        # using ':let' to define the context variable
        self.assertHTMLEqual(
            Template(
                """
                {% unordered_list :let="fruit" entries=entries %}
                    I like {{ fruit }}!
                {% endunordered_list %}
                """
            ).render(context),
            """
            <ul>
                <li>I like apples!</li>
                <li>I like bananas!</li>
                <li>I like cherries!</li>
            </ul>
            """,
        )

    # Nested components

    def test_nested_component(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div {{ attributes }}>{% render_slot slots.inner_block %}</div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello class="foo" %}
                    {% hello class="bar" %}
                        Hello, world!
                    {% endhello %}
                {% endhello %}
                """
            ).render(Context({})),
            """
            <div class="foo">
                <div class="bar">
                    Hello, world!
                </div>
            </div>
            """,
        )

    def test_nested_component_with_slots(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div {{ attributes }}>
                    <div {{ slots.body.attributes }}>{% render_slot slots.body %}</div>
                </div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello class="hello1" %}
                    {% slot body class="foo" %}
                        {% hello class="hello2" %}
                            {% slot body class="bar" %}
                                Hello, world!
                            {% endslot %}
                        {% endhello %}
                    {% endslot %}
                {% endhello %}
                """
            ).render(Context({})),
            """
            <div class="hello1">
                <div class="foo">
                    <div class="hello2">
                        <div class="bar">
                            Hello, world!
                        </div>
                    </div>
                </div>
            </div>
            """,
        )

    def test_component_using_other_components(self):
        @component.register("header")
        def header(context):
            return Template(
                """
                <h1>
                    {% render_slot slots.inner_block %}
                </h1>
                """
            ).render(context)

        @component.register("hello")
        def dummy(context):
            context["title"] = context["attributes"].pop("title", "")
            return Template(
                """
                <div>
                    {% header %}
                        {{ title }}
                    {% endheader %}

                    <div>
                        {% render_slot slots.inner_block %}
                    </div>
                </div>
                """
            ).render(context)

        self.assertHTMLEqual(
            Template(
                """
                {% hello title="Some title" %}
                    Hello, world!
                {% endhello %}
                """
            ).render(Context({})),
            """
            <div>
                <h1>
                    Some title
                </h1>
                <div>
                    Hello, world!
                </div>
            </div>
            """,
        )

    # Settings

    def test_can_change_default_slot_name_from_settings(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>{% render_slot slots.default_slot %}</div>
                """
            ).render(context)

        with self.settings(
            WEB_COMPONENTS={
                "DEFAULT_SLOT_NAME": "default_slot",
            }
        ):
            self.assertHTMLEqual(
                Template(
                    """
                    {% hello %}Hello{% endhello %}
                    """
                ).render(Context({})),
                """
                <div>Hello</div>
                """,
            )


class RenderComponentTest(TestCase):
    def setUp(self) -> None:
        component.registry.clear()

    def test_renders_class_component(self):
        @component.register("test")
        class Dummy(component.Component):
            def render(self, context):
                return "foo"

        self.assertEqual(
            component.render_component(
                name="test",
                attributes=django_web_components.attributes.AttributeBag(),
                slots={},
                context=Context({}),
            ),
            "foo",
        )

    def test_passes_context_to_class_component(self):
        @component.register("test")
        class Dummy(component.Component):
            def get_context_data(self, **kwargs) -> dict:
                return {
                    "context_data": "value from get_context_data",
                }

            def render(self, context):
                return Template(
                    """
                    <div {{ attributes }}>
                        <div>{{ context_data }}</div>
                        {% render_slot slots.inner_block %}
                    </div>
                    """
                ).render(context)

        self.assertHTMLEqual(
            component.render_component(
                name="test",
                attributes=django_web_components.attributes.AttributeBag(
                    {
                        "class": "font-bold",
                    }
                ),
                slots={
                    "inner_block": SlotNodeList(
                        [
                            SlotNode(
                                name="",
                                unresolved_attributes={},
                                nodelist=NodeList(
                                    [
                                        TextNode("Hello, world!"),
                                    ]
                                ),
                            ),
                        ]
                    ),
                },
                context=Context({}),
            ),
            """
            <div class="font-bold">
                <div>value from get_context_data</div>
                Hello, world!
            </div>
            """,
        )

    def test_renders_function_component(self):
        @component.register("test")
        def dummy(context):
            return "foo"

        self.assertEqual(
            component.render_component(
                name="test",
                attributes=django_web_components.attributes.AttributeBag(),
                slots={},
                context=Context({}),
            ),
            "foo",
        )

    def test_passes_context_to_function_component(self):
        @component.register("test")
        def dummy(context):
            return Template(
                """
                <div {{ attributes }}>
                    {% render_slot slots.inner_block %}
                </div>
                """
            ).render(context)

        self.assertHTMLEqual(
            component.render_component(
                name="test",
                attributes=django_web_components.attributes.AttributeBag(
                    {
                        "class": "font-bold",
                    }
                ),
                slots={
                    "inner_block": SlotNodeList(
                        [
                            SlotNode(
                                name="",
                                unresolved_attributes={},
                                nodelist=NodeList(
                                    [
                                        TextNode("Hello, world!"),
                                    ]
                                ),
                            ),
                        ]
                    ),
                },
                context=Context({}),
            ),
            """
            <div class="font-bold">
                Hello, world!
            </div>
            """,
        )


class RegisterTest(TestCase):
    def setUp(self) -> None:
        component.registry.clear()

    def test_call_register_as_decorator(self):
        @component.register("hello")
        def dummy(context):
            pass

        self.assertEqual(
            component.registry.get("hello"),
            dummy,
        )

    def test_call_register_directly(self):
        def dummy(context):
            pass

        component.register("hello", dummy)

        self.assertEqual(
            component.registry.get("hello"),
            dummy,
        )
