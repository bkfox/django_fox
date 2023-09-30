from __future__ import annotations
from typing import Any

from . import dsl


__all__ = ("Trace", "Traces")


class Trace(dsl.Unit):
    """Describe a function call that happened. It is used in two different
    ways:

        - to trace a call
        - to check if a call has been done (in Traces)

    When checking a call has been done, only provided values are checked.
    For instance:

    .. code-block :: python

        traces = Traces()
        traces.trace("call", [1,2,3], {"a": "val"})

        assert Trace("call", [1,2,3]) in traces
        assert Trace("call", kwargs={"a": "val"}) in traces
        assert Trace("call", kwargs={"a": "val", "b": "val"}) not in traces
    """

    def __init__(
        self, key: str, args: list[Any] = None, kwargs: dict[str, Any] = None
    ):
        self.args = args
        self.kwargs = kwargs
        super().__init__(key)

    def match(self, trace: Trace) -> bool:
        return (trace.args is None or self.args == trace.args) and (
            trace.kwargs is None or self.kwargs == trace.kwargs
        )


class Traces(dsl.Registry):
    """Keep track of function calls.

    A function should be declared as being watched in order to be
    tracked.
    """

    traces = None

    def __init__(self, watch: list | tuple = []):
        self.units = {key: [] for key in watch}
        self.expects = []
        super().__init__()

    def is_watching(self, key: str) -> bool:
        """Return True if function is being watched."""
        return key in self.units

    def watch(self, key: str):
        """Watch a provided function."""
        self.units.setdefault(key, [])

    def trace(
        self,
        key: str,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        force: bool = False,
        no_exc: bool = False,
    ) -> Trace:
        """Add a trace."""
        trace = Trace(key, args, kwargs)
        self.append(trace, force=force, no_exc=no_exc)
        return trace

    def find(self, trace: Trace) -> bool:
        """Return the first trace matching provided one, or None."""
        traces = self.units.get(trace.key)
        if not traces:
            return None
        return next((r for r in self.units if r.match(trace)), None)

    def find_all(self, trace: Trace) -> bool:
        """Return a tumple of traces matching provided one."""
        traces = self.units.get(trace.key)
        if not traces:
            return tuple()
        return tuple(r for r in self.units if r.match(trace))

    def clone(self) -> Traces:
        """Return a copy of self without previous calls."""
        return type(self)(self.units.keys())

    def join(
        self, other: Trace | Traces, force: bool = False, no_exc: bool = False
    ) -> Traces:
        """
        DSL:
            - ``Trace() ``: add trace to self
            - ``Traces() ``: add all traces & expects to self.
        """
        match other:
            case Trace(key):
                match key in self.units:
                    case True:
                        self.units[key].append(other)
                    case False if force:
                        self.units[key] = [other]
            case Traces(traces):
                for key, items in traces.items():
                    if key not in self.units:
                        self.units[key] = list(items)
                    else:
                        self.units[key].extend(items)
                    self.expects.extend(other.expects)
            case _:
                return super().append(other)
        return self

    def expect(self, other: Trace | Traces) -> Traces:
        """
        DSL:
            - ``Trace``: watch and add to expects
            - ``Traces``: watch and add expects (does not join traces)
        """
        match other:
            case Trace():
                self.watch(other.key)
            case Traces():
                for key in other.keys():
                    self.watch(key)
                self.expects.extend(other.expects)
            case _:
                return super().expect(other)
        self.expects.append(other)
        return self

    def test_expects(self, exc: bool = True) -> bool:
        """Test if all expectations are met.

        If ``exc == True``, then raise an ``ExpectationError``.
        """
        for expect in self.expects:
            match self.contains(expect):
                case False if exc:
                    raise dsl.ExpectError(f"Expectation not met: {expect}")
                case False:
                    return False
        return True

    def contains(self, other: Trace | Traces) -> bool:
        """
        DSL:
            - ``Trace``: check if any of saved trace matches provided one.
            - ``Traces``: check if all traces matches, respecting other's order.
        """
        match other:
            case Trace():
                traces = self.traces.get(other.key)
                return (
                    other
                    and any(trace.match(other) for trace in traces)
                    or False
                )
            case Traces():
                for key, traces_ in other.items():
                    traces = self.units.get(key)
                    if not traces:
                        return False
                    for trace, trace_ in zip(traces, traces_):
                        if not trace.match(trace_):
                            return False
            case _:
                return super().contains(other)

    def __enter__(self) -> Traces:
        return self

    def __exit__(self, *args, **kwargs):
        self.test_expects()
