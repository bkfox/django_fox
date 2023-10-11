"""Provide utility classes to work with panda dataframes."""
import pandas as pd


__all__ = ("RecordAccessor", "DjangoAccessor")


@pd.api.extensions.register_dataframe_accessor("record")
class RecordAccessor:
    def __init__(self, df):
        self._validate(df)
        self.df = df

    @staticmethod
    def _validate(obj):
        # if "latitude" not in obj.columns or "longitude" not in obj.columns:
        #    raise AttributeError("Must have 'latitude' and 'longitude'.")
        pass

    def get_column(self, record, field, prefix: str = ""):
        if prefix is True:
            prefix = self.get_prefix(record)
        return prefix + field

    def get_fields_iter(self, record, fields: [str] = None, prefix: str = ""):
        """Return a dict of fields mapping to column names.

        :param records.Model record: record to extract columns from
        :param [str] columns: those columns only
        :param str prefix: if column names' prefix in dataframe.
        :return a dict of `{field: column}`
        """
        if prefix is True:
            prefix = self.get_prefix(record)

        mapping = (
            (field, prefix + field.name)
            for field in fields
            if (prefix + field.name) in self.df
        )
        return mapping

    def get_prefix(self, record):
        return f"{type(record).__name__.lower()}."

    def get_fields(self, *args, **kwargs):
        """Return a dict of fields mapping to column names.

        Same as `get_fields_iter()` except it returns a dict.
        """
        return dict(self.get_fields_iter(*args, **kwargs))

    def to_records_iter(self, record, fields=None, prefix="", rows=None):
        """Return an iterator returning each row as record instance.

        Extra attribute `df_index` is set to each instance,
        corresponding to dataframe's index.
        """
        fields = self.get_fields(record, fields, prefix)
        if rows is None:
            rows = self.df.iterrows()

        for index, row in self.df.iterrows():
            attrs = {
                field: row[col]
                for field, col in fields.items()
                if not row[col].isnull()
            }
            obj = record(**attrs)
            setattr(obj, "df_index", index)
            yield obj

    def to_records(self, *args, **kwargs):
        """Return result of `to_records_iter()` as a list."""
        return list(self.to_records_iter(*args, **kwargs))

    def extract(self, record, fields: [str] = None, prefix=""):
        """Return a new dataframe's accessor for the provided record."""
        fields = self.get_fields(record, fields, prefix)
        # TODO FIXME

    def updated(self):
        """Return accessor to dataframe with only updated objects."""
        pass

    def update(self, df: pd.DataFrame, on: str = "pk"):
        """Update records with provided dataframe.

        Values are merged, NaN values filled with previous existing ones.

        :param pd.DataFrame df: insert values from this dataframe.
        :param str on: use this column to match values.
        :return self accessor.
        """
        if "_record_updated" not in df.columns:
            df["_record_updated"] = True
        common_cols = tuple(col for col in df.columns if col in self.df)
        dd = pd.merge(
            self.df, df, on=on, how="outer", suffixes=["_", None], copy=False
        )
        for col in common_cols:
            dd[col] = dd[col].combine_first(dd.pop(col + "_"))
        self.df = dd
        return self


# FIXME: inherit from RecordAccessor? -> if not dont forget init and validate
@pd.api.extensions.register_dataframe_accessor("django")
class DjangoAccessor(RecordAccessor):
    """This accessor provides function to work with Django. It assume that
    columns have the same name as fields.

    When working with ModelDataFrame, the `model` argument of the
    methods is not required.
    """

    @classmethod
    def get_prefix(self, model):
        return f"{model._meta.label_lower}."

    @classmethod
    def get_fields_iter(self, model, fields: [str] = None, prefix: str = ""):
        """Return a dict of fields mapping to column names.

        :param models.Model model: model to extract columns from
        :param [str] columns: those columns only
        :param str prefix: if column names' prefix in dataframe.
        :return a dict of `{field: column}`
        """
        model_fields = set(field.name for field in model._meta.get_fields())
        if fields:
            fields = fields and (set(fields) & model_fields) or model_fields
        else:
            fields = model_fields
        return super().get_fields_iter(model, fields, prefix)

    def save(self, model, fields=None, prefix="", updated=True):
        """Save rows as models into database, handling update and create.

        :param Model model: model to instanciate.
        :param [str] fields: select which model fields to save
        :param str prefix: column prefix
        :param bool updated: if True only updated records will be saved
        :return a tuple of `[created_records], [updated_records]`.
        """
        if updated:
            self = self.updated()
        df = self.df
        pk = self.get_column(model, "pk", prefix)
        if pk not in df:
            df.insert(0, pk, None)

        to_create = df.loc[df[pk].isnull()]
        to_create = self.to_records(model, fields, prefix)

        to_update = df.loc[df[pk].notnull()]
        to_update = self.to_records(model, fields, prefix)

        model.objects.bulk_create(to_create)
        model.objects.bulk_update(to_update, fields.keys())

        # FIXME: check it is okay
        pks = {obj.df_index: obj.pk for obj in to_create}
        df.loc[pks.keys()] = pd.Series(pks.values())

        return to_create, to_update
