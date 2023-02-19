# django-web-components

A simple way to create reusable template components in Django.

## Example component

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
  {% slot header %}Featured{% endslot %}
  {% slot title %}Card title{% endslot %}

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

@component.register("card")
class CardComponent(component.Component):
    # You may also override the get_template_name() method instead
    template_name = "components/card.html"

    # Extra context data will be passed to the template
    def get_context_data(self, **kwargs) -> dict:
      context = super().get_context_data(**kwargs)
      context["open"] = True
      return context
```

The component will be rendered by calling the `render(context)` method, which by default will load the template file and render it.

For tiny components, it may feel cumbersome to manage both the component class and the component's template. For this reason, you may define the template directly from the `render` method:

```python
from django_web_components import component
from django.template import Template

@component.register("card")
class CardComponent(component.Component):
    def render(self, context) -> str:
        return Template(
            """
            <div class="card">
                {% render_slot slots.inner_block %}
            </div>
            """
        ).render(context)
```

### Function based components

A component may also be defined as a single function that accepts a `context` and returns a string:

```python
from django_web_components import component
from django.template import Template

@component.register("card")
def card(context):
    return Template(
        """
        <div class="card">
            {% render_slot slots.inner_block %}
        </div>
        """
    ).render(context)
```

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
        component.register("card")(components.CardComponent)
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

# inside your settings[component.py](django_web_components%2Fcomponent.py)
WEB_COMPONENTS = {
    "DEFAULT_COMPONENT_TAG_FORMATTER": "path.to.your.ComponentTagFormatter",
}
```

## Passing data to components

You may pass data to components using keyword arguments, which accept either hardcoded values or variables:

```html
{% with message="Something bad happened!" %}
    {% #alert type="error" message=message %}
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

You may also render all attributes directly using `{{ attributes }}`, for example, if you have the following component

```html
{% alert id="alerts" class="font-bold" %} ... {% endalert %}
```

You may render all attributes using

```html
<div {{ attributes }}">
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
{% alert id="alerts" dismissible=True %} Something went wrong! {% endalert %}
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

To achieve this, you can manipulate the context from your component in order to provide a better API. There are several ways to do this, choose the method that makes the most sense to you, for example:

- You can override `get_context_data` and remove the `dismissible` attribute from `attributes` and return it in the context instead

```python
from django_web_components import component

@component.register("alert")
class Alert(component.Component):
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
    def render(self, context):
        context["dismissible"] = context["attributes"].pop("dismissible", False)

        return super().render(context)
```

Both the above solutions will work, and you can do the same for function based components. The component's template can then look like this:

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

### Named slots

### Slot attributes

### Duplicate named slots

### Scoped slots
