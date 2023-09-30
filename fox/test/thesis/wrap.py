from __future__ import annotations
from typing import Any


import inspect
import types

from . import dsl


__all__ = ("Wrapper", "Wrap")


class Wrapper:
    """Wraps an object or a module."""

    _wrap = None
    """Containing Interface."""

    def __init__(self, _wrap: Wrap, **kwargs):
        self._wrap = _wrap
        self.__dict__.update(kwargs)

    def __call__(self, *args, **kwargs):
        return self._wrap.call("__call__", *args, **kwargs)

    def __getattr__(self, attr):
        return self._wrap.getattr(attr)

    def __str__(self):
        wrap = self._wrap.__str__()
        return f"{wrap}::{self._wrap.target}"

    def __enter__(self, *args, **kwargs) -> Any:
        return self._wrap.call("__enter__", *args, **kwargs)

    def __exit__(self, *args, **kwargs):
        return self._wrap.call("__exit__", *args, **kwargs)


class NodeMixin:
    @property
    def parent(self) -> NodeMixin | None:
        return getattr(self, "_parent", None)

    @parent.setter
    def parent(self, parent: NodeMixin):
        self.set_parent(parent)

    def set_parent(self, parent: NodeMixin):
        if self.parent:
            self.parent._imeta.remove_child(self)
        self.parent = parent
        if parent:
            parent.add_child(self)

    def add_child(self, child: NodeMixin):
        """Add children interface to this one."""
        if not self.children:
            self.children = [child]
        else:
            self.children.append(child)

    def remove_child(self, child: NodeMixin):
        """Remove child interface."""
        if self.children and child in self.children:
            self.children.remove(child)


class Wrap(NodeMixin, dsl.Unit):
    """Interface wraps a target in order to redirect attribute get or calls and
    keep track of them.

    .. code-block :: python

        wrap = Wrap(target, a="attribute a")
        wrapped = wrap._
        assert wrapped.a == "attribute a"
        assert wrapped.foo(1, a=13) == "foo"
        assert wrapped.bar() == "bar"
    """

    _: Wrapper = None
    parent = None
    target = None

    instance_class = None

    def __init__(
        self,
        target: Any = None,
        parent: Wrap = None,
        key: str | None = None,
        **wrap_kwargs,
    ):
        self.target = target
        self.parent = parent
        self._ = Wrapper(self, **wrap_kwargs)
        if not key:
            key = type(self).__name__ + f".{target}"
        super().__init__(key=key)

    def call(self, name: str, args: list[Any], kwargs: dict[str, Any]):
        match name:
            case "__call__" if inspect.isclass(self.target):
                target = self.target(*args, **kwargs)
                return self.instance_class(target=target, parent=self)._
            case "__call__":
                return target(*args, **kwargs)
            case _:
                return getattr(target, name)(*args, **kwargs)

    def getattr(self, name: str) -> Any:
        if not self.target:
            raise ValueError("No target is set on Interface.")

        attr = getattr(self.target, name)
        if isinstance(attr, types.MethodType):
            # Redirect call of target methods through imeta.
            return lambda *args, **kwargs: self.call(name, args, kwargs)
        return attr

    def clone(self, *args, **kwargs) -> Wrap:
        """Return a clone of self with:

        - a new wrapper
        - and new trace watching same calls
        """
        clone = super().clone(*args, **kwargs)
        clone._._interface = clone
        return clone


Wrap.instance_class = Wrap
