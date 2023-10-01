import pandas as pd

# from rest_framework import serializers


__all__ = ("RecordSet",)


class Relation:
    """Describe a relationship between two models."""

    source = None
    """Source RecordSet."""
    target = None
    """Destination RecordSet."""
    column = None
    """Column on the source record set referring to target's index."""

    def __init__(self, source, target, column, many=False):
        self.source = source
        self.target = target
        self.column = column
        self.many = many

    @classmethod
    def sort(self, relations):
        pass

    def resolve(self, df):
        pass


class RecordSet:
    """Dataframe container providing utils in order to add/store data."""

    df_class = pd.DataFrame
    """DataFrame to use as."""
    df = None
    """DataFrame holding data."""

    def __init__(self, df=None, columns=None, df_class=None, **df_kwargs):
        if df is None:
            df_class = df_class or self.df_class
            df = self.df_class(columns=columns, **df_kwargs)
        self.df = df

    @classmethod
    def from_serializer(cls, serializer_class, *args, columns=False, **kwargs):
        """Return RecordSet instance creating a dataframe based on the provided
        serializer's fields."""
        if not columns:
            columns = list(serializer_class._declared_fields.keys())
        return cls(*args, **kwargs)

    def update(self, df: pd.DataFrame, on: str = "pk") -> pd.DataFrame:
        """Update records with provided dataframe.

        Values are merged, NaN values filled with previous existing ones.

        :param pd.DataFrame df: insert values from this dataframe.
        :param str on: use this column to match values.
        :return current dataframe held by record set.
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

    def reset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reset pool items with the provided dataframe. Previous items are
        dropped.

        :param pd.DataFrame df: dataframe to set.
        :return current dataframe held by record set.
        """
        self.df = df
        return df

    def drop(self, *args, inplace=True, **kwargs):
        """Drop items from record set. Arguments are passd down to
        `pd.DataFrame.drop()` (inplace is True by default).

        :param *args: `pd.DataFrame.drop()`'s args.
        :param **kwargs: `pd.DataFrame.drop()`'s kwargs.
        :return current dataframe held by record set.
        """
        return self.df.drop(*args, inplace=inplace, **kwargs)

    def __repr__(self):
        return repr(self.df)
