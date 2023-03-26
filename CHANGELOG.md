# Changelog

## [Unreleased]

## [0.2.0] - 2023-03-27
- Updated the `django_web_components.attributes.merge_attributes` function to make it easier to work with attributes, especially classes
  - The signature was changed to accept a list of dicts
  - `merge_attributes` no longer appends attributes, instead, there is a separate `append_attributes` function for that now
  - The `class` attribute can now be provided as a string, list, or dict, and it will be normalized into a string. This can be useful for example for toggling classes based on a truthy value. This works similarly to [Vue's mergeProps](https://vuejs.org/api/render-function.html#mergeprops)

```python
active = context["attributes"].pop("active", False)

context["attributes"] = merge_attributes(
    {
        "type": "button",
        "class": [
            "btn",
            {
                "active": active,
            },
        ],
    },
    context["attributes"],
)
```

- Fixed `attributes_to_string` not ignoring attributes with `False` values, e.g. `attributes_to_string({"required": False})` will now return `""` instead of `"required"`

## [0.1.1] - 2023-02-26
- Allow registering components without providing a name (e.g. `@component.register()`). In this case, the name of the component's function or class will be used as the component name

## [0.1.0] - 2023-02-25

- Initial release
