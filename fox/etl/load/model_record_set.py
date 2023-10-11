import pandas as pd
from rest_framework import serializers

from .record_set import RecordSet


__all__ = ("ModelRecordSet",)


class ModelRecordSet(RecordSet):
    model = None
    """Django model class."""

    def __init__(self, model=None, df=None, columns=None, **df_kwargs):
        self.model = model
        if model and not (df or columns):
            columns = self.columns_from_model(model)
        columns.add("pk")
        self.fields = tuple(columns)

        super().__init__(df=df, columns=columns, **df_kwargs)

    @classmethod
    def from_serializer(cls, serializer_class, *args, **kwargs):
        if issubclass(serializer_class, serializers.ModelSerializer):
            kwargs.setdefault("model", serializer_class.Meta.model)
        return super(ModelRecordSet, cls).from_serializer(*args, **kwargs)

    @classmethod
    def columns_from_model(cls, model):
        return set(f.name for f in model._meta.get_fields())

    def update_qs(self, queryset, strict=True):
        """Load queryset into record set's dataframe.

        Updated/inserted fields are tagged as not updated.
        """
        fields = strict and self.df.columns or []
        df = pd.DataFrame.from_records(queryset.values(*fields))
        df["_unsaved"] = False
        self.update(df)

    def save(self, df=None, all=False):
        """Save items into database, create and update."""
        if df is None:
            df = self.df

        created_df = self._create(df)
        df.update(created_df)

        updated_df = self._update(df)
        df.update(updated_df)

    def _create(self, df):
        """Bulk create items from df, returning sub-df with db primary keys."""
        series = df.loc[df["pk"] is None, self.fields]
        items = list(self.as_models(series))
        self.model.bulk_create(items)
        series["pk"] = (item.pk for item in items)
        series["_unsaved"] = False
        return series

    def _update(self, df):
        """Bulk update items from df, returning sub-df."""
        series = df.loc[df["pk"] is not None, self.fields]
        items = list(self.as_models(series))
        self.model.bulk_update(items, self.fields)
        series["_unsaved"] = False
        return series

    def as_models(self, df=None):
        """Yield model instances from df."""
        if df is None:
            df = self.df

        for attrs in df.itertuples():
            attrs = attrs.as_dict()
            yield self.model(**attrs)
