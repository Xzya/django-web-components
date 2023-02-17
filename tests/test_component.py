from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template, NodeList, Node
from django.template.base import TextNode
from django.test import TestCase
from django.utils.safestring import mark_safe, SafeString

from django_web_components import component
from django_web_components.component import (
    AttributeBag,
    Component,
    attributes_to_string,
    merge_attributes,
    ComponentTagFormatter,
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
                {
                    "message": "world",
                }
            ),
            """<div>Hello, world!</div>""",
        )


class AttributesToStringTest(TestCase):
    def test_simple_attribute(self):
        self.assertEqual(
            attributes_to_string({"foo": "bar"}),
            'foo="bar"',
        )

    def test_multiple_attributes(self):
        self.assertEqual(
            attributes_to_string({"class": "foo", "style": "color: red;"}),
            'class="foo" style="color: red;"',
        )

    def test_escapes_special_characters(self):
        self.assertEqual(
            attributes_to_string({"x-on:click": "bar", "@click": "'baz'"}),
            'x-on:click="bar" @click="&#x27;baz&#x27;"',
        )

    def test_does_not_escape_special_characters_if_safe_string(self):
        self.assertEqual(
            attributes_to_string({"foo": mark_safe("'bar'")}),
            "foo=\"'bar'\"",
        )

    def test_result_is_safe_string(self):
        result = attributes_to_string({"foo": mark_safe("'bar'")})
        self.assertTrue(type(result) == SafeString)

    def test_attribute_with_no_value(self):
        self.assertEqual(
            attributes_to_string({"required": None}),
            "required",
        )

    def test_attribute_with_true_value(self):
        self.assertEqual(
            attributes_to_string({"required": True}),
            "required",
        )


class MergeAttributesTest(TestCase):
    def test_merges_attributes(self):
        self.assertEqual(
            merge_attributes({"foo": "bar"}, {"bar": "baz"}),
            {"foo": "bar", "bar": "baz"},
        )

    def test_overwrites_defaults(self):
        self.assertEqual(
            merge_attributes({"foo": "bar"}, {"foo": "baz", "data": "foo"}),
            {"foo": "bar", "data": "foo"},
        )

    def test_appends_appendable_attributes_instead_of_overwriting(self):
        self.assertEqual(
            merge_attributes({"class": "foo"}, {"class": "bar"}),
            {"class": "bar foo"},
        )
        self.assertEqual(
            merge_attributes({"class": "foo"}, {}),
            {"class": "foo"},
        )
        self.assertEqual(
            merge_attributes({}, {"class": "foo"}),
            {"class": "foo"},
        )

    def test_appends_attributes(self):
        self.assertEqual(
            merge_attributes({"foo": "bar"}, {}, {"foo": "baz", "data": "foo"}),
            {"foo": "bar baz", "data": "foo"},
        )

    def test_returns_attribute_bag(self):
        result = merge_attributes(AttributeBag({"foo": "bar"}), {})
        self.assertTrue(type(result) == AttributeBag)


class AttributeBagTest(TestCase):
    def test_str_converts_to_string(self):
        self.assertEqual(
            str(AttributeBag({"foo": "bar"})),
            'foo="bar"',
        )


class ExampleComponentsTest(TestCase):
    def setUp(self) -> None:
        component.registry.clear()

    def test_component_with_inline_tag(self):
        @component.register("hello")
        def dummy(context):
            return Template("""<div>Hello, world!</div>""").render(Context(context))

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
            return Template("""<div {{ attributes }}>Hello, world!</div>""").render(Context(context))

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
            return Template("""<div>Hello, world!</div>""").render(Context(context))

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
            return Template("""<div>Hello, world!</div>""").render(Context(context))

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
            return Template("""<div>Hello, world!</div>""").render(Context(context))

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

    def test_component_with_attributes(self):
        @component.register("hello")
        def dummy(context):
            return Template("""<div {{ attributes }}>Hello, world!</div>""").render(Context(context))

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
            return Template("""<div {{ attributes }}>Hello, world!</div>""").render(Context(context))

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

    def test_component_with_default_slot(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>{% render_slot slots.inner_block %}</div>
                """
            ).render(Context(context))

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

    def test_component_with_slot(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>
                    <h1>{% render_slot slots.title %}</h1>
                </div>
                """
            ).render(Context(context))

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}
                    {% slot title %}Lorem ipsum{% endslot title %}
                {% endhello %}
                """
            ).render(Context({})),
            """
            <div>
                <h1>Lorem ipsum</h1>
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
            ).render(Context(context))

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
            ).render(Context(context))

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
            ).render(Context(context))

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
            ).render(Context(context))

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
            ).render(Context(context))

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

    def test_attributes_from_context_variables(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div {{ attributes }}>
                    {% render_slot slots.inner_block %}
                </div>
                """
            ).render(Context(context))

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

    def test_component_with_context_passed_in(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>{{ message }}</div>
                """
            ).render(Context(context))

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

    def test_attributes_with_defaults(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div {% merge_attrs attributes class="font-bold" @click="foo" %}></div>
                """
            ).render(Context(context))

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

    def test_nested_component(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div {{ attributes }}>{% render_slot slots.inner_block %}</div>
                """
            ).render(Context(context))

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
            ).render(Context(context))

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
            ).render(Context(context))

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
            ).render(Context(context))

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

    def test_can_change_default_slot_name_from_settings(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>{% render_slot slots.default_slot %}</div>
                """
            ).render(Context(context))

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
                "DEFAULT_COMPONENT_TAG_FORMATTER": "tests.test_component.CustomComponentTagFormatter",
            },
        ):

            @component.register("hello")
            def dummy(context):
                return Template("""<div>{% render_slot slots.inner_block %}</div>""").render(Context(context))

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
                "DEFAULT_COMPONENT_TAG_FORMATTER": "tests.test_component.CustomComponentTagFormatter",
            },
        ):

            @component.register("hello")
            def dummy(context):
                return Template("""<div>Hello, world!</div>""").render(Context(context))

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


class RegisterTest(TestCase):
    def setUp(self) -> None:
        component.registry.clear()

    def test_register_decorator(self):
        @component.register("hello")
        def dummy(context):
            pass

        self.assertEqual(
            component.registry.get("hello"),
            dummy,
        )


class RenderSlotTest(TestCase):
    def setUp(self) -> None:
        component.registry.clear()

    def test_can_render_default_slot(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>{% render_slot slots.inner_block %}</div>
                """
            ).render(Context(context))

        self.assertHTMLEqual(
            Template(
                """
                {% hello %}Foo{% endhello %}
                """
            ).render(Context({})),
            """
            <div>Foo</div>
            """,
        )

    def test_can_render_custom_slot(self):
        @component.register("hello")
        def dummy(context):
            return Template(
                """
                <div>
                    <div>{% render_slot slots.title %}</div>
                    <div>{% render_slot slots.inner_block %}</div>
                </div>
                """
            ).render(Context(context))

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

    def test_can_render_scoped_slots(self):
        # TODO: fix
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
            ).render(Context(context))

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

        # using 'let' to define the context variable
        self.assertHTMLEqual(
            Template(
                """
                {% table %}
                    {% slot column let="user" label="Name" %}
                        {{ user.name }}
                    {% endslot %}
                    {% slot column let="user" label="Age" %}
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


class SlotNodeListTest(TestCase):
    def test_attributes_returns_empty_if_no_elements(self):
        self.assertEqual(
            SlotNodeList().attributes,
            AttributeBag(),
        )

    def test_attributes_returns_empty_if_element_doesnt_have_attributes_property(self):
        self.assertEqual(
            SlotNodeList([TextNode("hello")]).attributes,
            AttributeBag(),
        )

    def test_attributes_returns_attributes_of_first_element(self):
        node = Node()
        node.attributes = {"foo": "bar"}

        self.assertEqual(
            SlotNodeList([node]).attributes,
            {"foo": "bar"},
        )

    def test_attributes_returns_empty_if_multiple_elements(self):
        node1 = Node()
        node1.attributes = {"foo": "bar"}
        node2 = Node()
        node2.attributes = {"foo": "bar"}

        self.assertEqual(
            SlotNodeList([node1, node2]).attributes,
            {},
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
                attributes=component.AttributeBag(),
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
                attributes=component.AttributeBag(
                    {
                        "class": "font-bold",
                    }
                ),
                slots={
                    "inner_block": SlotNodeList(
                        [
                            SlotNode(
                                name="",
                                attributes={},
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
                attributes=component.AttributeBag(),
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
                attributes=component.AttributeBag(
                    {
                        "class": "font-bold",
                    }
                ),
                slots={
                    "inner_block": SlotNodeList(
                        [
                            SlotNode(
                                name="",
                                attributes={},
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
