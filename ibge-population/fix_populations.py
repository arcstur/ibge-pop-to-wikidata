import requests
import logging
from typing import Optional

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "arcstur/wikidata-scripts (https://github.com/arcstur/wikidata-scripts)",
}

with open("result.qs", "r") as f:
    ALL_INITIAL_COMMANDS = f.read().splitlines()


class AllCitiesQid:
    ENDPOINT = "https://query.wikidata.org/sparql"
    QUERY = """
    SELECT ?item ?code WHERE {
        ?item wdt:P1585 ?code.
    }
    """

    def qids(self):
        params = {"query": self.QUERY}
        response = requests.get(self.ENDPOINT, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        qids = []
        for row in data["results"]["bindings"]:
            qid = row["item"]["value"].split("/")[-1]
            qids.append(qid)
        return qids


class JsonQid:
    P_POPULATION = "P1082"
    P_POINT_IN_TIME = "P585"
    P_METHOD = "P459"
    Q_ESTIMATION = "Q791801"
    Q_CENSUS = "Q39825"
    EDIT_SUMMARY = "fixing duplicate P1082 statements and P585 qualifiers"

    def __init__(self, qid):
        self.qid = qid
        base_endpoint = (
            "https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/"
        )
        self.endpoint = base_endpoint + qid
        self.initial_commands = []
        self.final_commands = []
        # load initial
        for cmd in ALL_INITIAL_COMMANDS:
            if qid in cmd.split("|")[0]:
                self.initial_commands.append(cmd)
        # load final
        res = requests.get(self.endpoint, headers=HEADERS)
        res.raise_for_status()
        entity = res.json()
        statements = entity["statements"][self.P_POPULATION]
        for st in statements:
            if self.p585_count(st) > 1:
                self.handle_duplicate_p585(st)
        # add edit summary or print ok
        if len(self.final_commands) == 0:
            logging.info(f"[{self.qid}] OK!")
        else:
            self.final_commands[-1] += f"|/* {self.EDIT_SUMMARY} */"

    def append_command(self, cmd):
        self.final_commands.append(cmd)
        logging.info(cmd)

    def p585_count(self, st):
        p585_count = 0
        for qual in st["qualifiers"]:
            pid = qual["property"]["id"]
            if pid == self.P_POINT_IN_TIME:
                p585_count += 1
        return p585_count

    def handle_duplicate_p585(self, st):
        if self.p585_count(st) == 2:
            idx_to_drop = None
            idxs = []
            for i, qual in enumerate(st["qualifiers"]):
                pid = qual["property"]["id"]
                if pid == self.P_POINT_IN_TIME:
                    idxs.append(i)
            assert len(idxs) == 2
            idx_to_drop = self.idx_to_drop(st, idxs[0], idxs[1])
            if idx_to_drop is not None:
                qual = st["qualifiers"][idx_to_drop]
                time = qual["value"]["content"]["time"]
                precision = qual["value"]["content"]["precision"]
                self.append_command(
                    "|".join(
                        [
                            "REMOVE_QUAL",
                            self.qid,
                            self.P_POPULATION,
                            st["value"]["content"]["amount"],
                            self.P_POINT_IN_TIME,
                            time + "/" + str(precision),
                        ]
                    )
                )
                return
        # more complex situation, 2 complex or 3+ years
        # remove current statement and redo for each year
        p585_qualifiers = []
        for qual in st["qualifiers"]:
            pid = qual["property"]["id"]
            if pid == self.P_POINT_IN_TIME:
                p585_qualifiers.append(qual)
        self.append_command(
            "|".join(
                [
                    f"-{self.qid}",
                    self.P_POPULATION,
                    st["value"]["content"]["amount"],
                ]
            )
        )
        _years = list(set([q["value"]["content"]["time"][:5] for q in p585_qualifiers]))
        years_left = {y: True for y in _years}
        logging.info(f"removing statement above with years: {_years}")
        # special case: census with 2000, 2010 + other values
        if "+2010" in years_left.keys() and "+2000" in years_left.keys():
            logging.info(
                "2000 census already handled in other statement, removing it from here"
            )
            years_left.pop("+2000")
        # special case: we don't have 2022 census data in result.qs
        if "+2022" in years_left.keys() and len(years_left.keys()) == 2:
            self.final_commands.pop(-1)
            years_left.pop("+2022")
            other_year = list(years_left.keys())[0]
            cmd = None
            for initial in self.initial_commands:
                year = initial.split("|")[4][:5]
                if year == other_year:
                    cmd = initial
                    break
            if cmd is None:
                raise ValueError(f"{other_year} not found")
            parts = cmd.split("|")
            self.append_command("|".join(["REMOVE_QUAL", *parts[0:5]]))
            self.append_command("|".join(["REMOVE_QUAL", *parts[0:3], *parts[5:7]]))
            self.append_command("|".join(["REMOVE_REF", *parts[0:3], *parts[7:9]]))
            self.append_command(
                "|".join(
                    ["REMOVE_REF", *parts[0:3], parts[9], "+2025-08-29T00:00:00Z/11"]
                )
            )
            self.append_command(initial)
            years_left.pop(other_year)
        for initial in self.initial_commands:
            year = initial.split("|")[4][:5]
            if year in years_left.keys():
                self.append_command(initial)
                years_left.pop(year)
        if len(years_left) > 0:
            raise ValueError(f"missing qs commands for years: {years_left}")

    def idx_to_drop(self, st, idx_old, idx_new) -> Optional[int]:
        qualifiers = st["qualifiers"]
        qual1 = qualifiers[idx_old]
        qual2 = qualifiers[idx_new]
        value1 = qual1["value"]["content"]
        value2 = qual2["value"]["content"]
        year1 = value1["time"][:5]
        year2 = value2["time"][:5]
        if year1 == year2:
            # years are the same
            if value1["precision"] < value2["precision"]:
                logging.debug(f"[{self.qid}] keep NEWEST, more precision")
                return idx_old
            else:
                # equal precisions, equal value, return newest
                # or idx_old has greater precision
                logging.debug(f"[{self.qid}] keep OLDEST, more or equal precision")
                return idx_new
        else:
            if self.only_census(st) and year1 == "+2000" and year2 == "+2010":
                # there's a lot of statements for census 2010 with a first qualifier = 2000, which can be removed
                logging.debug(f"[{self.qid}] [CENSUS] keep 2010, oldest wrong (2010)")
                return idx_old
        return None

    def only_census(self, st) -> bool:
        methods = []
        for qual in st["qualifiers"]:
            if qual["property"]["id"] == self.P_METHOD:
                methods.append(qual["value"]["content"])
        return list(set(methods)) == [self.Q_CENSUS]


def main():
    qids = AllCitiesQid().qids()
    with open("fix_populations.qs", "w") as f:
        for qid in qids:
            for cmd in JsonQid(qid).final_commands:
                f.write(cmd + "\n")


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    main()
