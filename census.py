import pandas as pd


class Census:
    def __init__(self):
        self.url = "https://sidra.ibge.gov.br/tabela/202"
        self.path = "./data/census/tabela202.xlsx"
        self.sheet_name = "Tabela"
        self.skipfooter = 1
        self.skiprows = 4
        self.ignore_codes = [
            "2399903" # not a municipality anymore
        ]

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
                na_values="...",
            )
            rename_columns = {
                "Unnamed: 0": "code",
                "Total": "1970",
                "Total.1": "1980",
                "Total.2": "1991",
                "Total.3": "2000",
                "Total.4": "2010",
            }
            df = df.rename(columns=rename_columns)
            for col in rename_columns.values():
                assert col in df.columns, f"{col} not present in columns: {df.columns}"
            df = df[df.columns[df.columns.isin(rename_columns.values())]]
            self._df = df
        return self._df.copy()

    def populations_per_year(self):
        df = self.df()
        df = df.loc[~df["code"].isin(self.ignore_codes)]
        return df.set_index("code").to_dict(orient="index")


# we only have one...
CENSUS_1970_2010 = Census()
