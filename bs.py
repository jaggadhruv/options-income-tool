"""Black-Scholes helpers. Yahoo does not provide Greeks, so we compute them."""
import math

def _ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def _d1d2(S, K, T, r, sigma):
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    return d1, d1 - sigma * math.sqrt(T)

def delta(S, K, T, r, sigma, kind):
    """Delta of a call (positive) or put (negative). Returns None on bad inputs."""
    if min(S, K, T, sigma) <= 0:
        return None
    d1, _ = _d1d2(S, K, T, r, sigma)
    return _ncdf(d1) if kind == "call" else _ncdf(d1) - 1

def prob_itm(S, K, T, r, sigma, kind):
    """Model probability the option finishes in the money."""
    if min(S, K, T, sigma) <= 0:
        return None
    _, d2 = _d1d2(S, K, T, r, sigma)
    return _ncdf(d2) if kind == "call" else _ncdf(-d2)

def price(S, K, T, r, sigma, kind):
    d1, d2 = _d1d2(S, K, T, r, sigma)
    if kind == "call":
        return S * _ncdf(d1) - K * math.exp(-r * T) * _ncdf(d2)
    return K * math.exp(-r * T) * _ncdf(-d2) - S * _ncdf(-d1)
