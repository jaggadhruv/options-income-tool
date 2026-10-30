"""QUARTERLY step. Turn a free screener CSV export into eligible_universe.json.
Usage:  python build_universe.py [path/to/export.csv]   (default: the single CSV in input/)
See SCREENING.md for the screener recipe."""
import sys, glob, json, re
import pandas as pd
import config as C

ALIASES = {
    "ticker": ["ticker", "symbol"],
    "name": ["company name", "name", "company"],
    "sector": ["sector"],
    "mcap": ["market cap", "marketcap", "market capitalization"],
    "price": ["price", "stock price", "last"],
    "volume": ["avg volume", "average volume", "avg. volume", "volume"],
    "de": ["debt / equity", "debt/equity", "d/e", "debt to equity"],
    "roe": ["roe", "return on equity"],
    "eps": ["eps (ttm)", "eps", "eps ttm"],
    "fcf": ["free cash flow", "fcf"],
}

def num(x):
    """'12.5B' -> 12.5e9, '35%' -> 35.0, '-' -> None"""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).replace(",", "").replace("$", "").replace("%", "").strip()
    if s in ("", "-", "n/a", "N/A", "nan"):
        return None
    m = re.fullmatch(r"(-?[\d.]+)\s*([KMBT]?)", s, re.I)
    if not m:
        return None
    return float(m.group(1)) * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[m.group(2).upper()]

def pick(df, key):
    low = {c.lower().strip(): c for c in df.columns}
    for a in ALIASES[key]:
        if a in low:
            return low[a]
    return None

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        files = glob.glob("input/*.csv")
        files = [f for f in files if "holdings" not in f and "positions" not in f]
        if len(files) != 1:
            sys.exit("Put exactly one screener CSV in input/ (or pass a path). Found: %s" % files)
        path = files[0]
    df = pd.read_csv(path)
    col = {k: pick(df, k) for k in ALIASES}
    if not col["ticker"]:
        sys.exit("No Ticker/Symbol column found. Columns: %s" % list(df.columns))
    out, dropped = [], {}
    def drop(why): dropped[why] = dropped.get(why, 0) + 1
    seen = set()
    for _, r in df.iterrows():
        t = str(r[col["ticker"]]).strip().upper().replace(".", "-")
        if not t or t in seen or t == "NAN":
            continue
        seen.add(t)
        g = lambda k: num(r[col[k]]) if col[k] else None
        sector = str(r[col["sector"]]) if col["sector"] else "Unknown"
        mcap, price, vol, de, roe, eps, fcf = (g(k) for k in ("mcap", "price", "volume", "de", "roe", "eps", "fcf"))
        if sector.lower() in ("financial", "financials", "financial services", "real estate"):
            drop("financials/real estate (balance sheet not comparable)"); continue
        if mcap is not None and mcap < C.MIN_MARKET_CAP: drop("market cap"); continue
        if price is not None and price < C.MIN_PRICE: drop("price"); continue
        if vol is not None and vol < C.MIN_AVG_VOLUME: drop("volume"); continue
        if de is not None and de > 1.0: drop("debt/equity > 1"); continue
        if roe is not None and roe <= 0: drop("ROE <= 0"); continue
        if eps is not None and eps <= 0: drop("EPS <= 0"); continue
        if fcf is not None and fcf <= 0: drop("free cash flow <= 0"); continue
        out.append({"ticker": t, "name": str(r[col["name"]]) if col["name"] else t,
                    "sector": sector, "mcap": mcap, "price": price})
    json.dump({"source": path, "count": len(out), "stocks": out}, open("eligible_universe.json", "w"), indent=1)
    print(f"Universe: {len(out)} stocks written to eligible_universe.json")
    for k, v in sorted(dropped.items(), key=lambda x: -x[1]):
        print(f"  dropped {v:4d}  {k}")

if __name__ == "__main__":
    main()
