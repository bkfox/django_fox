from . import dsl, inject, wrap
from .assume import Assume, Feign
from .traces import Trace, Traces, Watch


__all__ = ("Interface", "Predicate")


class Interface(wrap.Wrap, dsl.Node):
    traces: Traces = None
    assume: Assume = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.traces = Traces()
        self.assume = Assume()

    def set_parent(self, parent):
        super().set_parent(parent)
        if parent:
            self.assume = parent.assume.clone()
            self.traces = parent.traces.clone()

    def getattr(self, name):
        if name in self.assume:
            return lambda *args, **kwargs: self.call(name, args, kwargs)
        return super().getattr(name)

    def call(self, name, args, kwargs):
        if self.traces.is_watching(name):
            self.traces.trace(name, args, kwargs)

        if feign := (self.assume and self.assume.get(name)):
            return feign.next()
        return super().call(name, args, kwargs)

    def join(self, other):
        match other:
            case Trace() | Traces() | Watch():
                self.traces.join(other)
            case Feign() | Assume():
                self.assume.join(other)
            case _:
                super().join(other)
        return self

    def contains(self, other):
        match other:
            case Trace() | Traces() | Watch():
                return self.traces.contains(other)
            case Feign() | Assume():
                return self.assume.contains(other)
            case _:
                return super().contains(other)


Interface.instance_class = Interface


class Predicate(inject.Inject, Interface):
    pass
