'''
Output rendering.

Supports two output modes:
  - Terminal: plain-text report
  - JSON export
'''

import json
from pathlib import Path

def format_usd(value: float) -> str:
    if abs(value)>=1e9: return f"${value/1e9:.2f}B"
    return f"${value/1e6:.1f}M"


def render_terminal(result: dict, entries: list[dict]) -> None:
    '''Print a plain-text valuation report.'''
    #Header
    print(f"\nCompany: {result['company_name']}")
    print(f"Methodology: {result['methodology']}\n")

    #Results
    print(f"Estimated fair value: {format_usd(result['fair_value_point'])}")
    print(f"Range: {format_usd(result['fair_value_low'])} – {format_usd(result['fair_value_high'])}\n")

    print("Key inputs & assumptions:")
    print(f"\tRevenue: {format_usd(result['revenue'])}")
    print(f"\tMultiple used: {result['multiple_applied']:.1f}x {result['multiple_type']}")
    print(f"\tMultiple source: median of {result['peer_count']} public comps\n")

    print("Data sources:")
    print(f"\t{result['data_source']}")
    print("\tPeers: " + ", ".join([f"{n} ({t})" for n, t in zip(result['peer_names'], result['peer_tickers'])]) + "\n")

    print(f"How this estimate was derived: {result['narrative']}\n")

    print(f"Audit trail for: {result['company_name']}")
    print(render_text(entries))


def render_json(result: dict, entries: list[dict], output_path: str | Path) -> None:
    '''Write a machine-readable JSON report to disk.'''
    payload={
        "valuation":{
            "company_name":result["company_name"],
            "methodology":result["methodology"],
            "estimated_fair_value": {
                "point_usd": round(result["fair_value_point"]),
                "low_usd": round(result["fair_value_low"]),
                "high_usd": round(result["fair_value_high"]),
            },
            "key_inputs_and_assumptions": {
                "revenue_usd":result["revenue"],
                "multiple_type":result["multiple_type"],
                "multiple_applied":result["multiple_applied"],
            },
            "data_source":result["data_source"],
            "peer_group":{
                "count":result["peer_count"],
                "companies":result["peer_names"],
                "tickers":result["peer_tickers"],
            },
            "narrative":result["narrative"],
        },
        "audit_trail":[{"step_number": i, **entry} for i, entry in enumerate(entries,1)],
    }
    Path(output_path).write_text(json.dumps(payload, indent=2))
    print(f"JSON report saved to {output_path}")


def render_text(entries: list[dict]) -> str:
    '''Return a numbered plain-text audit chain.'''
    text=""
    for i, entry in enumerate(entries,1):
        text+=f"[{i}] {entry['step'].upper()}\n"
        text+=f"\t{entry['description']}\n"

        for k, v in entry["detail"].items():
            
            if isinstance(v, list): formatted=", ".join(str(x) for x in v)# format v (detail val)
            else: formatted=str(v)

            text+=f"\t{k}: {formatted}\n"

    return text