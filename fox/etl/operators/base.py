import copy

from ..utils import as_json_path, get_data

__all__ = ("Operator", "Chain", "GetData")


class Operator:
    """Operand on data, return a value from provided one.

    Minimal compatibility interface is provided for DRF fields.
    """

    def call(self, data):
        """Do actually something with data."""
        return data

    def run_validation(self, data):
        """DRF API compatibility: run `call()`"""
        return self.call(data)

    def to_internal_value(self, data):
        """DRF API compatibility: run `call()`"""
        return self.call(data)

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)


class Chain(Operator):
    """Chain multiple operators, using result of previous field transformation.

    Example:

        ```python
        chain_1 = Chain([
            GetData("$.path"),
            IntegerField()
        ])
        # or (append fields)
        chain_2 = Chain() >> GetData("$.path")
                          >> IntegerField()
        # or (prepend fields)
        chain_3 = Chain() << IntegerField
                          << GetData("$.path")
        ```
    """

    def __init__(self, *args, operators=None, **kwargs):
        self.operators = tuple()
        if operators:
            self.append(operators)
        super().__init__(*args, **kwargs)

    def clone(self):
        """Return shallow copy of self."""
        return copy.copy(self.operators)

    def append(self, operators, prepend=False):
        """Append provided operator or operators iterable to list of
        operators."""
        if isinstance(operators, Chain):
            operators = operators.operators
        elif isinstance(operators, Operator):
            operators = (operators,)
        else:
            operators = tuple(operators)

        if prepend:
            self.operators = operators + self.operators
        else:
            self.operators = self.operators + operators
        return self

    def prepend(self, operators):
        """Append provided operator or operators iterable to list of
        operators."""
        return self.append(operators, prepend=True)

    def call(
        self, data, _operators=None, _reverse=False, _method="call", **kwargs
    ):
        """Call operators passing results from one to each other param."""
        operators = _operators or self.operators
        if _reverse:
            operators = reversed(operators)
        for operator in operators:
            data = getattr(operator, _method)(data, **kwargs)

    def __lshift__(self, operator):
        """Prepend operator(s) to self."""
        return self.prepend(operator)

    def __rshift__(self, operator):
        """Append operator(s) to self."""
        return self.append(operator)


class GetData(Operator):
    """Using provided json path, extract data from source on deserialization.
    Do nothing on serialization.

    Write-only field !
    """

    def __init__(self, path, constructor=None, many=False, with_path=False):
        self.path = as_json_path(path)
        self.many = many
        self.with_path = with_path
        self.constructor = constructor

    def call(self, data):
        if not self.path:
            return data
        return get_data(
            data,
            self.path,
            many=self.many,
            with_path=self.with_path,
            constructor=self.constructor,
        )
