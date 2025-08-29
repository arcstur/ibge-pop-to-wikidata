import requests
from datetime import date

from estimates import Estimate


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


class EstimateToQs:
    P_POPULATION = "P1082"
    P_POINT_IN_TIME = "P585"
    P_METHOD = "P459"
    S_REF_URL = "S854"
    S_RETRIEVED = "S813"
    Q_ESTIMATION = "Q791801"

    def __init__(self):
        self.mapper = IbgeCodeToQid()
        self.mapper.load()

    def to_qs_list(self, estimate: Estimate):
        retrieved = f"+{date.today().isoformat()}T00:00:00Z/11"
        qs_list = []
        for code, population in estimate.populations().items():
            qid = self.mapper.qid(code)
            statement = [qid, self.P_POPULATION, str(population)]
            qualifiers = [
                self.P_POINT_IN_TIME,
                f"+{estimate.date}T00:00:00Z/11",
                self.P_METHOD,
                self.Q_ESTIMATION,
            ]
            reference = [
                self.S_REF_URL,
                f'"{estimate.url}"',
                self.S_RETRIEVED,
                retrieved,
            ]
            qs = "|".join(statement + qualifiers + reference)
            qs_list.append(qs)
        return qs_list
