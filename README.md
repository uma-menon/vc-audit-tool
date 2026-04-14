# VC Audit Tool

Estimates the fair value of a private VC portfolio company using **Comparable Company Analysis (Comps)**.

## Methodology

1. Retrieve publicly traded peer companies for the portfolio company's sector.
2. Select up to 6 of the most relevant peers.
3. Calculate each peer's EV/Revenue multiple.
4. Take the median of EV/Revenue multiples of the peer group.
5. Apply that median to the portfolio company's revenue to receive a point estimate.
6. Apply a ±20% margin to produce a fair value range.

Peer data is hardcoded in comps.py and clearly labelled as mock. Replace the _get_peers function with a real data source — no other code needs to change.

## Setup

```zsh
pip install pydantic
```

## Usage

**From a JSON file:**
```zsh
python3 main.py --input data/sample_basisai.json
python3 main.py --input data/sample_inflo.json
```

**Inline:**
```zsh
python3 main.py --company "Basis AI" --sector saas --revenue 10000000
```

**To save a JSON report instead of terminal output:**
```zsh
python3 main.py --input data/sample_inflo.json --output report.json
```

Notes: 
`--company` must be used with `--sector` and `--revenue`
`--sector` must be one of `saas`, `fintech`, `healthcare`, `ecommerce`, `marketplace`, `deeptech`, `other` 

**Sample JSON input:**
```json
{
  "name": "Basis AI",
  "sector": "saas",
  "revenue": 10000000
}
```

## Output
Every run prints to stdout:

- **Estimated fair value** — point estimate and ±20% range
- **Key inputs & assumptions** — revenue, EV/Revenue multiple used, EV/Revenue multiple source
- **Data sources** — provider label (Mock public comps dataset by default) and peer company names/tickers
- **Narrative** — plain English explanation of how the estimate was derived
- **Audit trail** — numbered log of every decision made during the run

With `--output`, the same information is written as structured JSON.

## Project structure

```
.
├── main.py           # CLI entry point — parses args, validates input, orchestrates
├── comps.py          # Peer data, Pydantic models, and valuation engine
└── formatter.py      # Terminal and JSON output rendering
```

## Design decisions & tradeoffs

- **Median over mean.** Less sensitive to outliers in a small peer set (3–6 companies).
- **±20% range.** Reflects natural spread across the peer group and uncertainty in the inputs. Configurable via `RANGE_BAND` in `comps.py`.
- **Audit trail as a plain list.** The trail is a list of dicts built up during the valuation run and rendered by `formatter.py` at the end — no separate class or module needed.
- **Pydantic only at the boundary.** `PortfolioCompany` and `PublicComp` are Pydantic models because they validate external input. Everything downstream passes plain dicts — no unnecessary type machinery in the middle of the pipeline.

## Potential improvements

- Replace `get_peers` in `comps.py` with a live data provider (ex. Yahoo Finance).
- Add peer filtering by size, growth rate, or other factors to improve comparability beyond sector alone.
- Support the other suggested methodologies (DCF, Last Round). For example, via a --method flag.
- Make the tool accessible via a web frontend by adding a FastAPI backend, and potentially add results visualization.
