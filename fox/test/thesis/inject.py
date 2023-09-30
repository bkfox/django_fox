from __future__ import annotations
from typing import Any
from . import wrap


__all__ = ("Inject",)


class Inject(wrap.Wrap):
    """Provide an interface that is injected into another namespace (module or
    object). It can be used along the `with` statement.

    .. code-block :: python

        iface = (
            Inject(os, "path") << Assume(
                abspath="/abs/path",
                exists=True
            )
        )

        assert os.path.abspath("relative") != "/abs/path"

        with iface | Feign("dirname", "/tmp"):
            assert os.path.abspath("relative") == "/abs/path"
            assert os.path.dirname("/abs/path") == "/tmp"
            assert not os.path.exists("/tmp/false")
            assert Trace("abspath") in iface
    """

    # FIXME: move out
    ns = None
    ns_attr = None

    def __init__(self, ns: Any, ns_attr: str, *args, **kwargs):
        self.ns = ns
        self.ns_attr = ns_attr

        if "key" not in kwargs:
            kwargs["key"] = type(self).__name__ + f".{ns}.{ns_attr}"
        super().__init__(None, *args, **kwargs)

    @property
    def is_injected(self) -> bool:
        """True if injection is done."""
        return self.target is None

    @property
    def ns_target(self) -> Any:
        """Actual namespace's target (using ns.ns_attr)"""
        if self.ns and self.ns_attr:
            return getattr(self.ns, self.ns_attr, None)
        return None

    def clone(self) -> Inject:
        clone = super().clone()
        clone.target = None
        return clone

    def inject(self) -> Inject:
        """Inject interface into the namespace."""
        if self.is_injected:
            raise RuntimeError("Injection is already injected")

        ns_target = getattr(self.ns, self.ns_attr, None)
        if self.target is ns_target:
            return
        elif self.target is not None and self.ns:
            raise RuntimeError(
                "self target already injected. It must be "
                "`release` before `inject`."
            )

        self.target = ns_target
        setattr(self.ns, self.ns_attr, self._)
        return self

    def release(self) -> Inject:
        """Remove injection from previously injected parent, reset target."""
        if self.is_injected:
            if self.ns_target is self._:
                setattr(self.ns, self.ns_attr, self.target)
            delattr(self, "target")
        return self

    def __enter__(self) -> Inject:
        """
        DSL:
           - inject wrapped object into target
        """
        self.inject()
        return super().__enter__(self)

    def __exit__(self, *args, **kwargs):
        """
        DSL:
           - release wrapped object into target
        """
        self.release()
        super().__exit__(self, *args, **kwargs)
