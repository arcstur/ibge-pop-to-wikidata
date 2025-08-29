import io
import os
import zipfile
import logging
import requests
import pandas as pd


class Estimate:
    def __init__(
        self,
        date,
        url,
        skiprows=1,
        skipfooter=2,
        sheet_name="Municípios",
        fix_codes=None,
        extension="ods",
    ):
        self.date = date
        self.url = url
        self.skiprows = skiprows
        self.skipfooter = skipfooter
        self.sheet_name = sheet_name
        self.fix_codes = fix_codes
        self.extension = extension

    def path(self):
        return f"./data/estimate/{self.date}.{self.extension}"

    def download(self):
        if os.path.exists(self.path()):
            logging.info(f"already downloaded: {self.path()}")
            return
        logging.info(f"downloading {self.url}")
        response = requests.get(self.url)
        if self.url.endswith("zip"):
            self.unzip(response.content)
        else:
            os.makedirs("./data/estimate", exist_ok=True)
            with open(self.path(), "wb") as f:
                f.write(response.content)

    def unzip(self, content):
        zip_file = io.BytesIO(content)
        with zipfile.ZipFile(zip_file, mode="r") as zip:
            for name in zip.namelist():
                if name.endswith(self.extension):
                    logging.info(f"extracting: {name}")
                    with zip.open(name, mode="r") as f_read:
                        with open(self.path(), "wb") as f_write:
                            f_write.write(f_read.read())
                            break

    def df(self):
        if not hasattr(self, "_df"):
            df = pd.read_excel(
                self.path(),
                dtype=str,
                skiprows=self.skiprows,
                skipfooter=self.skipfooter,
                sheet_name=self.sheet_name,
                thousands=",",
                decimal=".",
            )
            df = df.rename(
                columns={
                    " POPULAÇÃO ESTIMADA ": "POPULAÇÃO ESTIMADA",
                    "ESTIMADA": "POPULAÇÃO ESTIMADA",
                    "01.07.2008": "POPULAÇÃO ESTIMADA",
                    "Unnamed: 4": "POPULAÇÃO ESTIMADA",
                    "U.F.": "COD. UF",
                    "COD": "COD. UF",
                    "COD.1": "COD. MUNIC",
                    "MUNIC": "COD. MUNIC",
                }
            )
            columns = ("COD. UF", "COD. MUNIC", "POPULAÇÃO ESTIMADA")
            for col in columns:
                assert col in df.columns, f"{col} not present in columns: {df.columns}"
            df = df[df.columns[df.columns.isin(columns)]]
            df = df.dropna(subset=["POPULAÇÃO ESTIMADA"])
            df["POPULAÇÃO ESTIMADA"] = (
                df["POPULAÇÃO ESTIMADA"]
                .str.replace(r"\(\d+\)", "", regex=True)  # used for footnotes
                .str.replace(r"\(?\*\)?\S*$", "", regex=True)  # used for footnotes
                .str.replace(r"^\S*\(?\*\)?\S*", "", regex=True)  # used for footnotes
                .str.replace(",", "")  # remove all decimal/thousand notation
                .str.replace(".", "")
                .astype(int)
            )
            self._df = df
        return self._df.copy()

    def populations(self):
        if not hasattr(self, "_pops"):
            df = self.df()
            df = df.dropna(subset=["COD. MUNIC"])
            df["COD. MUNIC"] = df["COD. MUNIC"].str.rjust(5, fillchar="0")
            df["code"] = df["COD. UF"] + df["COD. MUNIC"]
            if self.fix_codes:
                df["code"] = df["code"].replace(self.fix_codes)
            pops = df.set_index("code")["POPULAÇÃO ESTIMADA"].to_dict()
            assert len(pops.keys()) == len(df), "some municipality went missing?"
            self._pops = pops
            logging.info(
                f"loaded {self.total_municipalities()} municipalities from {self.date}, total population = {self.total_population()}"
            )
        return self._pops

    def total_municipalities(self):
        return len(self.populations().keys())

    def total_population(self):
        return sum(self.populations().values())


ESTIMATE_YEARS = [
    # Data at: <https://ftp.ibge.gov.br/Estimativas_de_Populacao/>
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
        date="2018-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2018/estimativa_dou_2018_20181019.ods",
    ),
    Estimate(
        date="2017-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2017/estimativa_dou_2017.ods",
    ),
    Estimate(
        date="2016-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2016/estimativa_dou_2016_20160913.ods",
        skiprows=2,
    ),
    Estimate(
        date="2015-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2015/estimativa_dou_2015_20150915.ods",
        skiprows=2,
    ),
    Estimate(
        date="2014-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2014/estimativa_dou_2014_ods.zip",
        skiprows=2,
    ),
    Estimate(
        date="2013-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2013/estimativa_2013_dou_ods.zip",
        skiprows=2,
    ),
    Estimate(
        date="2012-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2012/estimativa_2012_DOU_28_08_2012_ods.zip",
        skiprows=2,
        sheet_name="TAB_DOU_Municípios_(internet)",
    ),
    Estimate(
        date="2011-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2011/POP2011_DOU.zip",
        skiprows=2,
        sheet_name="MUNICÍPIOS",
        extension="xls",
    ),
    Estimate(
        date="2009-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2009/UF_Municipio.zip",
        skiprows=4,
        sheet_name="MUNICÍPIOS",
        extension="xls",
    ),
    Estimate(
        date="2008-07-01",
        url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2008/UF_Municipio.zip",
        skiprows=4,
        sheet_name="POP08DOU",
        extension="xls",
    ),
    # After 2006, municipality codes change! :(
    # Estimate(
    #     date="2006-07-01",
    #     url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2006/UF_Municipio.zip",
    #     skiprows=4,
    #     sheet_name="P5564TCU",
    #     extension="xls",
    # ),
    # Estimate(
    #     date="1999-07-01",
    #     url="https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_1999/estimativa_populacao_1999_ods.zip",
    #     skiprows=2,
    #     sheet_name="Tab_Muniipios",
    #     fix_codes={
    #         "1100001": "1100015", # Alta Floresta D'Oeste
    #         "1100015": "1100155", # Ouro Preto do Oeste
    #         "1100155": "1101559", # Teixeirópolis
    #         # and many more....
    #     }
    # ),
]
