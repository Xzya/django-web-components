# django-web-components

[![Tests](https://github.com/Xzya/django-web-components/actions/workflows/tests.yml/badge.svg)](https://github.com/Xzya/django-web-components/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/django-web-components)](https://pypi.org/project/django-web-components/)

A simple way to create reusable template components in Django.

## Example

You have to first register your component

```python
from django_web_components import component

@component.register("card")
class Card(component.Component):
    template_name = "components/card.html"
```

The component's template:

```html
# components/card.html

{% load components %}

<div class="card">
    <div class="card-header">
        {% render_slot slots.header %}
    </div>
    <div class="card-body">
        <h5 class="card-title">
            {% render_slot slots.title %}
        </h5>

        {% render_slot slots.inner_block %}
    </div>
</div>
```

You can now render this component with:

```html
{% load components %}

{% card %}
  {% slot header %} Featured {% endslot %}
  {% slot title %} Card title {% endslot %}

  <p>Some quick example text to build on the card title and make up the bulk of the card's content.</p>

  <a href="#" class="btn btn-primary">Go somewhere</a>
{% endcard %}
```

Which will result in the following HTML being rendered:

```html
<div class="card">
    <div class="card-header">
        Featured
    </div>
    <div class="card-body">
        <h5 class="card-title">
            Card title
        </h5>

        <p>Some quick example text to build on the card title and make up the bulk of the card's content.</p>

        <a href="#" class="btn btn-primary">Go somewhere</a>
    </div>
</div>
```

## Installation

```
pip install django-web-components
```

Then add `django_web_components` to your `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    ...,
    "django_web_components",
]
```

### Optional

To avoid having to use `{% load components %}` in each template, you may add the tags to the `builtins` list inside your
settings.

```python
TEMPLATES = [
    {
        ...,
        "OPTIONS": {
            "context_processors": [
                ...
            ],
            "builtins": [
                "django_web_components.templatetags.components",
            ],
        },
    },
]
```

## Python / Django compatibility

The library supports Python 3.8+ and Django 3.2+.

| Python version | Django version      |
|----------------|---------------------|
| `3.11`         | `4.1`               |
| `3.10`         | `4.1`, `4.0`, `3.2` |
| `3.9`          | `4.1`, `4.0`, `3.2` |
| `3.8`          | `4.1`, `4.0`, `3.2` |

## Components

There are two approaches to writing components: class based components and function based components.

### Class based components

```python
from django_web_components import component

@component.register("alert")
class Alert(component.Component):
    # You may also override the get_template_name() method instead
    template_name = "components/alert.html"

    # Extra context data will be passed to the template context
    def get_context_data(self, **kwargs) -> dict:
        return {
            "dismissible": False,
        }
```

The component will be rendered by calling the `render(context)` method, which by default will load the template file and render it.

For tiny components, it may feel cumbersome to manage both the component class and the component's template. For this reason, you may define the template directly from the `render` method:

```python
from django_web_components import component
from django_web_components.template import CachedTemplate

@component.register("alert")
class Alert(component.Component):
    def render(self, context) -> str:
        return CachedTemplate(
            """
            <div class="alert alert-primary" role="alert">
                {% render_slot slots.inner_block %}
            </div>
            """,
            name="alert",
        ).render(context)
```

### Function based components

A component may also be defined as a single function that accepts a `context` and returns a string:

```python
from django_web_components import component
from django_web_components.template import CachedTemplate

@component.register
def alert(context):
    return CachedTemplate(
        """
        <div class="alert alert-primary" role="alert">
            {% render_slot slots.inner_block %}
        </div>
        """,
        name="alert",
    ).render(context)
```

The examples in this guide will mostly use function based components, since it's easier to exemplify as the component code and template are in the same place, but you are free to choose whichever method you prefer.

### Template files vs template strings

The library uses the regular Django templates, which allows you to either [load templates from files](https://docs.djangoproject.com/en/dev/ref/templates/api/#loading-templates), or create [Template objects](https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.Template) directly using template strings. Both methods are supported, and both have advantages and disadvantages:

- Template files
  - You get formatting support and syntax highlighting from your editor
  - You get [caching](https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader) by default
  - Harder to manage / reason about since your code is split from the template
- Template strings
  - Easier to manage / reason about since your component's code and template are in the same place
  - You lose formatting support and syntax highlighting since the template is just a string
  - You lose caching

Regarding caching, the library provides a `CachedTemplate`, which will cache and reuse the `Template` object as long as you provide a `name` for it, which will be used as the cache key:

```python
from django_web_components import component
from django_web_components.template import CachedTemplate

@component.register
def alert(context):
    return CachedTemplate(
        """
        <div class="alert alert-primary" role="alert">
            {% render_slot slots.inner_block %}
        </div>
        """,
        name="alert",
    ).render(context)
```

So in reality, the caching should not be an issue when using template strings, since `CachedTemplate` is just as fast as using the cached loader with template files.

Regarding formatting support and syntax highlighting, there is no good solution for template strings. PyCharm supports [language injection](https://www.jetbrains.com/help/pycharm/using-language-injections.html#use-language-injection-comments) which allows you to add a `# language=html` comment before the template string and get syntax highlighting, however, it only highlights HTML and not the Django tags, and you are still missing support for formatting. Maybe the editors will add better support for this in the future, but for the moment you will be missing syntax highlighting and formatting if you go this route. There is an [open conversation](https://github.com/EmilStenstrom/django-components/issues/183) about this on the `django-components` repo, credits to [EmilStenstrom](https://github.com/EmilStenstrom) for moving the conversation forward with the VSCode team.

In the end, it's a tradeoff. Use the method that makes the most sense for you.

## Registering your components

[Just like signals](https://docs.djangoproject.com/en/dev/topics/signals/#connecting-receiver-functions), the components can live anywhere, but you need to make sure Django picks them up on startup. The easiest way to do this is to define your components in a `components.py` submodule of the application they relate to, and then connect them inside the `ready()` method of your application configuration class.

```python
from django.apps import AppConfig
from django_web_components import component

class MyAppConfig(AppConfig):
    ...

    def ready(self):
        # Implicitly register components decorated with @component.register
        from . import components  # noqa
        # OR explicitly register a component
        component.register("card", components.Card)
```

You may also `unregister` an existing component, or get a component from the registry:

```python
from django_web_components import component
# Unregister a component
component.registry.unregister("card")
# Get a component
component.registry.get("card")
# Remove all components
component.registry.clear()
# Get all components as a dict of name: component
component.registry.all()
```

## Rendering components

Each registered component will have two tags available for use in your templates:

- A block tag, e.g. `{% card %} ... {% endcard %}`
- An inline tag, e.g. `{% #user_profile %}`. This can be useful for components that don't necessarily require a body

### Component tag formatter

By default, components will be registered using the following tags:

- Block start tag: `{% <component_name> %}`
- Block end tag: `{% end<component_name> %}`
- Inline tag: `{% #<component_name> %}`

This behavior may be changed by providing a custom tag formatter in your settings. For example, to change the block tags to `{% #card %} ... {% /card %}`, and the inline tag to `{% card %}` (similar to [slippers](https://github.com/mixxorz/slippers)), you can use the following formatter:

```python
class ComponentTagFormatter:
    def format_block_start_tag(self, name):
        return f"#{name}"

    def format_block_end_tag(self, name):
        return f"/{name}"

    def format_inline_tag(self, name):
        return name

# inside your settings
WEB_COMPONENTS = {
    "DEFAULT_COMPONENT_TAG_FORMATTER": "path.to.your.ComponentTagFormatter",
}
```

## Passing data to components

You may pass data to components using keyword arguments, which accept either hardcoded values or variables:

```html
{% with error_message="Something bad happened!" %}
    {% #alert type="error" message=error_message %}
{% endwith %}
```

All attributes will be added in an `attributes` dict which will be available in the template context:

```json
{
    "attributes": {
        "type": "error",
        "message": "Something bad happened!"
    }
}
```

You can then access it from your component's template:

```html
<div class="alert alert-{{ attributes.type }}">
    {{ attributes.message }}
</div>
```

### Rendering all attributes

You may also render all attributes directly using `{{ attributes }}`. For example, if you have the following component

```html
{% alert id="alerts" class="font-bold" %} ... {% endalert %}
```

You may render all attributes using

```html
<div {{ attributes }}>
    <!-- Component content -->
</div>
```

Which will result in the following HTML being rendered:

```html
<div id="alerts" class="font-bold">
    <!-- Component content -->
</div>
```

### Attributes with special characters

You can also pass attributes with special characters (`[@:_-.]`), as well as attributes with no value:

```html
{% button @click="handleClick" data-id="123" required %} ... {% endbutton %}
```

Which will result in the follow dict available in the context:

```python
{
    "attributes": {
        "@click": "handleClick",
        "data-id": "123",
        "required": True,
    }
}
```

And will be rendered by `{{ attributes }}` as `@click="handleClick" data-id="123" required`.

### Default / merged attributes

Sometimes you may need to specify default values for attributes, or merge additional values into some of the component's attributes. The library provides a `merge_attrs` tag that helps with this:

```html
<div {% merge_attrs attributes class="alert" role="alert" %}>
    <!-- Component content -->
</div>
```

If we assume this component is utilized like so:

```html
{% alert class="mb-4" %} ... {% endalert %}
```

The final rendered HTML of the component will appear like the following:

```html
<div class="alert mb-4" role="alert">
    <!-- Component content -->
</div>
```

### Non-class attribute merging

When merging attributes that are not `class` attributes, the values provided to the `merge_attrs` tag will be considered the "default" values of the attribute. However, unlike the `class` attribute, these attributes will not be merged with injected attribute values. Instead, they will be overwritten. For example, a `button` component's implementation may look like the following:

```html
<button {% merge_attrs attributes type="button" %}>
    {% render_slot slots.inner_block %}
</button>
```

To render the button component with a custom `type`, it may be specified when consuming the component. If no type is specified, the `button` type will be used:

```html
{% button type="submit" %} Submit {% endbutton %}
```

The rendered HTML of the `button` component in this example would be:

```html
<button type="submit">
    Submit
</button>
```

### Appendable attributes

You may also treat other attributes as "appendable" by using the `+=` operator:

```html
<div {% merge_attrs attributes data-value+="some-value" %}>
    <!-- Component content -->
</div>
```

If we assume this component is utilized like so:

```html
{% alert data-value="foo" %} ... {% endalert %}
```

The rendered HTML will be:

```html
<div data-value="foo some-value">
    <!-- Component content -->
</div>
```

### Manipulating the attributes

By default, all attributes are added to an `attributes` dict inside the context. However, this may not always be what we want. For example, imagine we want to have an `alert` component that can be dismissed, while at the same time being able to pass extra attributes to the root element, like an `id` or `class`. Ideally we would want to be able to render a component like this:

```html
{% alert id="alerts" dismissible %} Something went wrong! {% endalert %}
```

A naive way to implement this component would be something like the following:

```html
<div {{ attributes }}>
    {% render_slot slots.inner_block %}

    {% if attributes.dismissible %}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    {% endif %}
</div>
```

However, this would result in the `dismissible` attribute being included in the root element, which is not what we want:

```html
<div id="alerts" dismissible>
    Something went wrong!

    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
```

Ideally we would want the `dismissible` attribute to be separated from the `attributes` since we only want to use it in logic, but not necessarily render it to the component.

To achieve this, you can manipulate the context from your component in order to provide a better API for using the components. There are several ways to do this, choose the method that makes the most sense to you, for example:

- You can override `get_context_data` and remove the `dismissible` attribute from `attributes` and return it in the context instead

```python
from django_web_components import component

@component.register("alert")
class Alert(component.Component):
    template_name = "components/alert.html"

    def get_context_data(self, **kwargs):
        dismissible = self.attributes.pop("dismissible", False)

        return {
            "dismissible": dismissible,
        }
```

- You can override the `render` method and manipulate the context there

```python
from django_web_components import component

@component.register("alert")
class Alert(component.Component):
    template_name = "components/alert.html"

    def render(self, context):
        context["dismissible"] = context["attributes"].pop("dismissible", False)

        return super().render(context)
```

Both of the above solutions will work, and you can do the same for function based components. The component's template can then look like this:

```html
<div {{ attributes }}>
    {% render_slot slots.inner_block %}

    {% if dismissible %}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    {% endif %}
</div>
```

Which should result in the correct HTML being rendered:

```html
<div id="alerts">
    Something went wrong!

    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
```

## Slots

You will often need to pass additional content to your components via "slots". A `slots` context variable is passed to your components, which consists of a dict with the slot name as the key and the slot as the value. You may then render the slots inside your components using the `render_slot` tag.

### The default slot

To explore this concept, let's imagine we want to pass some content to an `alert` component:

```html
{% alert %}
    <strong>Whoops!</strong> Something went wrong!
{% endalert %}
```

By default, that content will be made available to your component in the default slot which is called `inner_block`. You can then render this slot using the `render_slot` tag inside your component:

```html
{% load components %}
<div class="alert alert-danger">
    {% render_slot slots.inner_block %}
</div>
```

Which should result in the following HTML being rendered:

```html
<div class="alert alert-danger">
    <strong>Whoops!</strong> Something went wrong!
</div>
```

---

You may also rename the default slot by specifying it in your settings:

```python
# inside your settings
WEB_COMPONENTS = {
    "DEFAULT_SLOT_NAME": "inner_block",
}
```

### Named slots

Sometimes a component may need to render multiple different slots in different locations within the component. Let's modify our alert component to allow for the injection of a "title" slot:

```html
{% load components %}
<div class="alert alert-danger">
    <span class="alert-title">
        {% render_slot slots.title %}
    </span>

    {% render_slot slots.inner_block %}
</div>
```

You may define the content of the named slot using the `slot` tag. Any content not within an explicit `slot` tag will be added to the default `inner_block` slot:

```html
{% load components %}
{% alert %}
    {% slot title %} Server error {% endslot %}

    <strong>Whoops!</strong> Something went wrong!
{% endalert %}
```

The rendered HTML in this example would be:

```html
<div class="alert alert-danger">
    <span class="alert-title">
        Server error
    </span>

    <strong>Whoops!</strong> Something went wrong!
</div>
```

### Duplicate named slots

You may define the same named slot multiple times:

```html
{% unordered_list %}
  {% slot item %} First item {% endslot %}
  {% slot item %} Second item {% endslot %}
  {% slot item %} Third item {% endslot %}
{% endunordered_list %}
```

You can then iterate over the slot inside your component:

```html
<ul>
    {% for item in slots.item %}
        <li>{% render_slot item %}</li>
    {% endfor %}
</ul>
```

Which will result in the following HTML:

```html
<ul>
    <li>First item</li>
    <li>Second item</li>
    <li>Third item</li>
</ul>
```

### Scoped slots

The slot content will also have access to the component's context. To explore this concept, imagine a list component that accepts an `entries` attribute representing a list of things, which it will then iterate over and render the `inner_block` slot for each entry.

```python
from django_web_components import component
from django_web_components.template import CachedTemplate

@component.register
def unordered_list(context):
    context["entries"] = context["attributes"].pop("entries", [])

    return CachedTemplate(
        """
        <ul>
            {% for entry in entries %}
                <li>
                    {% render_slot slots.inner_block %}
                </li>
            {% endfor %}
        </ul>
        """,
        name="unordered_list",
    ).render(context)
```

We can then render the component as follows:

```html
{% unordered_list entries=entries %}
    I like {{ entry }}!
{% endunordered_list %}
```

In this example, the `entry` variable comes from the component's context. If we assume that `entries = ["apples", "bananas", "cherries"]`, the resulting HTML will be:

```html
<ul>
    <li>I like apples!</li>
    <li>I like bananas!</li>
    <li>I like cherries!</li>
</ul>
```

---

You may also explicitly pass a second argument to `render_slot`:

```html
<ul>
    {% for entry in entries %}
        <li>
            <!-- We are passing the `entry` as the second argument to render_slot -->
            {% render_slot slots.inner_block entry %}
        </li>
    {% endfor %}
</ul>
```

When invoking the component, you can use the special attribute `:let` to take the value that was passed to `render_slot` and bind it to a variable:

```html
{% unordered_list :let="fruit" entries=entries %}
    I like {{ fruit }}!
{% endunordered_list %}
```

This would render the same HTML as above.

### Slot attributes

Similar to the components, you may assign additional attributes to slots. Below is a table component illustrating multiple named slots with attributes:

```python
from django_web_components import component
from django_web_components.template import CachedTemplate

@component.register
def table(context):
    context["rows"] = context["attributes"].pop("rows", [])

    return CachedTemplate(
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
        """,
        name="table",
    ).render(context)
```

You can invoke the component like so:

```html
{% table rows=rows %}
    {% slot column :let="user" label="Name" %}
        {{ user.name }}
    {% endslot %}
    {% slot column :let="user" label="Age" %}
        {{ user.age }}
    {% endslot %}
{% endtable %}
```

If we assume that `rows = [{ "name": "Jane", "age": "34" }, { "name": "Bob", "age": "51" }]`, the following HTML will be rendered:

```html
<table>
    <tr>
        <th>Name</th>
        <th>Age</th>
    </tr>
    <tr>
        <td>Jane</td>
        <td>34</td>
    </tr>
    <tr>
        <td>Bob</td>
        <td>51</td>
    </tr>
</table>
```

### Nested components

You may also nest components to achieve more complicated elements. Here is an example of how you might implement an [Accordion component using Bootstrap](https://getbootstrap.com/docs/5.3/components/accordion/):

```python
from django_web_components import component
from django_web_components.template import CachedTemplate
import uuid

@component.register
def accordion(context):
    context["accordion_id"] = context["attributes"].pop("id", str(uuid.uuid4()))
    context["always_open"] = context["attributes"].pop("always_open", False)

    return CachedTemplate(
        """
        <div class="accordion" id="{{ accordion_id }}">
            {% render_slot slots.inner_block %}
        </div>
        """,
        name="accordion",
    ).render(context)


@component.register
def accordion_item(context):
    context["id"] = context["attributes"].pop("id", str(uuid.uuid4()))
    context["open"] = context["attributes"].pop("open", False)

    return CachedTemplate(
        """
        <div class="accordion-item" id="{{ id }}">
            <h2 class="accordion-header" id="{{ id }}-header">
                <button
                    class="accordion-button {% if not open %}collapsed{% endif %}"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#{{ id }}-collapse"
                    aria-expanded="{% if open %}true{% else %}false{% endif %}"
                    aria-controls="{{ id }}-collapse"
                >
                    {% render_slot slots.title %}
                </button>
            </h2>
            <div
                id="{{ id }}-collapse"
                class="accordion-collapse collapse {% if open %}show{% endif %}"
                aria-labelledby="{{ id }}-header"
                {% if accordion_id and not always_open %}
                    data-bs-parent="#{{ accordion_id }}"
                {% endif %}}
            >
                <div class="accordion-body">
                    {% render_slot slots.body %}
                </div>
            </div>
        </div>
        """,
        name="accordion_item",
    ).render(context)
```

You can then use them as follows:

```html
{% accordion %}

    {% accordion_item open %}
        {% slot title %} Accordion Item #1 {% endslot %}
        {% slot body %}
            <strong>This is the first item's accordion body.</strong> It is shown by default.
        {% endslot %}
    {% endaccordion_item %}

    {% accordion_item %}
        {% slot title %} Accordion Item #2 {% endslot %}
        {% slot body %}
            <strong>This is the second item's accordion body.</strong> It is hidden by default.
        {% endslot %}
    {% endaccordion_item %}

    {% accordion_item %}
        {% slot title %} Accordion Item #3 {% endslot %}
        {% slot body %}
            <strong>This is the third item's accordion body.</strong> It is hidden by default.
        {% endslot %}
    {% endaccordion_item %}

{% endaccordion %}
```

## Setup for development and running the tests

The project uses `poetry` to manage the dependencies. Check out the documentation on how to install poetry here: https://python-poetry.org/docs/#installation

Install the dependencies

```bash
poetry install
```

Activate the environment

```bash
poetry shell
```

Now you can run the tests

```bash
python runtests.py
```

## Motivation / Inspiration / Resources

The project came to be after seeing how other languages / frameworks deal with components, and wanting to bring some of those ideas back to Django.

- [django-components](https://github.com/EmilStenstrom/django-components) - The existing `django-components` library is already great and supports most of the features that this project has, but I thought the syntax could be improved a bit to feel less verbose, and add a few extra things that seemed necessary, like support for function based components and template strings, and working with attributes
- [Phoenix Components](https://hexdocs.pm/phoenix_live_view/Phoenix.Component.html) - I really liked the simplicity of Phoenix and how they deal with components, and this project is heavily inspired by it. In fact, some of the examples above are straight-up copied from there (like the table example).
- [Laravel Blade Components](https://laravel.com/docs/9.x/blade#components) - The initial implementation was actually very different and was relying on HTML parsing to turn the HTML into template Nodes, and was heavily inspired by Laravel. This had the benefit of having a nicer syntax (e.g. rendering the components looked a lot like normal HTML `<x-alert type="error">Server Error</x-alert>`), but the solution was a lot more complicated and I came to the conclusion that using a similar approach to `django-components` made a lot more sense in Django
- [Vue Components](https://vuejs.org/guide/essentials/component-basics.html)
- [slippers](https://github.com/mixxorz/slippers)
- [django-widget-tweaks](https://github.com/jazzband/django-widget-tweaks)
- [How EEx Turns Your Template Into HTML](https://www.mitchellhanberg.com/how-eex-turns-your-template-into-html/)

### Component libraries

Many other languages / frameworks are using the same concepts for building components (slots, attributes), so a lot of the knowledge is transferable, and there is already a great deal of existing component libraries out there (e.g. using Bootstrap, Tailwind, Material design, etc.). I highly recommend looking at some of them to get inspired on how to build / structure your components. Here are some examples:

- https://bootstrap-vue.org/docs/components/alert
- https://coreui.io/bootstrap-vue/components/alert.html
- https://laravel-bootstrap-components.com/components/alerts
- https://flowbite.com/docs/components/alerts/
- https://www.creative-tim.com/vuematerial/components/button
- https://phoenix-ui.fly.dev/components/alert
- https://storybook.phenixgroupe.com/components/message
- https://surface-ui.org/samplecomponents/Button
- https://react-bootstrap.github.io/components/alerts/
