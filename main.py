import logging

from estimates import ESTIMATE_YEARS
from wikidata import EstimateToQs

def main():
    logging.basicConfig(level="INFO")
    eqs = EstimateToQs()
    full_qs_list = []
    for estimate in ESTIMATE_YEARS:
        estimate.download()
        full_qs_list.extend(eqs.to_qs_list(estimate))
    full_qs_list = sorted(full_qs_list)
    with open("result.qs", "w") as f:
        f.write("\n".join(full_qs_list) + "\n")
    logging.info("QuickStatements command written to ./result.qs, sorted by QID")

if __name__ == "__main__":
    main()
