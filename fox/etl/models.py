from django.db import models

import pandas as pd

from .pandas import DjangoAccessor


__all__ = ("QuerySet", "Model")


class QuerySet(models.QuerySet):
    df_class = pd.DataFrame
    df_accessor_class = DjangoAccessor

    def from_df(self, df: pd.DataFrame, field: str = None, prefix: str = True):
        """Load items based on dataframe column. Column must match a field name
        when field is not provided.

        :param pd.DataFrame df: dataframe to get values from
        :param str field: model field name to look up (defaults to column)
        :param str prefix: column prefix
        :return filtered queryset.
        """
        if field is None:
            field = "pk"
        column = df.django.get_column(self.model, field, prefix)
        lookup = {field + "__in": df.loc[df[column].notnull(), column].values}
        return self.filter(**lookup)

    def to_df(self, fields: [str] = None, prefix: str = True) -> pd.DataFrame:
        """Return a Dataframe using QuerySet fetched values.

        :param [str] columns: extract only those values.
        :param bool model_prefix: if True, prefix using model's name
        :param str prefix: column prefix
        :return the new ModelDataFrame.
        """
        if not fields:
            fields = [f.name for f in self.model._meta.get_fields()]
        mapping = {
            field: self.df_accessor_class.get_column(self.model, field, prefix)
            for field in fields
        }
        values = self.values_list(*mapping.keys())
        return self.df_class(values, columns=mapping.values())


class Model(models.Model):
    """Abstract empty model providing tools to work with dataframes."""

    objects = QuerySet.as_manager()

    # TODO:
    # - related_to_df(self, field)

    class Meta:
        abstract = True
