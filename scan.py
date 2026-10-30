"""DAILY step. Finds cash-secured-put and covered-call candidates on quality US stocks,
applies the risk rules in config.py, monitors open positions, writes an HTML report.
Usage:  python scan.py            (live Yahoo data)
        python scan.py --mock     (offline synthetic data, for testing)"""
import sys, os, json, math, glob, datetime as dt
import numpy as np
import pandas as pd
import config as C
import bs
import report

TODAY = dt.date.today()

# ---------------------------------------------------------------- indicators
def indicators(h):
    c = h["Close"].dropna()
    if len(c) < 210:
        return None
    d = c.diff()
    up, dn = d.clip(lower=0).rolling(14).mean(), (-d.clip(upper=0)).rolling(14).mean()
    rsi = float(100 - 100 / (1 + up.iloc[-1] / dn.iloc[-1])) if dn.iloc[-1] > 0 else 100.0
    hv = float(np.log(c).diff().tail(30).std() * math.sqrt(252))
    return dict(price=float(c.iloc[-1]), sma50=float(c.tail(50).mean()), sma200=float(c.tail(200).mean()),
                rsi=rsi, hv30=hv, high52=float(c.tail(252).max()),
                drawdown=float(1 - c.iloc[-1] / c.tail(252).max()))

def regime(p):
    """Market gate. Returns dict with ok flag and the facts behind it."""
    out = {"ok": True, "notes": []}
    try:
        spy = indicators(p.history("SPY"))
        vix = p.history("^VIX")["Close"].iloc[-1] if hasattr(p, "history") else None
        out.update(spy=spy["price"], spy_sma200=spy["sma200"], vix=float(vix))
        if C.REQUIRE_SPY_ABOVE_SMA200 and spy["price"] < spy["sma200"]:
            out["ok"] = False; out["notes"].append("S&P 500 (SPY) is below its 200-day average: long-term downtrend.")
        if vix > C.VIX_PAUSE_ABOVE:
            out["ok"] = False; out["notes"].append(f"VIX is {vix:.1f}, above {C.VIX_PAUSE_ABOVE:.0f}: market is in panic mode.")
    except Exception as e:
        out["ok"] = False; out["notes"].append(f"Could not read market data ({e}). Standing aside to be safe.")
    return out

def pick_expiry(exps):
    best = None
    for e in exps:
        dte = (dt.date.fromisoformat(e) - TODAY).days
        if C.DTE_MIN <= dte <= C.DTE_MAX:
            if best is None or abs(dte - C.DTE_TARGET) < abs(best[1] - C.DTE_TARGET):
                best = (e, dte)
    return best

def spread_ok(bid, ask):
    mid = (bid + ask) / 2
    return mid > 0 and ((ask - bid) <= C.MAX_SPREAD_ABS or (ask - bid) / mid <= C.MAX_SPREAD_PCT)

def clip01(x): return max(0.0, min(1.0, x))

# ---------------------------------------------------------------- cash-secured puts
def eval_put(sym, meta, ind, p, funnel, held_cash):
    def rej(why): funnel[why] = funnel.get(why, 0) + 1; return None
    if C.REQUIRE_ABOVE_SMA200 and ind["price"] < ind["sma200"]: return rej("below 200-day average")
    if ind["drawdown"] > C.MAX_DRAWDOWN_FROM_HIGH: return rej("more than 20% below 52w high")
    if ind["rsi"] > C.RSI_MAX_FOR_PUTS: return rej("overheated (RSI)")
    exp = pick_expiry(p.expirations(sym))
    if not exp: return rej("no expiry in 30-45 day window")
    expiry, dte = exp
    earn = p.next_earnings(sym)
    if C.AVOID_EARNINGS_BEFORE_EXPIRY and earn and TODAY <= earn <= dt.date.fromisoformat(expiry) + dt.timedelta(days=C.EARNINGS_BUFFER_DAYS):
        return rej("earnings before expiry")
    _, puts = p.chain(sym, expiry)
    S, T = ind["price"], dte / 365
    best, seen_any = None, False
    for _, o in puts.iterrows():
        K, bid, ask, iv, oi = o["strike"], o["bid"], o["ask"], o["impliedVolatility"], o.get("openInterest", 0) or 0
        if K >= S or iv < 0.05 or bid <= 0: continue
        d = bs.delta(S, K, T, C.RISK_FREE_RATE, iv, "put")
        if d is None or not (C.DELTA_MIN <= abs(d) <= C.DELTA_MAX): continue
        seen_any = True
        if oi < C.MIN_OPEN_INTEREST or not spread_ok(bid, ask): continue
        cash = K * 100
        if cash > C.CAPITAL * C.MAX_POSITION_PCT: continue
        mid = round((bid + ask) / 2, 2)
        roc = mid / (K - mid)
        ann = roc * 365 / dte
        if not (C.MIN_ANNUALISED_RETURN <= ann <= C.MAX_ANNUALISED_RETURN): continue
        planned_loss = mid * (C.STOP_MULTIPLE - 1) * 100
        if planned_loss > C.CAPITAL * C.MAX_LOSS_PER_TRADE_PCT: continue
        pitm = bs.prob_itm(S, K, T, C.RISK_FREE_RATE, iv, "put")
        richness = iv / max(ind["hv30"], 0.01)
        score = (25 * (1 - clip01(abs(abs(d) - 0.17) / 0.10)) + 20 * clip01(ann / 0.25)
                 + (15 if S > ind["sma50"] > ind["sma200"] else 8)
                 + 15 * clip01((richness - 0.8) / 0.6) + (10 if K < ind["sma50"] else 0)
                 + 10 * clip01(oi / 3000) * (1 - clip01(((ask - bid) / mid) / C.MAX_SPREAD_PCT) * 0.5)
                 + (5 if not earn else 0))
        c = dict(kind="put", ticker=sym, name=meta.get("name", sym), sector=meta.get("sector", "Unknown"),
                 price=S, strike=float(K), expiry=expiry, dte=dte, bid=bid, ask=ask, credit=mid,
                 delta=abs(d), p_profit=1 - pitm, iv=iv, hv=ind["hv30"], richness=richness, oi=int(oi),
                 cash_needed=cash, breakeven=K - mid, cushion=(S - (K - mid)) / S, roc=roc, ann=ann,
                 max_loss=(K - mid) * 100, planned_loss=planned_loss, earnings=str(earn) if earn else "n/a",
                 rsi=ind["rsi"], sma50=ind["sma50"], sma200=ind["sma200"], score=round(score, 1),
                 tp_price=round(mid * (1 - C.TAKE_PROFIT_PCT), 2), stop_price=round(mid * C.STOP_MULTIPLE, 2),
                 time_exit=(dt.date.fromisoformat(expiry) - dt.timedelta(days=C.TIME_EXIT_DTE)).isoformat())
        if best is None or c["score"] > best["score"]: best = c
    if best is None:
        return rej("no put passed delta/liquidity/return/capital rules" if seen_any else "no put in delta range or too expensive for your capital")
    return best

# ---------------------------------------------------------------- covered calls
def eval_call(sym, shares, basis, meta, ind, p, funnel):
    def rej(why): funnel[why] = funnel.get(why, 0) + 1; return None
    if shares < 100: return rej("holding < 100 shares")
    exp = pick_expiry(p.expirations(sym))
    if not exp: return rej("no expiry in window")
    expiry, dte = exp
    earn = p.next_earnings(sym)
    if C.AVOID_EARNINGS_BEFORE_EXPIRY and earn and TODAY <= earn <= dt.date.fromisoformat(expiry): return rej("earnings before expiry")
    calls, _ = p.chain(sym, expiry)
    S, T = ind["price"], dte / 365
    best = None
    for _, o in calls.iterrows():
        K, bid, ask, iv, oi = o["strike"], o["bid"], o["ask"], o["impliedVolatility"], o.get("openInterest", 0) or 0
        if K <= S * 1.03 or K < basis or iv < 0.05 or bid <= 0: continue   # never lock in a loss
        d = bs.delta(S, K, T, C.RISK_FREE_RATE, iv, "call")
        if d is None or not (C.DELTA_MIN <= d <= C.DELTA_MAX): continue
        if oi < C.MIN_OPEN_INTEREST or not spread_ok(bid, ask): continue
        mid = round((bid + ask) / 2, 2)
        ann = mid / S * 365 / dte
        if ann < 0.04: continue
        score = 40 * (1 - clip01(abs(d - 0.17) / 0.10)) + 30 * clip01(ann / 0.15) + 20 * clip01(oi / 3000) + (10 if not earn else 0)
        c = dict(kind="call", ticker=sym, name=meta.get("name", sym), sector=meta.get("sector", "Unknown"), price=S,
                 strike=float(K), expiry=expiry, dte=dte, credit=mid, delta=d, p_profit=1 - bs.prob_itm(S, K, T, C.RISK_FREE_RATE, iv, "call"),
                 iv=iv, oi=int(oi), shares=int(shares), basis=basis, ann=ann,
                 upside_cap=(K - S) / S, gain_if_called=(K - basis + mid) * 100, score=round(score, 1),
                 tp_price=round(mid * (1 - C.TAKE_PROFIT_PCT), 2), time_exit=(dt.date.fromisoformat(expiry) - dt.timedelta(days=C.TIME_EXIT_DTE)).isoformat(),
                 earnings=str(earn) if earn else "n/a", in_universe=meta.get("in_universe", True))
        if best is None or c["score"] > best["score"]: best = c
    return best or rej("no call passed rules")

# ---------------------------------------------------------------- open positions
def monitor(p, sectors):
    path = "input/positions.csv"
    if not os.path.exists(path): return []
    df = pd.read_csv(path)
    out = []
    for _, r in df.iterrows():
        sym, kind, K = str(r["ticker"]).upper(), str(r["type"]).lower(), float(r["strike"])
        dte = (dt.date.fromisoformat(str(r["expiry"])) - TODAY).days
        n, credit = int(r["contracts"]), float(r["credit"])
        try:
            S = indicators(p.history(sym))
            calls, puts = p.chain(sym, str(r["expiry"]))
            ch = (puts if kind == "put" else calls)
            row = ch.iloc[(ch["strike"] - K).abs().argsort()[:1]].iloc[0]
            now = round((row["bid"] + row["ask"]) / 2, 2)
        except Exception as e:
            out.append(dict(ticker=sym, kind=kind, strike=K, expiry=str(r["expiry"]), dte=dte, contracts=n, credit=credit,
                            now=None, captured=None, price=None, actions=[f"Could not fetch data ({e}). Check manually."], level="warn",
                            cash=K * 100 * n if kind == "put" else 0, sector=sectors.get(sym, "Unknown")))
            continue
        cap = (credit - now) / credit
        acts, level = [], "ok"
        if cap >= C.TAKE_PROFIT_PCT: acts.append(f"TAKE PROFIT: buy to close (captured {cap:.0%} of premium)."); level = "good"
        if dte <= C.TIME_EXIT_DTE: acts.append(f"TIME EXIT: {dte} days left. Close, or roll out to a later month."); level = "warn"
        if now >= credit * C.STOP_MULTIPLE: acts.append(f"STOP: option is {now/credit:.1f}x what you collected. Close now, accept the loss."); level = "bad"
        if kind == "put" and S["price"] < K: acts.append("IN THE MONEY: stock is below your strike. Close, roll, or accept assignment (only if you still want to own it)."); level = "bad" if level != "bad" else level
        if kind == "put" and S["price"] < S["sma200"]: acts.append("Stock fell below its 200-day average. Long-term trend has turned; prefer to close."); level = "warn" if level == "ok" else level
        if not acts: acts.append("Hold. No rule triggered.")
        out.append(dict(ticker=sym, kind=kind, strike=K, expiry=str(r["expiry"]), dte=dte, contracts=n, credit=credit, now=now,
                        captured=cap, price=S["price"], actions=acts, level=level, cash=K * 100 * n if kind == "put" else 0,
                        sector=sectors.get(sym, "Unknown")))
    return out

# ---------------------------------------------------------------- main
def main():
    mock = "--mock" in sys.argv
    if mock:
        from data import MockProvider; p = MockProvider()
        uni = [{"ticker": t, "name": t + " Corp", "sector": s} for t, s in
               [("AAA", "Technology"), ("BBB", "Healthcare"), ("CCC", "Consumer Defensive"), ("DDD", "Energy"),
                ("EEE", "Industrials"), ("FFF", "Utilities"), ("GGG", "Communication Services"), ("HHH", "Healthcare")]]
        orig_hist = p.history
        p.history = lambda s, days=400: (pd.DataFrame({"Close": np.full(260, 20.0 if s == "^VIX" else 400.0)}) if s in ("^VIX", "SPY") else orig_hist(s, days))
    else:
        from data import YahooProvider; p = YahooProvider()
        if not os.path.exists("eligible_universe.json"):
            open("index.html", "w").write("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Options Income Report</title><body style='font:16px/1.5 sans-serif;max-width:640px;margin:40px auto;padding:0 16px'><h1>Options Income Report</h1><p><b>Setup needed.</b> The stock universe file (eligible_universe.json) has not been added yet, so nothing was scanned.</p><ol><li>Export a screener CSV (see SCREENING.md) into the input folder.</li><li>Run <code>python build_universe.py</code>.</li><li>Commit eligible_universe.json, then re-run the workflow.</li></ol><p>Updated: " + str(TODAY) + "</p></body>")
            print("SETUP NEEDED: eligible_universe.json is missing. Follow SCREENING.md: put your screener CSV in input/, run build_universe.py, commit the JSON. Nothing scanned.")
            sys.exit(0)
        uni = json.load(open("eligible_universe.json"))["stocks"]
    for u in uni:   # unknown sector must not make unrelated stocks block each other
        if str(u.get("sector", "Unknown")).lower() in ("unknown", "nan", "", "none"): u["sector"] = "Unknown-" + u["ticker"]
    sectors = {u["ticker"]: u["sector"] for u in uni}
    mkt = regime(p)
    funnel, puts, calls = {}, [], []
    for i, u in enumerate(uni):
        try:
            ind = indicators(p.history(u["ticker"]))
            if not ind: funnel["not enough history"] = funnel.get("not enough history", 0) + 1; continue
            c = eval_put(u["ticker"], u, ind, p, funnel, 0)
            if c: puts.append(c)
        except Exception as e:
            funnel["data error"] = funnel.get("data error", 0) + 1
    if os.path.exists("input/holdings.csv"):
        for _, h in pd.read_csv("input/holdings.csv").iterrows():
            t = str(h["ticker"]).upper()
            try:
                ind = indicators(p.history(t))
                meta = next((u for u in uni if u["ticker"] == t), {"name": t, "sector": "Unknown", "in_universe": False})
                c = eval_call(t, float(h["shares"]), float(h["cost_basis"]), meta, ind, p, funnel)
                if c: calls.append(c)
            except Exception:
                funnel["data error"] = funnel.get("data error", 0) + 1
    open_pos = monitor(p, sectors)
    # ---- portfolio construction (greedy, best score first, obey limits)
    deployed = sum(o["cash"] for o in open_pos)
    slots = C.MAX_OPEN_POSITIONS - len(open_pos)
    used_sectors = {o["sector"] for o in open_pos}
    picks, rest = [], []
    for c in sorted(puts, key=lambda x: -x["score"]):
        ok = (mkt["ok"] and len(picks) < slots and c["sector"] not in used_sectors | {x["sector"] for x in picks} 
              and deployed + c["cash_needed"] <= C.CAPITAL * C.MAX_DEPLOYED_PCT)
        if ok: picks.append(c); deployed += c["cash_needed"]
        else: rest.append(c)
    ctx = dict(date=str(TODAY), mock=mock, market=mkt, picks=picks, others=rest[:10], calls=sorted(calls, key=lambda x: -x["score"]),
               positions=open_pos, funnel=funnel, scanned=len(uni), deployed=deployed, slots=slots)
    os.makedirs("reports", exist_ok=True); os.makedirs("data", exist_ok=True)
    html = report.render(ctx)
    name = "reports/options_report_%s%s.html" % (TODAY, "_MOCK" if mock else "")
    open(name, "w").write(html); open("reports/latest.html", "w").write(html)
    if not mock: open("index.html", "w").write(html)   # GitHub Pages shows this at the site root
    json.dump(ctx, open("data/last_scan.json", "w"), indent=1, default=str)
    for f in sorted(glob.glob("reports/options_report_*.html"))[:-30]: os.remove(f)
    print(f"Scanned {len(uni)} | put candidates {len(puts)} | picks {len(picks)} | covered calls {len(calls)} | market OK: {mkt['ok']}")
    print("Report:", name)

if __name__ == "__main__":
    main()
