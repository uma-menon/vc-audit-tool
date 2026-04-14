'''
Comparable Company Analysis (Comps) Fair Value calculation.

Workflow:
  1. Fetch public peers by the company's sector.
  2. Select up to MAX_PEERS companies.
  3. Calculate each peer's EV/Revenue multiple.
  4. Take the median EV/Revenue multiple of the peer group.
  5. Apply that median to the portfolio company's revenue to receive the Fair Value point estimate.
  6. Apply a ±RANGE_BAND to produce a fair value range.
'''

from enum import Enum
from statistics import median
from typing import Optional
from pydantic import BaseModel, Field
from formatter import format_usd

#constants
RANGE_BAND=0.20 #to build FV high & low from FV point
MAX_PEERS=6

#3 Pydantic Models 
class Sector(str, Enum): #in case of capitalization differences, etc.
    SAAS = "saas"
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    ECOMMERCE = "ecommerce"
    MARKETPLACE = "marketplace"
    DEEPTECH = "deeptech"
    OTHER = "other"

class PortfolioCompany(BaseModel): #all companies must have these field types
    name: str
    sector: Sector
    revenue: float = Field(..., gt=0) #required, >0
    notes: Optional[str] = None #may be relevant for human reviewer

class PublicComp(BaseModel): #all peers must have these field types
    ticker: str
    name: str
    ev_usd: float=Field(..., gt=0)
    revenue: float=Field(..., gt=0)

    @property
    def ev_revenue_multiple(self) -> float:
        return self.ev_usd/self.revenue


# Mock peer data --> replace with an API such as YahooFinance
PEERS: dict[Sector, list[dict]] = {
    Sector.SAAS: [
        dict(ticker="CRM",  name="Salesforce",    ev_usd=220e9, revenue=34e9),
        dict(ticker="NOW",  name="ServiceNow",    ev_usd=160e9, revenue=10e9),
        dict(ticker="HUBS", name="HubSpot",       ev_usd=18e9,  revenue=2.5e9),
        dict(ticker="ZS",   name="Zscaler",       ev_usd=30e9,  revenue=2.2e9),
        dict(ticker="DDOG", name="Datadog",       ev_usd=35e9,  revenue=2.7e9),
        dict(ticker="VEEV", name="Veeva Systems", ev_usd=28e9,  revenue=2.4e9),
    ],
    Sector.FINTECH: [
        dict(ticker="ADYEN", name="Adyen",          ev_usd=40e9, revenue=1.8e9),
        dict(ticker="FISV",  name="Fiserv",         ev_usd=80e9, revenue=19e9),
        dict(ticker="SQ",    name="Block (Square)", ev_usd=42e9, revenue=21e9),
        dict(ticker="AFRM",  name="Affirm",         ev_usd=16e9, revenue=2.5e9),
        dict(ticker="NCNO",  name="nCino",          ev_usd=4e9,  revenue=0.5e9),
    ],
    Sector.HEALTHCARE: [
        dict(ticker="VEEVA", name="Veeva Systems",  ev_usd=28e9,  revenue=2.4e9),
        dict(ticker="HCAT",  name="Health Catalyst",ev_usd=0.8e9, revenue=0.3e9),
        dict(ticker="AMWL",  name="Amwell",         ev_usd=0.6e9, revenue=0.3e9),
        dict(ticker="PHR",   name="Phreesia",       ev_usd=1.4e9, revenue=0.35e9),
    ],
    Sector.ECOMMERCE: [
        dict(ticker="SHOP", name="Shopify",      ev_usd=95e9, revenue=8.9e9),
        dict(ticker="BIGC", name="BigCommerce",  ev_usd=0.7e9,revenue=0.34e9),
        dict(ticker="MELI", name="MercadoLibre", ev_usd=90e9, revenue=17e9),
    ],
    Sector.MARKETPLACE: [
        dict(ticker="ABNB", name="Airbnb", ev_usd=80e9,  revenue=11e9),
        dict(ticker="UBER", name="Uber",   ev_usd=150e9, revenue=44e9),
        dict(ticker="LYFT", name="Lyft",   ev_usd=5e9,   revenue=5.7e9),
        dict(ticker="ETSY", name="Etsy",   ev_usd=6e9,   revenue=2.7e9),
    ],
    Sector.DEEPTECH: [
        dict(ticker="AI",   name="C3.ai",        ev_usd=3e9,  revenue=0.4e9),
        dict(ticker="SOUN", name="SoundHound AI",ev_usd=2e9,  revenue=0.09e9),
        dict(ticker="BBAI", name="BigBear.ai",   ev_usd=0.5e9,revenue=0.16e9),
        dict(ticker="PATH", name="UiPath",       ev_usd=9e9,  revenue=1.3e9),
    ],
    Sector.OTHER: [
        dict(ticker="TTD",  name="The Trade Desk",ev_usd=40e9, revenue=2.4e9),
        dict(ticker="TWLO", name="Twilio",        ev_usd=10e9, revenue=4.5e9),
        dict(ticker="MDB",  name="MongoDB",       ev_usd=20e9, revenue=2.0e9),
    ],
}

def get_peers(sector: Sector) -> list[PublicComp]:
    raw=PEERS.get(sector, PEERS[Sector.OTHER])
    return [PublicComp(**row) for row in raw] #unpack


#Actual valuation calculation & logging
def run_comps_valuation(company: PortfolioCompany) -> tuple[dict, list[dict]]:
    '''
    Run the Comps valuation workflow.

    Returns:
        result: dict with all output fields (fair value, inputs, narrative, sources)
        audit_entries: list of step dicts for the audit trail
    '''
    entries: list[dict]=[]

    def log(step: str, description: str, detail: dict) -> None:
        entries.append({"step": step, "description": description, "detail": detail})

    #Record inputs
    log("inputs", 
        f"Valuation requested for {company.name}.", 
        {
            "sector":company.sector.value,
            "revenue":format_usd(company.revenue),
            **({"notes":company.notes} if company.notes else {}),
        }
    )

    #1. Fetch all peers
    all_peers=get_peers(company.sector)
    log("fetch_peers",f"Fetched {len(all_peers)} publicly traded {company.sector.value} peers.", 
        {
            "source": "Mock public comps dataset",
            "companies_available":[p.name for p in all_peers],
        }
    )

    #2. Select peer group
    peers=all_peers[:MAX_PEERS] #up to 6
    log("select_peers",f"Selected {len(peers)} peers from available set of {len(all_peers)}.", 
        {
            "tickers":[p.ticker for p in peers],
            "peer_names":[p.name for p in peers],
        }
    )

    #3-4. Calculate EV/Revenue multiples, and get median
    median_multiple=median(p.ev_revenue_multiple for p in peers)
    log("peer_multiples",f"Peer-group median EV/Revenue = {median_multiple:.1f}x.", 
        {
            # Company (Ticker): 1.0x
            **{f"{p.name} ({p.ticker})": f"{p.ev_revenue_multiple:.1f}x" for p in peers},
            "peer_group_median":f"{median_multiple:.1f}x",
        }
    )

    #5. Apply median multiple to company revenue 
    fair_value_point=median_multiple*company.revenue
    log("valuation_calculation",f"Applied {median_multiple:.1f}x multiple to {format_usd(company.revenue)} revenue", 
        {
            "formula":f"{median_multiple:.1f}x * {format_usd(company.revenue)}",
            "result": format_usd(fair_value_point),
        }
    )

    # 6. Find range
    fair_value_low=fair_value_point*(1-RANGE_BAND)
    fair_value_high=fair_value_point*(1+RANGE_BAND)
    log("fair_value_range",f"Applied ±{RANGE_BAND:.0%} range", 
        {
            "point_estimate":format_usd(fair_value_point),
            "low_end":format_usd(fair_value_low),
            "high_end":format_usd(fair_value_high),
        }
    )

    # Assemble result
    result={
        "company_name":company.name,
        "methodology":"Comparable Company Analysis (Comps)",
        "fair_value_point":fair_value_point,
        "fair_value_low":fair_value_low,
        "fair_value_high":fair_value_high,
        "revenue":company.revenue,
        "multiple_applied":round(median_multiple, 2),
        "multiple_type":"EV/Revenue",
        "peer_count":len(peers),
        "peer_names":[p.name for p in peers],
        "peer_tickers":[p.ticker for p in peers],
        "data_source":"Mock public comps dataset",
        "narrative":f"Valuation based on peer-group median multiple of {median_multiple:.1f}x applied to {format_usd(company.revenue)} LTM revenue",
    }

    return result, entries