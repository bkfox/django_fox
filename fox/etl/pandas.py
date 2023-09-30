import pandas as pd


__all__ = ("ModelDataFrame", "DjangoAccessor")


class ModelDataFrame(pd.DataFrame):
    _metadata = ["model"]

    def __init__(
        self, data=None, index=None, columns=None, *args, model=None, **kwargs
    ):
        self.model = model
        if not columns:
            columns = [field.name for field in model._meta.get_fields()]
        super().__init__(data, index, columns, *args, **kwargs)

    @property
    def _constructor(self):
        return ModelDataFrame


@pd.api.extensions.register_dataframe_accessor("django")
class DjangoAccessor:
    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        # if "latitude" not in obj.columns or "longitude" not in obj.columns:
        #    raise AttributeError("Must have 'latitude' and 'longitude'.")
        pass

    def yield_models(self, model=None, columns=None):
        model = self._get_model(model)
        columns = self._get_columns(model, columns)

        for index, row in self._obj.iterrows():
            attrs = {col: row[col] for col in columns if not row[col].isnull()}
            obj = model(**attrs)
            setattr(obj, "df_index", index)
            yield obj

    def save(self, model=None, columns=None):
        model = self._get_model(model)
        columns = self._get_columns(model, columns)

        to_create = self._obj.loc[self._obj["pk"].isnull()]
        to_update = self._obj.loc[self._obj["pk"].notnull()]
        to_create = list(self.yield_models(model, columns))
        to_update = list(self.yield_models(model, columns))

        model.objects.bulk_create(to_create)
        model.objects.bulk_update(to_update, columns)

        pks = {obj.df_index: obj.pk for obj in to_create}
        self._obj.loc[pks.keys()] = pd.Series(pks.values())

        return to_create, to_update

    def _get_model(self, model=None):
        if model is None:
            if (
                not isinstance(self._obj, ModelDataFrame)
                or not self._obj.model
            ):
                raise ValueError(
                    "No model provided nor dataframe is an instance "
                    "of ModelDataFrame"
                )
            model = self._obj.model
        return model

    def _get_columns(self, model, columns):
        fields = tuple(
            field.name
            for field in model._meta.get_fields()
            if field.name in self._obj
        )
        if columns:
            # filter out missing non field columns
            columns = list(set(columns) & set(fields))
        return columns
