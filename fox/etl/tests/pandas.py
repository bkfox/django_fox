import pandas as pd
import pytest

from fox.etl.pandas import RecordsAccessor, DjangoAccessor


def df_data(prefix=""):
    cols = [prefix + "a", prefix + "b", prefix + "c"]
    return {
        col: [i * j + j for j in range(0, 6)] for i, col in enumerate(cols)
    }


@pytest.fixture
def df():
    data = df_data("")
    return pd.DataFrame(data)


@pytest.fixture
def df_1():
    data = df_data("1.")
    return pd.DataFrame(data)


@pytest.fixture
def df_2():
    data = df_data("2.")
    return pd.DataFrame(data)


class SampleRecord:
    a = 0
    b = 1
    c = 2

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __eq__(self, other):
        return (self.a, self.b, self.c) == (other.a, other.b, other.c)

    _bar = None

    def foo(self):
        pass


class TestRecordsAccessor:
    def test_get_prefix(self):
        assert RecordsAccessor.get_prefix(SampleRecord) == "samplerecord."

    def test_get_column_custom_prefix(self):
        assert RecordsAccessor.get_column(SampleRecord, "a", "p.") == "p.a"

    def test_get_column_prefix_true(self):
        assert (
            RecordsAccessor.get_column(SampleRecord, "a", True)
            == "samplerecord.a"
        )

    def test_iter_record_fields(self):
        assert set(RecordsAccessor.iter_record_fields(SampleRecord)) == {
            "a",
            "b",
            "c",
        }

    # Note:
    # - `iter_fields` is tested through `get_fields`, since this one is a shortcut
    # to it.
    # - Same for `to_records`
    def test_get_fields_with_arg_fields(self, df):
        result = df.records.get_fields(SampleRecord, ["a", "b"])
        cols = ["a", "b"]
        assert result == {col: col for col in cols}

    def test_get_fields_with_arg_prefix(self, df):
        df = df.add_prefix("1.")
        result = df.records.get_fields(SampleRecord, prefix="1.")
        cols = df_data().keys()
        assert result == {col: "1." + col for col in cols}

    def test_get_fields_with_arg_prefix_true(self, df):
        prefix = df.records.get_prefix(SampleRecord)
        df = df.add_prefix(prefix)
        result = df.records.get_fields(SampleRecord, prefix=True)
        cols = df_data().keys()
        assert result == {col: prefix + col for col in cols}

    def test_get_fields_missing_col(self, df):
        df = df.drop(columns=["c"])
        result = df.records.get_fields(SampleRecord)
        assert set(result.keys()) == {"a", "b"}

    def test_get_records(self, df_1):
        records = df_1.records.get_records(SampleRecord, prefix="1.")
        expected = [
            SampleRecord(a=r[0], b=r[1], c=r[2]) for _, r in df_1.iterrows()
        ]
        assert records == expected

    def test_extract(self, df, df_1):
        result = df_1.records.extract(SampleRecord, prefix="1.")
        assert result.equals(df)

    def update(self, df_1):
        pass

    def updated(self, df_1):
        pass


class TestDjangoAccessor:
    cl_ = DjangoAccessor

    def get_prefix(self, df_2):
        pass

    def iter_record_fields(self, df_2):
        pass

    def save(self, df_2):
        pass
