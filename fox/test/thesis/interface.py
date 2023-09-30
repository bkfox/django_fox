from __future__ import annotations
from typing import Any

from . import dsl, inject, wrap
from .assume import Assume, Feign
from .traces import Trace, Traces


__all__ = ("Interface", "Predicate")


class Interface(wrap.Wrap, dsl.Expr):
    """Wrap a target, providing tracking function calls and providing
    assumptions about their results.

    .. code-block :: python

        # using without DSL
        interface = Interface(target)
        interface.join(Feign("func", 13))
        interface._.func()
        assert interface.contains(Trace("func", 13))

        # with dsl:
        with Interface(target) | Feign("func", 13) as interface:
            interface._.func()
            assert Trace("func", 13) in interface

        # or using expect syntax:
        with Interface(target) & Feign("func", 13) as interface:
            interface._.func()
    """

    traces: Traces = None
    assume: Assume = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.traces = Traces()
        self.assume = Assume()

    def set_parent(self, parent: Interface):
        super().set_parent(parent)
        if parent:
            self.assume = parent.assume.clone()
            self.traces = parent.traces.clone()

    def getattr(self, name: str) -> Any:
        if name in self.assume:
            return lambda *args, **kwargs: self.call(name, args, kwargs)
        return super().getattr(name)

    def call(self, name, args, kwargs):
        if self.traces.is_watching(name):
            self.traces.trace(name, args, kwargs)

        if feign := (self.assume and self.assume.get(name)):
            return feign.next()
        return super().call(name, args, kwargs)

    def join(
        self, other: Trace | Traces | Feign | Assume | Interface
    ) -> Interface:
        """
        DSL:
            - ``Trace``, ``Traces``, ``Watch``: join into self's traces
            - ``Feign``, ``Assume``: join into self's assume
        """
        match other:
            case Trace() | Traces():
                self.traces.join(other)
            case Feign() | Assume():
                self.assume.join(other)
            case Interface():
                self.assume.join(other.assume)
                self.traces.join(other.traces)
            case _:
                super().join(other)
        return self

    def expect(
        self, other: Trace | Traces | Feign | Assume | Interface
    ) -> Interface:
        match other:
            case Trace() | Traces():
                self.traces.expect(other)
            case Feign():
                self.traces.expect(Trace(other.name))
                self.assume.join(other)
            case Assume():
                for feign in other.values():
                    self.traces.expect(Trace(other.name))
                self.assume.join(other)
            case Interface():
                self.expect(other.assume)
                self.expect(other.traces)
            case _:
                super().expect(other)
        return self

    def contains(self, other: Trace | Traces | Feign | Assume):
        """
        DSL:
            - ``Trace``, ``Traces``, ``Watch``: check contains in self's traces
            - ``Feign``, ``Assume``: check contains self's assume
        """
        match other:
            case Trace() | Traces():
                return self.traces.contains(other)
            case Feign() | Assume():
                return self.assume.contains(other)
            case _:
                return super().contains(other)

    def __enter__(self) -> Interface:
        self.traces.__enter__()
        return super().__enter__(self)

    def __exit__(self, *args, **kwargs):
        self.traces.__exit__(*args, **kwargs)
        super().__exit__(self, *args, **kwargs)


Interface.instance_class = Interface


class Predicate(inject.Inject, Interface):
    pass
