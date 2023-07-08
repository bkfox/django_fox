import pandas as pd

# from rest_framework import serializers


__all__ = ("RecordSet",)


class RecordSet:
    """Dataframe container providing utils in order to add/store data."""

    df = None
    """DataFrame holding data."""

    def __init__(self, df=None, columns=None, **df_kwargs):
        self.df = df or pd.DataFrame(columns=columns, **df_kwargs)

    @classmethod
    def from_serializer(cls, serializer_class, *args, columns=False, **kwargs):
        if not columns:
            columns = list(serializer_class._declared_fields.keys())
        return cls(*args, **kwargs)

    def update(self, df, on="pk"):
        """Update records with provided dataframe.

        Values are merge, NaN values filled with previous existing ones.
        """
        if "_unsaved" not in df.columns:
            df["_unsaved"] = True
        common_cols = tuple(col for col in df.columns if col in self.df)
        dd = pd.merge(
            self.df, df, on=on, how="outer", suffixes=["_", None], copy=False
        )
        for col in common_cols:
            dd[col] = dd[col].combine_first(dd.pop(col + "_"))
        self.df = dd
