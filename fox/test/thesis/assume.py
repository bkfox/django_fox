from __future__ import annotations
from typing import Any
import inspect

from . import dsl

__all__ = (
    "Feign",
    "Assume",
)


class Feign(dsl.Unit):
    """Provide one or more values to use by assumptions. It describes a
    function results to return when called.

    It handles:
    - one value: among different `get`, the value is always the same
    - many values: FIFO list of expected values;
    - values can be callable: in such cas
    """

    def __init__(self, key: str, *values: list[Any], many: bool | None = None):
        self.values = values
        self.many = many if many is not None else len(values) > 1
        self.index = 0
        super().__init__(key)

    def next(self, args: list[Any] = [], kwargs: dict[str, Any] = {}) -> Any:
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

    def clone(self, key: str = None) -> Feign:
        """Clone self, keep the same list between instances."""
        clone = type(self)(key or self.key, many=self.many)
        clone.values = self.values
        return clone

    def __or__(self, other: Feign | Assume) -> Assume:
        """
        DSL:
            - ``Feign``, ``Assume``: join into provided Assume or new one.
        """
        if isinstance(other, Feign):
            return Assume().bind(self.key, self).bind(other.key, other)
        elif isinstance(other, Assume):
            return other & self
        raise TypeError(
            "Provided operand value must either be an "
            "Feign or Assume instance"
        )


class Assume(dsl.Registry):
    """Provides assumptions on function results.

    An assumption contains multiple Feign instance describing expected
    results when they are called.
    """

    def __init__(self, *feigns: list[Feign], **feigns_desc: dict[str, Any]):
        """For each keyword argument, create/set an assume as key is the
        attribute name, and value a single value for all calls or Feign."""
        self.units = {feign.key: feign for feign in feigns}
        for name, item in feigns_desc.items():
            self.feign(name, item)
        super().__init__()

    def feign(self, name: str, *values: list[Any]) -> Feign:
        """Set an feign by name. When item is only one value and is an instance
        of Feign, set it as it. Otherwise, create an instance of Feign.

        :param str name: function or attribute name
        :param Feign|Any *item: an assume or its values
        :returns: self
        """
        feign = Feign(name, *values)
        self.set(feign)
        return feign

    def set(self, feign: Feign, name: str | None = None) -> Feign:
        """Set an Feign by name."""
        if feign.name != name:
            feign = feign.clone(name)
            feign.name = name
        self.units[name] = feign
        return feign

    def pop(self, name: str) -> Feign | None:
        """Remove assume with provided name."""
        return self.units.pop(name, None)

    def next(
        self, name: str, args: list[Any] = [], kwargs: dict[str, Any] = {}
    ) -> Any:
        """Get feignd function result.

        :param name: function name
        :param args: positional arguments passed to function
        :param kwargs: keyword arguments passed to function
        :raises KeyError: no registered function with this `name`.
        """
        item = self.units[name]
        return item.next(args, kwargs)

    def clone(self) -> Assume:
        """Return a clone of self."""
        return type(self)(**self._clone_feigns())

    def clone_feigns(self, names=None) -> dict:
        """Return a dict of self's feigns clones."""
        names = names if names is not None else self.items.keys()
        return {name: self.units[name].clone() for name in names}

    def contains(self, other: Feign | str | Assume) -> bool:
        """
        DSL:
            - ``Feign``, str: check if function is feigned (by name)
            - ``Assume``: check if all other's functions are feigned
        """
        match other:
            case Feign():
                return other.name in self.units
            case str():
                return other in self.units
            case Assume():
                return all(key in self.units for key in other.keys())
            case _:
                return super().contains(other)

    def join(self, other: Feign | Assume) -> Assume:
        """
        DSL:
            - ``Feign``, ``Assume``: join into self.
        """
        match other:
            case Feign():
                self.set(other)
            case Assume():
                for feign in other.values():
                    self.set(feign)
            case _:
                super().join(other)
        return self
