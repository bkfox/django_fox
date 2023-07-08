"""Interfaces provides assumptions about the result of function calls. This
module provide classes to work with it.

An assumption (`Assume`) maps attribute names to feigned values, which
are used when a function call is redirected.


.. code-block :: python

    with interface.assume(bar=8, foo="top") as assume:
        # calls of bar() will return 8

        with assume & Feign("bar", 10, 9, 8, 7):
            # calls of bar() will return 10, next call 9, etc.
            # ...
            assert Trace(bar_kw="param") in assume.get("bar")
"""
import inspect

from . import dsl

__all__ = (
    "Feign",
    "Assume",
)


class Feign(dsl.Unit):
    """Provide one or more values to use by assumptions.

    It handles:
    - one value: among different `get`, the value is always the same
    - many values: FIFO list of expected values;
    - values can be callable: in such cas
    """

    def __init__(self, name, *values, many=None):
        self.name = name
        self.values = values
        self.many = many if many is not None else len(values) > 1
        self.index = 0

    def next(self, args=[], kwargs={}):
        """Get the next value for the assume and add a trace.

        :raises IndexError: no more values to pop.
        """
        if self.index >= len(self.values):
            raise IndexError("No enough values have been provided to Feign.")

        value = self.values[self.index]
        if self.many:
            self.index += 1
        if inspect.isfunction(value):
            return value(*args, **kwargs)
        return value

    def clone(self, name=None):
        clone = type(self)(name or self.name, many=self.many)
        clone.values = self.values
        return clone

    def __and__(self, other):
        from .assume import Assume

        if isinstance(other, Feign):
            return Assume().bind(self.name, self).bind(other.name, other)
        elif isinstance(other, Assume):
            return other & self
        raise TypeError(
            "Provided operand value must either be an "
            "Feign or Assume instance"
        )


class Assume(dsl.Node):
    """Provide assumes on function results."""

    def __init__(self, *feigns, **feigns_desc):
        """For each keyword argument, create/set an assume as key is the
        attribute name, and value a single value for all calls or Feign."""
        self.feigns = {feign.name: feign for feign in feigns}
        for name, item in feigns_desc.items():
            self.feign(name, item)

    def feign(self, name, *values):
        """Set an feign by name. When item is only one value and is an instance
        of Feign, set it as it. Otherwise, create an instance of Feign.

        :param str name: function or attribute name
        :param Feign|Any *item: an assume or its values
        :returns: self
        """
        self.set(Feign(name, *values))
        return self

    def set(self, assume, name=None):
        """Set an Feign by name."""
        if assume.name != name:
            assume = assume.clone(name)
            assume.name = name
        self.feigns[name] = assume

    def pop(self, name):
        """Remove assume with provided name."""
        return self.feigns.pop(name, None)

    def get(self, name):
        """
        Get an Feign instance by name
        :returns: Feign or None.
        """
        return self.feigns.get(name)

    def next(self, name, args=[], kwargs={}):
        """Get feignd function result.

        :param name: function name
        :param args: positional arguments passed to function
        :param kwargs: keyword arguments passed to function
        :raises KeyError: no registered function with this `name`.
        """
        item = self.feigns[name]
        return item.next(args, kwargs)

    def keys(self):
        """Return feigns' names iterator."""
        return self.feigns.keys()

    def values(self):
        """Return feigns' instances iterator."""
        return self.feigns.values()

    def items(self):
        """Return feigns iterator of `(key, feign)`"""
        return self.feigns.items()

    def clone(self):
        """Return a clone of self."""
        return type(self)(**self._clone_feigns())

    def clone_feigns(self, names=None):
        """Return a dict of self's feigns clones."""
        names = names if names is not None else self.items.keys()
        return {name: self.feigns[name].clone() for name in names}

    def contains(self, other):
        """Return True if a Feign is provided for this `name`."""
        match other:
            case Feign():
                return other.name in self.feigns
            case str():
                return other in self.feigns
            case Assume():
                return all(feign.name in self.feign for feign in other.feign)
            case _:
                return super().contains(other)

    def join(self, other):
        match other:
            case Feign():
                self.set(other)
            case Assume():
                for feign in other.values():
                    self.set(feign)
            case _:
                super().join(other)
        return self
