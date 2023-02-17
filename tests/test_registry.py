from django.test import TestCase

from django_web_components.registry import (
    ComponentRegistry,
    AlreadyRegistered,
    NotRegistered,
)


class ComponentRegistryTest(TestCase):
    def test_register(self):
        registry = ComponentRegistry()

        def dummy(context):
            pass

        registry.register("hello", dummy)

        self.assertEqual(
            registry.get("hello"),
            dummy,
        )

    def test_register_raises_if_component_already_registered(self):
        registry = ComponentRegistry()

        def dummy(context):
            pass

        registry.register("hello", dummy)

        with self.assertRaises(AlreadyRegistered):
            registry.register("hello", dummy)

    def test_get_raises_if_component_not_registered(self):
        registry = ComponentRegistry()

        with self.assertRaises(NotRegistered):
            registry.get("hello")

    def test_unregister(self):
        registry = ComponentRegistry()

        def dummy(context):
            pass

        registry.register("hello", dummy)

        self.assertEqual(
            registry.get("hello"),
            dummy,
        )

        registry.unregister("hello")

        with self.assertRaises(NotRegistered):
            registry.get("hello")

    def test_clear(self):
        registry = ComponentRegistry()

        def dummy(context):
            pass

        registry.register("hello", dummy)

        self.assertEqual(
            registry.get("hello"),
            dummy,
        )

        registry.clear()

        with self.assertRaises(NotRegistered):
            registry.get("hello")
