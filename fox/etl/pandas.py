"""Provide utility classes to work with panda dataframes."""
import pandas as pd


__all__ = ("RecordsAccessor", "DjangoAccessor")


@pd.api.extensions.register_dataframe_accessor("records")
class RecordsAccessor:
    """This accessor allows to manipulate."""

    def __init__(self, df):
        self._validate(df)
        self.df = df

    @staticmethod
    def _validate(obj):
        # if "latitude" not in obj.columns or "longitude" not in obj.columns:
        #    raise AttributeError("Must have 'latitude' and 'longitude'.")
        pass

    @classmethod
    def get_prefix(cls, record_class):
        return f"{record_class.__name__.lower()}."

    @classmethod
    def get_column(cls, record_class, field, prefix: str = ""):
        """Return a column name for the provided field and prefix.

        :param str field: the field name
        :param str prefix: column prefix, can be True, in this case retrieve
        """
        if prefix is True:
            prefix = cls.get_prefix(record_class)
        return (prefix or "") + field

    @classmethod
    def iter_record_fields(cls, record_class) -> set:
        """Return fields of this record class as a set."""
        return (
            k
            for k, v in vars(record_class).items()
            if k[0] != "_" and not callable(v)
        )

    def iter_fields(
        self, record_class, fields: [str] = None, prefix: str = ""
    ):
        """Return a dict of fields mapping to column names.

        :param records.Model record: record to extract columns from
        :param [str] fields: those fields only
        :param str prefix: if column names' prefix in dataframe.
        :return a dict of `{field: column}`
        """
        record_fields = self.iter_record_fields(record_class)
        if fields:
            fields = list(set(fields) & set(record_fields))
        else:
            fields = list(record_fields)

        if prefix is True:
            prefix = self.get_prefix(record_class)

        return (
            (field, col)
            for field, col in ((field, prefix + field) for field in fields)
            if col in self.df
        )

    def get_fields(self, *args, **kwargs):
        """Return a dict of fields mapping to column names.

        Same as `iter_fields()` except it returns a dict.
        """
        return dict(self.iter_fields(*args, **kwargs))

    def iter_records(self, record_class, fields=None, prefix="", rows=None):
        """Return an iterator returning each row as record instance.

        Extra attribute `df_index` is set to each instance,
        corresponding to dataframe's index.
        """
        fields = self.get_fields(record_class, fields, prefix)
        if rows is None:
            rows = self.df.iterrows()

        for index, row in rows:
            attrs = {field: row[col] for field, col in fields.items()}
            obj = record_class(**attrs)
            setattr(obj, "df_index", index)
            yield obj

    def get_records(self, *args, **kwargs):
        """Return result of `iter_records()` as a list."""
        return list(self.iter_records(*args, **kwargs))

    def extract(self, record_class, fields: [str] = None, prefix=""):
        """Return a new dataframe's accessor for the provided record_class."""
        fields = self.iter_fields(record_class, fields, prefix)
        fields = dict((c, f) for f, c in fields)
        df = self.df.loc[:, list(fields.keys())]
        return df.rename(columns=fields)

    _update_tag_col = "_record_updated"

    def update(self, df: pd.DataFrame, on: str = "pk"):
        """Update dataframe with provided one, using lookup key.

        Values are merged, NaN values filled with previous existing ones.

        :param pd.DataFrame df: insert values from this dataframe.
        :param str on: use this column to match values.
        :return self accessor.
        """
        if self._update_tag_col not in df.columns:
            df[self._update_tag_col] = True

        common_cols = tuple(col for col in df.columns if col in self.df)
        dd = pd.merge(
            self.df, df, on=on, how="outer", suffixes=["_", None], copy=False
        )
        for col in common_cols:
            dd[col] = dd[col].combine_first(dd.pop(col + "_"))
        self.df = dd
        return self

    def updated(self):
        """Return accessor to dataframe with only updated objects."""
        return self.df.loc[self.df[self._update_tag_col]]


@pd.api.extensions.register_dataframe_accessor("django")
class DjangoAccessor(RecordsAccessor):
    """This accessor provides function to work with Django. It assume that
    columns have the same name as fields.

    When working with ModelDataFrame, the `model` argument of the
    methods is not required.
    """

    @classmethod
    def get_prefix(cls, model_class):
        return f"{model_class._meta.label_lower}."

    @classmethod
    def iter_record_fields(cls, record_class) -> set:
        """Return iterator over fields of this record class as a set."""
        if hasattr(record_class, "_meta"):
            # this method avoid Django import
            return (field.name for field in record_class._meta.get_fields())
        return super(DjangoAccessor, cls).iter_record_fields(record_class)

    def save(self, model_class, fields=None, prefix="", updated=True):
        """Save rows as models into database, handling update and create.

        :param Model model_class: model class to instanciate.
        :param [str] fields: select which model fields to save
        :param str prefix: column prefix
        :param bool updated: if True only updated records will be saved
        :return a tuple of `[created_records], [updated_records]`.
        """
        if updated:
            self = self.updated()

        df = self.df
        pk = self.get_column(model_class, "pk", prefix)
        if pk not in df:
            df.insert(0, pk, None)

        to_create = df.loc[df[pk].isnull()]
        to_create = self.get_records(model_class, fields, prefix)

        to_update = df.loc[df[pk].notnull()]
        to_update = self.get_records(model_class, fields, prefix)

        model_class.objects.bulk_create(to_create)
        model_class.objects.bulk_update(to_update, fields.keys())

        # FIXME: check it is okay
        pks = {obj.df_index: obj.pk for obj in to_create}
        df.loc[pks.keys()] = pd.Series(pks.values())
        df.loc[self._update_tag_col] = False

        return to_create, to_update
