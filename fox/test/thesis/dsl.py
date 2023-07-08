"""Provide simple operands manipulation in order to have some kind of DSL.

Base object in DSL is ``Unit``. ``Node`` provides operations on itself.

Operators can be chained, being executed only once ``exec()`` or ``__enter__``
is called. It results to a copy of the first object in the chain being
updated following the provided operators. Operators can be nested, in
such case they will be executed when required (parent clone or exec)

Operators:
    - ``|``: join
    - ``&``: join and expect
    - ``in``: contains
"""
import copy


__all__ = ("ExpectError", "ManyErrors", "Unit", "Node", "NodeOp")


class ExpectError(ValueError):
    """Expectation was not met."""

    pass


class ManyErrors(Exception):
    """Gather multiple errors at once."""

    def __init__(self, msg, errors, *args, **kwargs):
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

    def __init__(self, key=None):
        self.key = key or (type(self).__name__ + f".{self}")

    def clone(self, clone=None, **init_kwargs):
        if clone is None:
            clone = type(self)(**init_kwargs)
        for key, attr in vars(self):
            match attr:
                case Unit():
                    attr = attr.clone()
                case NodeOp():
                    attr = attr.exec()
                case dict() | list():
                    attr = type(attr)(attr)
                case _ if key.startswith("_"):
                    continue
                case _:
                    attr = copy.copy(attr)
            setattr(clone, key, attr)
        return clone


class Node(Unit):
    def join(self, other):
        if isinstance(other, NodeOp):
            return self.join(other.exec())
        raise TypeError(
            f"Invalid operand type (`{self.__class__.__name__}."
            f"join()` with `{other})`"
        )

    def expect(self, other):
        if isinstance(other, NodeOp):
            return self.expect(other.exec())
        raise TypeError(
            f"Invalid operand type (`{self.__class__.__name__}."
            f"expect()` with `{other})`"
        )

    def contains(self, other):
        raise TypeError(
            f"Invalid operand type (`{self.__class__.__name__}."
            f"contains()` with `{other})`"
        )

    def __or__(self, other):
        op = NodeOp(self)
        return op | other

    def __and__(self, other):
        op = NodeOp(self)
        return op & other

    def __contains__(self, other):
        self.contains(other)
        return self

    def __enter__(self):
        pass

    def __exit__(self, *args, **kwargs):
        pass


class NodeWithChildren(Node):
    units = None

    def __init__(self):
        self.units = {}
        super().__init__()

    def get(self, key, default=None):
        return self.units.get(key, default)

    def items(self):
        return self.units.items()

    def keys(self):
        return self.units.keys()

    def values(self):
        return self.units.values()


class NodeOpMeta:
    def __new__(mcls, name, bases, attrs):
        cls = super(NodeOpMeta).__new__(mcls, name, bases, attrs)
        mcls.init_map(cls)
        return cls

    @classmethod
    def init_map(mcls, cls):
        for func, target in cls.map.items():
            mcls.add_mapping(cls, func, target)

    @classmethod
    def add_mapping(mcls, cls, func, target):
        def method(self, other):
            self.terms.setdefault(target, other)

        setattr(cls, func, method)


class NodeOp(metaclass=NodeOpMeta):
    map = {"__or__": "join", "__contains__": "contain", "__and__": "expect"}

    def __init__(self, node: Unit):
        self.node = node
        self.terms = {}

    def exec(self):
        node = self.node.clone()
        for attr, terms in self.terms.items():
            func = getattr(node, attr)
            for term in terms:
                if isinstance(term, NodeOp):
                    term = term.exec()
                func(term)
        return node

    def __enter__(self):
        if self._node:
            raise RuntimeError("Already used in `with` statement")

        self._node = self.exec()
        if hasattr(self._node, "__enter__"):
            self._node.__enter__()
        return self._now

    def __exit__(self, *args, **kwargs):
        if hasattr(self._node, "__enter__"):
            self._node.__exit__(*args, **kwargs)
        self._node = None
