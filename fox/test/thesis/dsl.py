"""Provide simple operands manipulation in order to have some kind of DSL.

Base object in DSL is ``Unit``. ``Expr`` provides operations on itself.

Operators can be chained, being executed only once ``exec()`` or ``__enter__``
is called. It results to a copy of the first object in the chain being
updated following the provided operators. Operators can be nested, in
such case they will be executed when required (parent clone or exec)

Operators:
    - ``|``: join
    - ``&``: join and expect
    - ``in``: contains
"""
from __future__ import annotations
from typing import Any, Iterator
import copy


__all__ = ("ExpectError", "ManyErrors", "Unit", "Expr", "Operand")


class ExpectError(ValueError):
    """Expectation was not met."""

    pass


class ManyErrors(Exception):
    """Gather multiple errors at once."""

    def __init__(self, msg: str, errors: list[Exception], *args, **kwargs):
        errors_msg = "\n".join(f"    - {error}" for error in errors)
        msg += f"\n{errors_msg}"
        self.errors = errors
        super().__init__(msg, *args, **kwargs)


# class UnitMeta:
#     def __new__(metacls, name, bases, attrs):
#         cls = super(UnitMeta).__new__(metacls, name, bases, attrs)
#         cls._dsl = metacls.init_dsl(cls)
#         return cls
#
#     @classmethod
#     def init_dsl(metacls, cls):
#         dsl = cls.DSL(cls)
#         return dsl


class Unit:
    key = None
    """All units instance must provide a value for this attribute."""

    def __init__(self, key: str = ""):
        self.key = key or (type(self).__name__ + f".{self}")

    def clone(self, clone: Unit = None, **init_kwargs) -> Unit:
        if clone is None:
            clone = type(self)(**init_kwargs)
        for key, attr in vars(self):
            match attr:
                case Unit():
                    attr = attr.clone()
                case Operand():
                    attr = attr.exec()
                case dict() | list():
                    attr = type(attr)(attr)
                case _ if key.startswith("_"):
                    continue
                case _:
                    attr = copy.copy(attr)
            setattr(clone, key, attr)
        return clone


class Expr(Unit):
    def join(self, other: Unit | Operand) -> Unit:
        if isinstance(other, Operand):
            return self.join(other.exec())
        raise TypeError(
            f"Invalid operand type (`{self.__class__.__name__}."
            f"join()` with `{other})`"
        )

    def expect(self, other: Unit | Operand) -> Unit:
        if isinstance(other, Operand):
            return self.expect(other.exec())
        raise TypeError(
            f"Invalid operand type (`{self.__class__.__name__}."
            f"expect()` with `{other})`"
        )

    def contains(self, other: Unit) -> Unit:
        raise TypeError(
            f"Invalid operand type (`{self.__class__.__name__}."
            f"contains()` with `{other})`"
        )

    def __or__(self, other: Unit | Operand) -> Operand:
        return Operand(self) | other

    def __and__(self, other: Unit | Operand) -> Operand:
        return Operand(self) & other

    def __contains__(self, other: Unit) -> bool:
        self.contains(other)
        return self

    def __enter__(self) -> Expr:
        return self

    def __exit__(self, *args, **kwargs):
        pass


class Registry(Expr):
    """Provide a registry of units contained in dict by key."""

    units = None

    def __init__(self):
        self.units = {}
        super().__init__()

    def get(self, key: str, default: Any = None):
        return self.units.get(key, default)

    def items(self) -> Iterator[tuple[str, Unit]]:
        return self.units.items()

    def keys(self) -> Iterator[str]:
        return self.units.keys()

    def values(self) -> Iterator[Unit]:
        return self.units.values()


class Operand:
    map = {"__or__": "join", "__and__": "map"}

    def __init__(self, node: Unit):
        self.node = node
        self.terms = []

    def exec(self) -> Unit:
        node = self.node.clone()
        for attr, term in self.terms.items():
            func = getattr(node, attr)
            if isinstance(term, Operand):
                term = term.exec()
            func(term)
        return node

    def __and__(self, other) -> Operand:
        self.terms.append((self.map("__and__"), other))
        return self

    def __or__(self, other) -> Operand:
        self.terms.append((self.map("__or__"), other))
        return self

    def __enter__(self) -> Expr:
        if self._node:
            raise RuntimeError("Already used in `with` statement")

        self._node = self.exec()
        if hasattr(self._node, "__enter__"):
            self._node.__enter__()
        return self._node

    def __exit__(self, *args, **kwargs):
        if hasattr(self._node, "__enter__"):
            self._node.__exit__(*args, **kwargs)
        self._node = None
