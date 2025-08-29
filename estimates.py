import io
import os
import zipfile
import logging
import requests
import pandas as pd


class Estimate:
    def __init__(self, date, url, skiprows=1, skipfooter=2, sheet_name="Municípios"):
        self.date = date
        self.url = url
        self.skiprows = skiprows
        self.skipfooter = skipfooter
        self.sheet_name = sheet_name

    def path(self):
        return f"./data/estimate/{self.date}.ods"

    def download(self):
        if os.path.exists(self.path()):
            logging.info(f"already downloaded: {self.path()}")
            return
        logging.info(f"downloading {self.url}")
        response = requests.get(self.url)
        if self.url.endswith("zip"):
            self.unzip(response.content)
        else:
            with open(self.path(), "wb") as f:
                f.write(response.content)

    def unzip(self, content):
        zip_file = io.BytesIO(content)
        with zipfile.ZipFile(zip_file, mode="r") as zip:
            for name in zip.namelist():
                if name.endswith("ods"):
                    with zip.open(name, mode="r") as f_read:
                        with open(self.path(), "wb") as f_write:
                            f_write.write(f_read.read())
                            break

    def df(self):
        if not hasattr(self, "_df"):
            df = pd.read_excel(
                self.path(),
                engine="odf",
                dtype=str,
                skiprows=self.skiprows,
                skipfooter=self.skipfooter,
                sheet_name=self.sheet_name,
                thousands=",",
                decimal=".",
            )
            df = df.rename(columns={" POPULAÇÃO ESTIMADA ": "POPULAÇÃO ESTIMADA"})
            columns = ("COD. UF", "COD. MUNIC", "POPULAÇÃO ESTIMADA")
            for col in columns:
                assert col in df.columns, f"{col} not present in columns"
            df = df[[*columns]]
            df = df.dropna(subset=["POPULAÇÃO ESTIMADA"])
            df["POPULAÇÃO ESTIMADA"] = (
                df["POPULAÇÃO ESTIMADA"]
                .str.replace(r"\(\d+\)", "", regex=True) # used for footnotes
                .str.replace("(*)", "")  # used for footnotes
                .str.replace(",", "")  # remove all decimal/thousand notation
                .str.replace(".", "")
                .astype(int)
            )
            self._df = df
        return self._df

    def populations(self):
        if not hasattr(self, "_pops"):
            df = self.df()
            df = df.dropna(subset=["COD. MUNIC"])
            df["code"] = df["COD. UF"].astype(str) + df["COD. MUNIC"].astype(str)
            pops = df.set_index("code")["POPULAÇÃO ESTIMADA"].to_dict()
            assert len(pops.keys()) == len(df), "some municipality went missing?"
            self._pops = pops
        return self._pops

    def total_municipalities(self):
        return len(self.populations().keys())

    def total_population(self):
        return sum(self.populations().values())


ESTIMATE_YEARS = [
    Estimate(
        date="2025-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/estimativa_dou_2025.ods",
    ),
    Estimate(
        date="2024-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2024/estimativa_dou_2024.ods",
        sheet_name="MUNICÍPIOS",
    ),
    Estimate(
        date="2021-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2021/estimativa_dou_2021.ods",
    ),
    Estimate(
        date="2020-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2020/estimativa_dou_2020.ods",
    ),
    Estimate(
        date="2019-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2019/estimativa_dou_2019.ods",
    ),
    Estimate(
        date="2015-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2015/estimativa_dou_2015_20150915.ods",
        skiprows=2,
    ),
    Estimate(
        date="1999-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_1999/estimativa_populacao_1999_ods.zip",
        skiprows=2,
        sheet_name="Tab_Muniipios",
    ),
]


def download_all():
    os.makedirs("./data/estimate", exist_ok=True)
    for estimate in ESTIMATE_YEARS:
        estimate.download()
        logging.info(
            f"loaded {estimate.total_municipalities()} municipalities from {estimate.date}, total population = {estimate.total_population()}"
        )
