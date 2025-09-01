from datetime import date

import requests
import pandas as pd

from estimates import Estimate
from census import Census


class IbgeCodeToQid:
    ENDPOINT = "https://query.wikidata.org/sparql"
    QUERY = """
    SELECT ?item ?code WHERE {
        ?item wdt:P1585 ?code.
    }
    """
    HEADERS = {
        "Accept": "application/json",
        "User-Agent": "ibge-pop-to-wikidata (https://github.com/arcstur/ibge-pop-to-wikidata)",
    }

    def __init__(self):
        pass

    def load(self):
        params = {"query": self.QUERY}
        response = requests.get(self.ENDPOINT, params=params, headers=self.HEADERS)
        response.raise_for_status()
        data = response.json()
        mapping = {}
        for row in data["results"]["bindings"]:
            qid = row["item"]["value"].split("/")[-1]
            code = row["code"]["value"]
            mapping[code] = qid
        self.mapping = mapping

    def qid(self, code):
        return self.mapping[str(code)]


P_POPULATION = "P1082"
P_POINT_IN_TIME = "P585"
P_METHOD = "P459"
S_REF_URL = "S854"
S_RETRIEVED = "S813"


class EstimateToQs:
    Q_ESTIMATION = "Q791801"

    def __init__(self):
        self.mapper = IbgeCodeToQid()
        self.mapper.load()

    def to_qs_list(self, estimate: Estimate):
        retrieved = f"+{date.today().isoformat()}T00:00:00Z/11"
        qs_list = []
        for code, population in estimate.populations().items():
            qid = self.mapper.qid(code)
            statement = [qid, P_POPULATION, str(population)]
            qualifiers = [
                P_POINT_IN_TIME,
                f"+{estimate.date}T00:00:00Z/11",
                P_METHOD,
                self.Q_ESTIMATION,
            ]
            reference = [
                S_REF_URL,
                f'"{estimate.url}"',
                S_RETRIEVED,
                retrieved,
            ]
            qs = "|".join(statement + qualifiers + reference)
            qs_list.append(qs)
        return qs_list


class CensusToQs:
    Q_CENSUS = "Q39825"

    def __init__(self):
        self.mapper = IbgeCodeToQid()
        self.mapper.load()

    def to_qs_list(self, census: Census):
        retrieved = f"+{date.today().isoformat()}T00:00:00Z/11"
        qs_list = []
        for code, populations_per_year in census.populations_per_year().items():
            qid = self.mapper.qid(code)
            for year, population in populations_per_year.items():
                if pd.isna(population) or not population:
                    continue
                statement = [qid, P_POPULATION, str(population)]
                qualifiers = [
                    P_POINT_IN_TIME,
                    f"+{year}-07-01T00:00:00Z/9",  # year precision
                    P_METHOD,
                    self.Q_CENSUS,
                ]
                reference = [
                    S_REF_URL,
                    f'"{census.url}"',
                    S_RETRIEVED,
                    retrieved,
                ]
                qs = "|".join(statement + qualifiers + reference)
                qs_list.append(qs)
        return qs_list
