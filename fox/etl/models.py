from django.db import models
import pandas as pd


__all__ = ("QuerySet", "Model")


class QuerySet(models.QuerySet):
    def from_df(
        self, df: pd.DataFrame, column: str = "pk", field: str | None = None
    ):
        """Load items based on dataframe column. Column must match a field name
        when field is not provided.

        :param pd.DataFrame df: dataframe to get values from
        :param str column: dataframe column to look for
        :param str field: model field name to look up (defaults to column)
        :return filtered queryset.
        """
        field = field or column
        lookup = {field: df.loc[df[column].notnull(), column]}
        return self.filter(**lookup)

    def to_df(self, columns: [str] = None) -> pd.DataFrame:
        """Return a Dataframe using QuerySet fetched values.

        :param [str] columns: extract only those values.
        :return the new DataFrame.
        """
        fields = {field.name for field in self.model._meta.get_fields()}
        if not columns:
            columns = list(fields)
        elif not_fields := [col for col in columns if col not in fields]:
            raise ValueError(
                "Provided columns are not model fields: " ", ".join(not_fields)
            )

        values = self.values_list(columns)
        return pd.DataFrame(values, columns=columns)


class Model(models.Model):
    """Abstract empty model providing tools to work with dataframes."""

    objects = QuerySet.as_manager()

    # TODO:
    # - related_to_df(self, field)

    class Meta:
        abstract = True
