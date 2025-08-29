import logging
import sys

from estimates import ESTIMATE_YEARS
from census import CENSUS_1970_2010
from wikidata import EstimateToQs
from wikidata import CensusToQs


def main():
    logging.basicConfig(level="INFO")
    result = "./result.qs"
    full_qs_list = []

    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "estimates":
        eqs = EstimateToQs()
        for estimate in ESTIMATE_YEARS:
            estimate.download()
            full_qs_list.extend(eqs.to_qs_list(estimate))
        full_qs_list = sorted(full_qs_list)
    elif what == "census":
        cqs = CensusToQs()
        c = CENSUS_1970_2010
        full_qs_list.extend(cqs.to_qs_list(c))
    else:
        raise ValueError(f"argument must be 'estimates' or 'census', it's {what}")

    with open(result, "w") as f:
        f.write("\n".join(full_qs_list) + "\n")
    logging.info(f"QuickStatements command written to {result}, sorted by QID")


if __name__ == "__main__":
    main()
