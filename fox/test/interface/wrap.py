import inspect
import types

from . import dsl


__all__ = ("Wrapper", "Wrap")


class Wrapper:
    """Wraps an object or a module."""

    _interface = None
    """Containing Interface."""

    def __init__(self, _interface, **kwargs):
        self._interface = _interface
        self.__dict__.update(kwargs)

    def __call__(self, *args, **kwargs):
        return self._interface.call("__call__", *args, **kwargs)

    def __getattr__(self, attr):
        return self._interface.getattr(attr)

    def __str__(self):
        interface = super().__str__()
        return f"{interface}::{self._interface.target}"

    def __enter__(self, *args, **kwargs):
        return self._interface.target.__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        return self._interface.target.__exit__(*args, **kwargs)


class NodeMixin:
    @property
    def parent(self):
        return getattr(self, "_parent", None)

    @parent.setter
    def parent(self, parent):
        self.set_parent(parent)

    def set_parent(self, parent):
        if self.parent:
            self.parent._imeta.remove_child(self)
        self.parent = parent
        if parent:
            parent.add_child(self)

    def add_child(self, child):
        """Add children interface to this one."""
        if not self.children:
            self.children = [child]
        else:
            self.children.append(child)

    def remove_child(self, child):
        """Remove child interface."""
        if self.children and child in self.children:
            self.children.remove(child)


class Wrap(NodeMixin, dsl.Unit):
    """Interface wraps a target in order to redirect attribute get or calls and
    keep track of them.

    .. code-block :: python

        iface = (
            Interface(target, a="attribute a")
                << Asume(foo="foo", bar="bar")
                << Trace("foo")
        )

        obj = iface._
        assert obj.a == "attribute a"
        assert obj.foo(1, a=13) == "foo"
        assert obj.bar() == "bar"

        assert Trace("foo", [1]) in iface
        assert Trace("foo", [1], {"a": 13}) in iface
        assert Trace("foo", [2]) not in iface

        iface = iface & Assume(foo="not foo")
        obj = iface._
        assert obj.a == "attribute a"
        assert obj.foo() == "not foo"
        assert obj.bar() == "bar"
    """

    _: Wrapper = None
    parent = None
    target = None

    instance_class = None

    def __init__(self, target=None, parent=None, **wrap_kwargs):
        self.target = target
        self.parent = parent
        self._ = Wrapper(self, **wrap_kwargs)

    def call(self, name, args, kwargs):
        match name:
            case "__call__" if inspect.isclass(self.target):
                target = self.target(*args, **kwargs)
                return self.instance_class(target=target, parent=self)._
            case "__call__":
                return target(*args, **kwargs)
            case _:
                return getattr(target, name)(*args, **kwargs)

    def getattr(self, name):
        if not self.target:
            raise ValueError("No target is set on Interface.")

        attr = getattr(self.target, name)
        if isinstance(attr, types.MethodType):
            # Redirect call of target methods through imeta.
            return lambda *args, **kwargs: self.call(name, args, kwargs)
        return attr

    def clone(self, *args, **kwargs):
        """Return a clone of self with:

        - a new wrapper
        - and new trace watching same calls
        """
        clone = super().clone(*args, **kwargs)
        clone._._interface = clone
        return clone


Wrap.instance_class = Wrap
