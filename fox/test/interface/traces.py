from __future__ import annotations
from collections import namedtuple

from . import dsl


__all__ = ("Trace", "Traces")


class Trace(dsl.Unit):
    def __init__(self, name, args=None, kwargs=None):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def match(self, trace: Trace) -> bool:
        return (trace.args is None or self.args == trace.args) and (
            trace.kwargs is None or self.kwargs == trace.kwargs
        )


Watch = namedtuple("Watch", ["name"])
"""
DSL: trace the calls for provided name.
"""


class Traces(dsl.Node):
    """Keep trace of function calls."""

    traces = None

    def __init__(self, watch: list | tuple = []):
        self.traces = {name: [] for name in watch}

    def is_watching(self, name):
        return name in self.traces

    def watch(self, name):
        self.append(Watch(name))

    def trace(self, name, args=None, kwargs=None, force=False, no_exc=False):
        """Add a trace."""
        trace = Trace(name, args, kwargs)
        self.append(trace, force=force, no_exc=no_exc)
        return trace

    def match(self, trace: Trace) -> bool:
        """Return True if provided trace matches one of the saved trace."""
        traces = self.traces.get(trace.name)
        return traces and any(r.match(trace) for r in self.traces) or False

    def find(self, trace: Trace) -> bool:
        """Return the first trace matching provided one, or None."""
        traces = self.traces.get(trace.name)
        if not traces:
            return None
        return next((r for r in self.traces if r.match(trace)), None)

    def find_all(self, trace: Trace) -> bool:
        """Return a tumple of traces matching provided one."""
        traces = self.traces.get(trace.name)
        if not traces:
            return tuple()
        return tuple(r for r in self.traces if r.match(trace))

    def clone(self):
        """Return a copy of self without previous calls."""
        return type(self)(self.traces.keys())

    def join(self, other, force=False, no_exc=False):
        match other:
            case Trace(name):
                match name in self.traces:
                    case True:
                        self.traces[name].append(other)
                    case False if force:
                        self.traces[name] = [other]
            case Traces(traces):
                for key, items in traces.items():
                    if key not in self.traces:
                        self.traces[key] = list(items)
                    else:
                        self.traces[key].extend(items)
            case Watch():
                self.traces[other.name] = []
            case _:
                return super().append(other)
        return self

    def contains(self, other):
        """Return True if provided trace matches."""
        match other:
            case Trace():
                return self.match(other)
            case _:
                return super().contains(other)
