#!/usr/bin/env python3
'''
Usage:
  python main.py --input data/sample_basisai.json
  python main.py --company "Basis AI" --sector saas --revenue 10000000
  python main.py --input data/sample_inflo.json --output report.json
'''

import argparse
import json
import sys
from pathlib import Path
from comps import PortfolioCompany, run_comps_valuation
from formatter import render_terminal, render_json


def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser()

    input_group=parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input","-i",)
    input_group.add_argument("--company",)

    parser.add_argument("--sector",choices=["saas", "fintech", "healthcare", "ecommerce", "marketplace", "deeptech", "other"])
    parser.add_argument("--revenue",type=float)
    parser.add_argument("--notes",type=str)
    parser.add_argument("--output", "-o",)

    return parser


def main() -> None:
    parser=build_parser()
    args=parser.parse_args()

    #Load/validate inputs
    try:
        if args.input: raw=json.loads(Path(args.input).read_text())
        else:
            if not args.sector: parser.error("--sector is required when using --company")
            if not args.revenue and args.revenue!=0: parser.error("--revenue is required when using --company")
            raw={"name": args.company,"sector": args.sector,"revenue": args.revenue,"notes": args.notes}

        company=PortfolioCompany.model_validate(raw) #type checking via Pydantic method
    except Exception as e:
        print(f"Error loading input: {e}",file=sys.stderr) #with json.loads
        sys.exit(1)

    #Run valuation calc.
    try:
        result, audit_entries=run_comps_valuation(company)
    except Exception as e:
        print(f"Valuation error: {e}",file=sys.stderr)
        sys.exit(1)

    #Render output
    if args.output: render_json(result,audit_entries,args.output)
    else: render_terminal(result,audit_entries)


if __name__ == "__main__":
    main()