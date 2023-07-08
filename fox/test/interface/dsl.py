import copy


class UnitMeta:
    def __new__(metacls, name, bases, attrs):
        cls = super(UnitMeta).__new__(metacls, name, bases, attrs)
        cls._dsl = metacls.init_dsl(cls)
        return cls

    @classmethod
    def init_dsl(metacls, cls):
        dsl = cls.DSL(cls)
        return dsl


class Unit(metaclass=UnitMeta):
    class DSL:
        pass

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
        raise TypeError("Invalid operand type")

    def contains(self, other):
        raise TypeError("Invalid operand type")

    def __or__(self, other):
        op = NodeOp(self)
        return op | other

    def __and__(self, other):
        op = NodeOp(self)
        return op & other

    def __contains__(self, other):
        self.contains(other)
        return self


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
    map = {"__or__": "join"}

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
