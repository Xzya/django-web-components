from typing import Dict, Any


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class ComponentRegistry:
    def __init__(self):
        self._registry: Dict[str, Any] = {}

    def register(self, name: str = None, component: Any = None):
        if name in self._registry:
            raise AlreadyRegistered('The component "%s" is already registered' % name)

        self._registry[name] = component

    def unregister(self, name):
        self.get(name)

        del self._registry[name]

    def get(self, name) -> Any:
        if name not in self._registry:
            raise NotRegistered('The component "%s" is not registered' % name)

        return self._registry[name]

    def all(self) -> Dict[str, Any]:
        return self._registry

    def clear(self):
        self._registry = {}
