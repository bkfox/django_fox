from rest_framework import fields

from .. import operators as ops

__all__ = (
    "OperatorField",
    "ChainField",
)


class OperatorField(fields.Field):
    """Wrap one or two operators as field."""

    def __init__(
        self, to_internal_value=None, to_representation=None, **kwargs
    ):
        if not (to_internal_value or to_representation):
            raise ValueError(
                "At least one of to_internal_value or "
                "to_representation must be provided"
            )

        if to_internal_value:
            self.to_internal_value = to_internal_value
        else:
            self.read_only = True

        if to_representation:
            self.to_representation = to_representation
        else:
            self.write_only = True
        super().__init__(**kwargs)


class ChainField(ops.Chain, fields.Field):
    """Chain multiple fields des-serialization, using result of previous field
    transformation.

    Mode specifies call direction of `to_representation` and
    `to_internal_value`:

    | Mode         | to_representation | to_internal_value |
    |--------------|-------------------|-------------------|
    | UP           | first -> last     | first -> last     |
    | DOWN         | last  -> first    | last  -> first    |
    | UP_AND_DOWN  | first -> last     | last  -> first    |
    | DOWN_AND_UP  | last  -> first    | first -> last     |

    By default, since fields provided here are aiming data extraction,
    default mode is DOWN_AND_UP.

    Example:

        ```python
        field_1 = ChainField([
            GetData("$.path"),
            IntegerField()
        ])
        # or (append fields)
        field_2 = ChainField() >> GetData("$.path")
                               >> IntegerField()
        # or (prepend fields)
        field_3 = ChainField() << IntegerField
                               << GetData("$.path")
        ```
    """

    DOWN = 0b00000000
    UP = 0b00000011
    UP_AND_DOWN = 0b00000010
    DOWN_AND_UP = 0b00000001

    def __init__(self, *args, mode=DOWN_AND_UP, **kwargs):
        self.mode = mode
        super().__init__(*args, **kwargs)

    @property
    def fields(self):
        return (op for op in self.operators if isinstance(op, fields.Field))

    def append(self, operators, prepend=False):
        """Append provided field or operators iterable to list of operators."""
        if isinstance(operators, ChainField):
            operators = operators.chain.operators
        elif isinstance(operators, (fields.Field, ops.Operator)):
            operators = (operators,)

        ro, wo = self._check_read_write_only(operators)
        super().append(operators, prepend=prepend)
        self.read_only, self.write_only = ro, wo
        return self

    def _check_read_write_only(self, fields):
        """Test fields read/write_only values, returning a tuple of determined
        values.

        :returns: New values for `(read_only, write_only)`
        :raise ValueError: when invalid values for write/read_only
        """
        ro = self.read_only or any(
            getattr(f, "read_only", False) for f in fields
        )
        wo = self.write_only or any(
            getattr(f, "write_only", False) for f in fields
        )
        if ro and wo:
            raise ValueError(
                "read_only and write_only can not be mixed up " "in a chain."
            )
        return ro, wo

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        for field in self.fields:
            field.bind(field_name, parent)

    def run_validation(self, data=fields.empty):
        return self.call(
            data,
            _method="run_validation",
            _reverse=self.model & self.DOWN_AND_UP,
        )

    def to_internal_value(self, data):
        return self.call(
            data,
            _method="to_internal_value",
            _reverse=self.model & self.DOWN_AND_UP,
        )

    def to_representation(self, value):
        """This method can only be called if all chained fields provide a
        `to_representation` method."""
        return self.call(
            value,
            _method="to_representation",
            _reverse=self.model & self.UP_AND_DOWN,
        )


class RelationField(ops.Relation, fields.Field):
    pass
