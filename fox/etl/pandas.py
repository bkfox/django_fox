import pandas as pd


__all__ = ("ModelDataFrame", "DjangoAccessor")


class ModelDataFrame(pd.DataFrame):
    """DataFrame providing capabilities to work with Django models."""

    _metadata = ["model"]

    def __init__(
        self, data=None, index=None, columns=None, *args, model=None, **kwargs
    ):
        self.model = model
        if not columns:
            columns = [field.name for field in model._meta.get_fields()]
        if "pk" not in columns:
            columns.append("pk")

        super().__init__(data, index, columns, *args, **kwargs)

    @property
    def _constructor(self):
        return ModelDataFrame


@pd.api.extensions.register_dataframe_accessor("django")
class DjangoAccessor:
    """This accessor provides tools to work with Django. It assume that columns
    have the same name as fields.

    When working with ModelDataFrame, the `model` argument of the
    methods is not required.
    """

    def __init__(self, df):
        self._validate(df)
        self.df = df

    @staticmethod
    def _validate(obj):
        # if "latitude" not in obj.columns or "longitude" not in obj.columns:
        #    raise AttributeError("Must have 'latitude' and 'longitude'.")
        pass

    def to_models(self, model=None, columns=None):
        """Yield instances of model for each row of the DataFrame. `model` is
        not required for ModelDataFrame instances.

        :param Model model: model to instanciate.
        :param [str] columns: initialize only with thoses columns' values.
        :yield Model models based on rows' values.
        """
        model = self._get_model(model)
        columns = self._get_columns(model, columns)

        for index, row in self.df.iterrows():
            attrs = {col: row[col] for col in columns if not row[col].isnull()}
            obj = model(**attrs)
            setattr(obj, "df_index", index)
            yield obj

    def save(self, model=None, columns=None):
        """Save rows as models into database, handling update and create.

        :param Model model: model to instanciate.
        :param [str] columns: initialize models only with thoses columns' values.
        :return a tuple of `[created_models], [updated_models]`.
        """
        model = self._get_model(model)
        columns = self._get_columns(model, columns)

        if "pk" not in self.df:
            self.df.insert(0, "pk", None)

        # FIXME: "pk" can be missing
        to_create = self.df.loc[self.df["pk"].isnull()]
        to_update = self.df.loc[self.df["pk"].notnull()]
        to_create = list(self.to_models(model, columns))
        to_update = list(self.to_models(model, columns))

        model.objects.bulk_create(to_create)
        model.objects.bulk_update(to_update, columns)

        pks = {obj.df_index: obj.pk for obj in to_create}
        self.df.loc[pks.keys()] = pd.Series(pks.values())

        return to_create, to_update

    def _get_model(self, model=None):
        if model is None:
            if not isinstance(self.df, ModelDataFrame) or not self.df.model:
                raise ValueError(
                    "No model provided nor dataframe is an instance "
                    "of ModelDataFrame"
                )
            model = self.df.model
        return model

    def _get_columns(self, model, columns):
        fields = tuple(
            field.name
            for field in model._meta.get_fields()
            if field.name in self.df
        )
        if columns:
            # filter out missing non field columns
            columns = list(set(columns) & set(fields))
        return columns
