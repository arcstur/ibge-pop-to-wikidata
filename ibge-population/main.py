import logging
import sys

from estimates import ESTIMATE_YEARS
from census import CENSUS_LIST
from wikidata import EstimateToQs
from wikidata import CensusToQs

def sort_key(cmd):
    qid = cmd.split("|")[0]
    year = cmd.split("|")[4][:5]
    return qid + year

def main():
    logging.basicConfig(level="INFO")
    result = "./result.qs"
    full_qs_list = []

    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what in ("estimates", "both"):
        eqs = EstimateToQs()
        for estimate in ESTIMATE_YEARS:
            estimate.download()
            full_qs_list.extend(eqs.to_qs_list(estimate))
    if what in ("census", "both"):
        cqs = CensusToQs()
        for c in CENSUS_LIST:
            full_qs_list.extend(cqs.to_qs_list(c))
    elif what not in ("census", "estimates", "both"):
        raise ValueError(f"argument must be 'estimates', 'census' or 'both', it's {what}")

    full_qs_list = sorted(full_qs_list, key=sort_key)
    with open(result, "w") as f:
        f.write("\n".join(full_qs_list) + "\n")
    logging.info(f"QuickStatements command written to {result}, sorted by QID")


if __name__ == "__main__":
    main()
