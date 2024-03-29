"""Provide utility classes to work with panda dataframes."""
import pandas as pd


__all__ = ("RecordsAccessor", "DjangoAccessor")


@pd.api.extensions.register_dataframe_accessor("records")
class RecordsAccessor:
    """This accessor allows to manipulate."""

    pk_field = "pk"

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

        if self.pk_field not in fields and (prefix + self.pk_field) in self.df:
            fields.insert(0, self.pk_field)

        return (
            (field, col)
            for field, col in ((field, prefix + field) for field in fields)
            if col in self.df
        )

    def get_fields(self, record_class, fields=None, *args, **kwargs):
        """Return a dict of fields mapping to column names.

        Same as `iter_fields()` except that:
        - it returns a dict.
        - return fields as is if it is an instance of dict (without field
            verification).
        """
        # FIXME: This shortcut is really hacky
        if isinstance(fields, dict):
            return fields
        return dict(self.iter_fields(record_class, fields, *args, **kwargs))

    def iter_records(self, record_class, fields=None, prefix="", rows=None):
        """Return an iterator returning each row as record instance.

        Extra attribute `df_index` is set to each instance,
        corresponding to dataframe's index.
        """
        fields = self.get_fields(record_class, fields, prefix)
        if rows is None:
            rows = self.df.iterrows()

        for index, row in rows:
            nan = row.isnull()
            nan = {row.index[i] for i, v in enumerate(nan) if v}
            attrs = dict(
                (field, row[col])
                for field, col in fields.items()
                if col not in nan
            )
            obj = record_class(**attrs)
            setattr(obj, "df_index", index)
            yield obj

    def get_records(self, *args, **kwargs):
        """Return result of `iter_records()` as a list."""
        return list(self.iter_records(*args, **kwargs))

    def extract(self, record_class, fields: [str] = None, prefix=""):
        """Return a new dataframe for the provided record_class."""
        fields = self.iter_fields(record_class, fields, prefix)
        fields = dict((c, f) for f, c in fields)
        df = self.df.loc[:, list(fields.keys())]
        return df.rename(columns=fields)

    _update_col = "_record_updated"

    def update(self, df: pd.DataFrame, on: str = None, null_new: bool = True):
        """Update dataframe in place with provided one, using lookup key.

        Values are merged, NaN values filled with previous existing ones.

        :param pd.DataFrame df: insert values from this dataframe.
        :param str on: use this column to match values.
        :return new dataframe.
        """
        df[self._update_col] = True
        if on is None:
            on = self.pk_field

        common_cols = tuple(col for col in df.columns if col in self.df)
        if null_new:
            creates = df.loc[df[on].isnull()]
            df = df.loc[df[on].notnull()]
        else:
            creates = None

        common_cols = tuple(col for col in df.columns if col in self.df)
        dd = pd.merge(
            self.df, df, on=on, how="outer", suffixes=["_", None], copy=False
        )
        for col in common_cols:
            col_ = (col == on) and col or col + "_"
            dd[col] = dd[col].combine_first(dd.pop(col_))

        if null_new:
            # ignore_index should be safe a long as concat order is preserved
            dd = pd.concat([dd, creates], ignore_index=True)
        dd.loc[dd[self._update_col].isnull(), self._update_col] = False
        return dd

    def updated(self):
        """Return accessor to dataframe with only updated objects."""
        if self._update_col not in self.df:
            return self.df.iloc[0:0]
        return self.df.loc[self.df[self._update_col]]


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
            df = self.updated()
            self = df.django
        else:
            df = self.df

        pk = self.get_column(model_class, "pk", prefix)
        if pk not in df:
            df.insert(0, pk, None)

        fields = self.get_fields(model_class, fields, prefix)
        to_create = df.loc[df[pk].isnull()]
        to_update = df.loc[df[pk].notnull()]

        to_create = to_create.django.get_records(model_class, fields)
        to_update = to_update.django.get_records(model_class, fields)

        fields.pop(self.pk_field, None)
        model_class.objects.bulk_create(to_create)
        model_class.objects.bulk_update(to_update, fields.keys())

        # FIXME: check it is okay
        pks = {
            obj.df_index: getattr(obj, self.pk_field, None)
            for obj in to_create
        }
        df.loc[pks.keys(), self.pk_field] = pd.Series(pks.values())
        df.loc[self._update_col] = False

        return to_create, to_update
