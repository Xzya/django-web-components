from django.template import Template

template_cache = {}


class CachedTemplate:
    def __init__(self, template_string, origin=None, name=None, engine=None):
        self.template_string = template_string
        self.origin = origin
        self.name = name
        self.engine = engine

    def render(self, context):
        key = self.name

        if key in template_cache:
            return template_cache[key].render(context)

        template = Template(self.template_string, self.origin, self.name, self.engine)

        if key is not None:
            template_cache[key] = template

        return template.render(context)
