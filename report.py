"""HTML report. Single column, embedded CSS, one accent colour, green/red only for signal."""
from html import escape as e
import config as C

CSS = """
:root{--bg:#faf8f4;--fg:#1d1d1b;--mut:#6b6a66;--line:#e4e0d8;--acc:#1f4e5f;--good:#2f7d4f;--bad:#b3392f;--warn:#a8741a;--card:#fff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,Segoe UI,Helvetica,Arial,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 18px 60px}h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:34px 0 10px;padding-top:6px;border-top:1px solid var(--line)}
.sub{color:var(--mut);font-size:13px}.mono,td.n{font-family:ui-monospace,Menlo,Consolas,monospace}
.banner{border-radius:8px;padding:12px 16px;margin:16px 0;border:1px solid var(--line);background:var(--card)}
.banner.ok{border-left:5px solid var(--good)}.banner.stop{border-left:5px solid var(--bad)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin:12px 0}
.card h3{margin:0 0 2px;font-size:17px}.ticket{background:#f1efe8;border-radius:6px;padding:8px 12px;font-family:ui-monospace,Menlo,monospace;font-size:13.5px;margin:10px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:10px 0}.k{font-size:11.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.03em}.v{font-family:ui-monospace,Menlo,monospace;font-size:15px}
table{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--card)}th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left}th{font-size:11.5px;color:var(--mut);text-transform:uppercase}td.n{text-align:right}
.tag{display:inline-block;font-size:11.5px;padding:1px 8px;border-radius:10px;border:1px solid var(--line);color:var(--mut)}
.good{color:var(--good)}.bad{color:var(--bad)}.warn{color:var(--warn)}.acc{color:var(--acc)}
.rules li{margin:3px 0}.foot{margin-top:40px;font-size:12.5px;color:var(--mut);border-top:1px solid var(--line);padding-top:12px}
"""

def usd(x): return "$%s" % format(x, ",.0f")
def px(x): return "$%.2f" % x
def pct(x, d=0): return ("%." + str(d) + "f%%") % (x * 100)

def kv(k, v, cls=""): return f'<div><div class="k">{e(k)}</div><div class="v {cls}">{v}</div></div>'

def put_card(c, rank):
    return f"""<div class="card"><h3>#{rank} {e(c['ticker'])} <span class="sub">{e(c['name'])} · {e(c['sector'])} · score {c['score']:.0f}/100</span></h3>
<div class="ticket">SELL TO OPEN 1x {e(c['ticker'])} {c['expiry']} ${c['strike']:g} PUT, limit {px(c['credit'])} or better (bid {px(c['bid'])} / ask {px(c['ask'])})</div>
<div class="grid">{kv('Cash set aside', usd(c['cash_needed']))}{kv('Premium you collect', usd(c['credit']*100))}
{kv('Chance it expires worthless', pct(c['p_profit']), 'good')}{kv('Return (annualised)', pct(c['ann']))}
{kv('Stock now', px(c['price']))}{kv('You buy at (break-even)', px(c['breakeven']))}{kv('Cushion before loss', pct(c['cushion'],1))}{kv('Days to expiry', c['dte'])}</div>
<div class="grid">{kv('Take profit: buy back at', px(c['tp_price']), 'good')}{kv('Stop: buy back if price hits', px(c['stop_price']), 'bad')}
{kv('Time exit by', c['time_exit'], 'warn')}{kv('Planned max loss (if stop used)', usd(c['planned_loss']), 'bad')}</div>
<div class="sub">Worst case, stock goes to zero: lose {usd(c['max_loss'])}. Delta {c['delta']:.2f} · implied vol {pct(c['iv'])} vs recent realised {pct(c['hv'])} · open interest {c['oi']:,} · RSI {c['rsi']:.0f} · next earnings {e(c['earnings'])}.
Stock is above its 200-day average ({px(c['sma200'])}). If assigned you own 100 shares of a company that passed the quality screen, at {px(c['breakeven'])} each.</div></div>"""

def render(x):
    m = x["market"]
    mk = ("ok", "Market gate: OPEN. Conditions allow new trades.") if m["ok"] else ("stop", "Market gate: CLOSED. No new trades today.")
    facts = ""
    if "vix" in m: facts = f'S&P 500 ETF {px(m["spy"])} vs 200-day {px(m["spy_sma200"])} · VIX {m["vix"]:.1f}'
    h = [f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Options Income Report {x['date']}</title><style>{CSS}</style></head><body><main>"]
    h.append(f"<h1>Options Income Report</h1><div class='sub'>{x['date']} · {x['scanned']} quality stocks scanned · strategy: cash-secured puts and covered calls only · capital {usd(C.CAPITAL)}{' · <b>MOCK DATA, NOT REAL</b>' if x['mock'] else ''}</div>")
    h.append(f"<div class='banner {mk[0]}'><b>{mk[1]}</b><div class='sub'>{facts} {' '.join(e(n) for n in m['notes'])}</div></div>")
    h.append(f"<div class='sub'>Cash tied up (open trades plus today's picks) {usd(x['deployed'])} of {usd(C.CAPITAL)} · free trade slots {x['slots']} of {C.MAX_OPEN_POSITIONS}</div>")
    if x["positions"]:
        h.append("<h2>Your open positions: what to do today</h2>")
        h.append("<table><tr><th>Position</th><th>Expiry</th><th class='n'>DTE</th><th class='n'>Sold at</th><th class='n'>Now</th><th class='n'>Profit captured</th><th>Action</th></tr>")
        for o in x["positions"]:
            now = px(o["now"]) if o["now"] is not None else "n/a"; cap = pct(o["captured"]) if o["captured"] is not None else "n/a"
            h.append(f"<tr><td>{e(o['ticker'])} ${o['strike']:g} {o['kind']} x{o['contracts']}</td><td>{o['expiry']}</td><td class='n'>{o['dte']}</td><td class='n'>{px(o['credit'])}</td><td class='n'>{now}</td><td class='n'>{cap}</td><td class='{o['level']}'>{' '.join(e(a) for a in o['actions'])}</td></tr>")
        h.append("</table>")
    h.append("<h2>Today's best new trades (cash-secured puts)</h2>")
    if not m["ok"]: h.append("<p>The market gate is closed, so the tool suggests nothing new. Doing nothing is a valid position. Candidates below are for study only.</p>")
    elif x["slots"] <= 0: h.append("<p>All your trade slots are in use. Manage the open positions first.</p>")
    elif not x["picks"]: h.append("<p>No trade passed every rule today. That is normal and healthy. Do not loosen the rules to force a trade.</p>")
    for i, c in enumerate(x["picks"], 1): h.append(put_card(c, i))
    if x["calls"]:
        h.append("<h2>Covered calls on shares you own</h2><table><tr><th>Stock</th><th>Sell call</th><th class='n'>Premium</th><th class='n'>Chance worthless</th><th class='n'>Annualised</th><th class='n'>Upside you give up above</th><th class='n'>If called away</th><th>Exit</th></tr>")
        for c in x["calls"]:
            warn = "" if c.get("in_universe", True) else " <span class='tag'>not in quality universe</span>"
            h.append(f"<tr><td>{e(c['ticker'])}{warn}</td><td>{c['expiry']} ${c['strike']:g}</td><td class='n'>{usd(c['credit']*100)}</td><td class='n'>{pct(c['p_profit'])}</td><td class='n'>{pct(c['ann'])}</td><td class='n'>{px(c['strike'])} (+{pct(c['upside_cap'],1)})</td><td class='n'>{usd(c['gain_if_called'])} gain</td><td>buy back at {px(c['tp_price'])} or by {c['time_exit']}</td></tr>")
        h.append("</table><div class='sub'>Strike is always above your cost basis, so being called away never locks in a loss on the shares.</div>")
    if x["others"]:
        h.append("<h2>Other candidates (did not fit slots, sector or cash limits)</h2><table><tr><th>Stock</th><th>Sector</th><th>Put</th><th class='n'>Credit</th><th class='n'>Delta</th><th class='n'>Chance worthless</th><th class='n'>Annualised</th><th class='n'>Cash</th><th class='n'>Score</th></tr>")
        for c in x["others"]:
            h.append(f"<tr><td>{e(c['ticker'])}</td><td>{e(c['sector'])}</td><td>{c['expiry']} ${c['strike']:g}</td><td class='n'>{px(c['credit'])}</td><td class='n'>{c['delta']:.2f}</td><td class='n'>{pct(c['p_profit'])}</td><td class='n'>{pct(c['ann'])}</td><td class='n'>{usd(c['cash_needed'])}</td><td class='n'>{c['score']:.0f}</td></tr>")
        h.append("</table>")
    h.append("<h2>Why stocks were filtered out</h2><table><tr><th>Reason</th><th class='n'>Stocks</th></tr>")
    for k, v in sorted(x["funnel"].items(), key=lambda a: -a[1]): h.append(f"<tr><td>{e(k)}</td><td class='n'>{v}</td></tr>")
    h.append("</table>")
    h.append(f"""<h2>Your rules (from config.py)</h2><ul class='rules'><li>Max {C.MAX_OPEN_POSITIONS} trades, max {pct(C.MAX_POSITION_PCT)} of capital in one, max {pct(C.MAX_DEPLOYED_PCT)} deployed in total, one trade per sector.</li>
<li>Sell only options with delta {C.DELTA_MIN}-{C.DELTA_MAX}, {C.DTE_MIN}-{C.DTE_MAX} days out, on stocks above their 200-day average with no earnings before expiry.</li>
<li>Close at {pct(C.TAKE_PROFIT_PCT)} of premium captured, at {C.TIME_EXIT_DTE} days left, or if the option costs {C.STOP_MULTIPLE:g}x what you received.</li>
<li>No new trades if VIX is above {C.VIX_PAUSE_ABOVE:.0f} or the S&P 500 is below its 200-day average.</li></ul>
<div class='foot'>Educational tool, not financial advice. Options prices come from delayed free data and can be stale; always check the live bid/ask in your broker before placing an order, and use a limit order. Selling options can lose more than the premium collected. The "chance worthless" figure is a model estimate (Black-Scholes), not a guarantee. Not a recommendation to buy or sell any security.</div></main></body></html>""")
    return "".join(h)
