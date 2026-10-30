"""Data access. YahooProvider = live (yfinance). MockProvider = offline synthetic data for testing."""
import time, zlib, datetime as dt
import numpy as np
import pandas as pd

class YahooProvider:
    def __init__(self, delay=0.3):
        import yfinance as yf
        self.yf, self.delay, self._t = yf, delay, {}

    def _tk(self, sym):
        if sym not in self._t:
            time.sleep(self.delay)
            self._t[sym] = self.yf.Ticker(sym)
        return self._t[sym]

    def history(self, sym, days=400):
        df = self._tk(sym).history(period="2y", auto_adjust=True)
        return df.tail(days) if df is not None and len(df) else pd.DataFrame()

    def next_earnings(self, sym):
        try:
            cal = self._tk(sym).calendar
            d = cal.get("Earnings Date") if isinstance(cal, dict) else None
            if d:
                d = d[0] if isinstance(d, (list, tuple)) else d
                return pd.Timestamp(d).date()
        except Exception:
            pass
        return None

    def expirations(self, sym):
        try:
            return list(self._tk(sym).options)
        except Exception:
            return []

    def chain(self, sym, expiry):
        oc = self._tk(sym).option_chain(expiry)
        return oc.calls, oc.puts


class MockProvider:
    """Deterministic fake market so the whole pipeline can be tested without internet."""
    def __init__(self, seed=7):
        self.rng = np.random.default_rng(seed)
        self.today = dt.date.today()

    def _spot(self, sym):
        return 10 + (zlib.crc32(sym.encode()) % 3000) / 100.0     # $10 - $40

    def history(self, sym, days=400):
        s0 = self._spot(sym)
        r = np.random.default_rng(zlib.crc32(sym.encode()) % 2**32).normal(0.0005, 0.012, days)
        px = s0 * np.exp(np.cumsum(r) - r.sum() + np.log(1))   # ends at s0
        idx = pd.bdate_range(end=pd.Timestamp(self.today), periods=days)
        return pd.DataFrame({"Close": px, "High": px * 1.01, "Low": px * .99,
                             "Volume": 3e6}, index=idx)

    def next_earnings(self, sym):
        return self.today + dt.timedelta(days=15 if zlib.crc32(sym.encode()) % 5 == 0 else 70)

    def expirations(self, sym):
        out = []
        d = self.today
        while len(out) < 6:
            d += dt.timedelta(days=1)
            if d.weekday() == 4:
                out.append(d.isoformat())
        return out

    def chain(self, sym, expiry):
        import bs
        S = self.history(sym)["Close"].iloc[-1]
        T = max((dt.date.fromisoformat(expiry) - self.today).days, 1) / 365
        strikes = np.round(np.arange(S * 0.7, S * 1.3, max(0.5, round(S / 40 * 2) / 2)), 2)
        rows_c, rows_p = [], []
        for k in strikes:
            iv = 0.26 + 0.25 * max(0, (S - k) / S)           # put skew
            for kind, rows in (("call", rows_c), ("put", rows_p)):
                mid = bs.price(S, k, T, 0.04, iv, kind)
                half = max(0.01, mid * 0.02)
                rows.append(dict(strike=k, bid=max(0.0, round(mid - half, 2)), ask=round(mid + half, 2),
                                 lastPrice=round(mid, 2), openInterest=int(2000 * np.exp(-abs(k - S) / S * 6)),
                                 volume=300, impliedVolatility=iv))
        return pd.DataFrame(rows_c), pd.DataFrame(rows_p)
