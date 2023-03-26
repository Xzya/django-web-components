from django.test import TestCase
from django.utils.safestring import mark_safe, SafeString

from django_web_components.attributes import (
    AttributeBag,
    attributes_to_string,
    merge_attributes,
    split_attributes,
    normalize_class,
    append_attributes,
)


class AttributeBagTest(TestCase):
    def test_str_converts_to_string(self):
        self.assertEqual(
            str(AttributeBag({"foo": "bar"})),
            'foo="bar"',
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
            "",
        )

    def test_attribute_with_false_value(self):
        self.assertEqual(
            attributes_to_string({"required": False}),
            "",
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

    def test_overwrites_attributes(self):
        self.assertEqual(
            merge_attributes({"foo": "bar"}, {"foo": "baz", "data": "foo"}),
            {"foo": "baz", "data": "foo"},
        )

    def test_normalizes_classes(self):
        self.assertEqual(
            merge_attributes({"foo": "bar", "class": "baz"}, {"class": "qux"}),
            {"foo": "bar", "class": "baz qux"},
        )

    def test_merge_multiple_dicts(self):
        self.assertEqual(
            merge_attributes(
                {"foo": "bar"},
                {"class": "baz"},
                {"id": "qux"},
            ),
            {"foo": "bar", "class": "baz", "id": "qux"},
        )

    def test_returns_attribute_bag(self):
        result = merge_attributes(AttributeBag({"foo": "bar"}), {})
        self.assertTrue(type(result) == AttributeBag)


class SplitAttributesTest(TestCase):
    def test_returns_normal_attrs(self):
        self.assertEqual(split_attributes({"foo": "bar"}), ({}, {"foo": "bar"}))

    def test_returns_special_attrs(self):
        self.assertEqual(split_attributes({":let": "bar"}), ({":let": "bar"}, {}))

    def test_splits_attrs(self):
        self.assertEqual(split_attributes({":let": "fruit", "foo": "bar"}), ({":let": "fruit"}, {"foo": "bar"}))


class AppendAttributesTest(TestCase):
    def test_single_dict(self):
        self.assertEqual(
            append_attributes({"foo": "bar"}),
            {"foo": "bar"},
        )

    def test_appends_dicts(self):
        self.assertEqual(
            append_attributes({"class": "foo"}, {"id": "bar"}, {"class": "baz"}),
            {"class": "foo baz", "id": "bar"},
        )


class NormalizeClassTest(TestCase):
    def test_str(self):
        self.assertEqual(
            normalize_class("foo"),
            "foo",
        )

    def test_list(self):
        self.assertEqual(
            normalize_class(["foo", "bar"]),
            "foo bar",
        )

    def test_nested_list(self):
        self.assertEqual(
            normalize_class(["foo", ["bar", "baz"]]),
            "foo bar baz",
        )

    def test_tuple(self):
        self.assertEqual(
            normalize_class(("foo", "bar")),
            "foo bar",
        )

    def test_dict(self):
        self.assertEqual(
            normalize_class({"foo": True, "bar": False, "baz": None}),
            "foo",
        )

    def test_combined(self):
        self.assertEqual(
            normalize_class(
                [
                    "class1",
                    ["class2", "class3"],
                    {
                        "class4": True,
                        "class5": False,
                        "class6": "foo",
                    },
                ]
            ),
            "class1 class2 class3 class4 class6",
        )
