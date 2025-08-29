import pandas as pd


class Census:
    def __init__(self, url, path, skiprows, rename_columns, keep_columns, ignore_codes=[]):
        self.url = url
        self.path = path
        self.skiprows = skiprows
        self.rename_columns = rename_columns
        self.keep_columns = keep_columns
        self.ignore_codes = ignore_codes
        self.sheet_name = "Tabela"
        self.skipfooter = 1

    def df(self):
        if not hasattr(self, "_df"):
            df = pd.read_excel(
                self.path,
                dtype=str,
                skiprows=self.skiprows,
                skipfooter=self.skipfooter,
                sheet_name=self.sheet_name,
                thousands=",",
                decimal=".",
                na_values=["...", "-"],
            )
            df = df.rename(columns=self.rename_columns)
            for col in self.keep_columns:
                assert col in df.columns, f"{col} not present in columns: {df.columns}"
            df = df[df.columns[df.columns.isin(self.keep_columns)]]
            self._df = df
        return self._df.copy()

    def populations_per_year(self):
        df = self.df()
        if self.ignore_codes:
            df = df.loc[~df["code"].isin(self.ignore_codes)]
        return df.set_index("code").to_dict(orient="index")


# we only have one...
CENSUS_LIST = [
    Census(
        url="https://sidra.ibge.gov.br/tabela/202",
        path="./data/census/tabela202.xlsx",
        skiprows=4,
        rename_columns={
            "Unnamed: 0": "code",
            "Total": "1970",
            "Total.1": "1980",
            "Total.2": "1991",
            "Total.3": "2000",
            "Total.4": "2010",
        },
        keep_columns=[
            "code",
            "1970",
            "1980",
            "1991",
            "2000",
            "2010",
        ],
        ignore_codes = [
            "2399903"  # not a municipality anymore
        ],
    ),
    Census(
        url="https://sidra.ibge.gov.br/tabela/1287",
        path="./data/census/tabela1287.xlsx",
        skiprows=3,
        rename_columns={
            "Unnamed: 0": "code",
        },
        keep_columns=[
            "code",
            "1872",
            "1890",
            "1900",
            "1920",
            "1940",
            "1950",
            "1960",
            "1970",
            "1980",
            "1991",
            "2000",
            "2010",
        ],
    ),
]
