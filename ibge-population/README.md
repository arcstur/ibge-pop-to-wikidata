# ibge-pop-to-wikidata

IBGE population data to Wikidata of Brazilian cities.

## Running

```bash
# to obtain QS for estimates
python3 main.py estimates

# to obtain QS for census
python3 main.py census
```

## Fixing

So some mistakes happened (duplicate qualifiers for example). The `fix_populations` script was made to fix them.
