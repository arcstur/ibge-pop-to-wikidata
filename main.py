import logging

from estimates import ESTIMATE_YEARS
from wikidata import EstimateToQs

def main():
    logging.basicConfig(level="INFO")
    eqs = EstimateToQs()
    with open("result.qs", "w") as f:
        for estimate in ESTIMATE_YEARS:
            estimate.download()
            qs_list = eqs.to_qs_list(estimate)
            f.write("\n".join(qs_list) + "\n\n")
    logging.info("QuickStatements command written to ./result.qs")

if __name__ == "__main__":
    main()
