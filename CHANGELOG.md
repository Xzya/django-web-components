# Changelog

## [Unreleased]
- Fixed `attributes_to_string` not ignoring attributes with `False` values, e.g. `attributes_to_string({"required": False})` will now return `""` instead of `"required"`

## [0.1.1] - 2023-02-26
- Allow registering components without providing a name (e.g. `@component.register()`). In this case, the name of the component's function or class will be used as the component name

## [0.1.0] - 2023-02-25

- Initial release
