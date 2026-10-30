"""All risk rules live here. Change a number here, nowhere else.
Defaults are deliberately conservative. Read LEARN.md before changing them."""

# ---- Your account -------------------------------------------------------
CAPITAL = 5000.0                 # USD you are willing to dedicate to options income
MAX_POSITION_PCT = 0.50          # one position may tie up at most 50% of CAPITAL
MAX_OPEN_POSITIONS = 2           # never more than 2 trades at once
MAX_DEPLOYED_PCT = 0.80          # always keep 20%+ of CAPITAL in cash
MAX_LOSS_PER_TRADE_PCT = 0.10    # planned loss on one trade <= 10% of CAPITAL
MAX_PER_SECTOR = 1               # no two open trades in the same sector

# ---- Which stocks are allowed ------------------------------------------
MIN_MARKET_CAP = 10e9            # $10B+
MIN_AVG_VOLUME = 1_000_000
MIN_PRICE = 5.0

# ---- Which options are allowed -----------------------------------------
DTE_MIN, DTE_MAX = 30, 45        # days to expiry window
DTE_TARGET = 38
DELTA_MIN, DELTA_MAX = 0.10, 0.25   # abs(delta) of the option you SELL (about 75-90% chance to expire worthless)
MIN_OPEN_INTEREST = 500
MAX_SPREAD_PCT = 0.10            # (ask-bid)/mid must be <= 10%
MAX_SPREAD_ABS = 0.10            # ...or the spread is <= $0.10
MIN_ANNUALISED_RETURN = 0.08     # below 8% annualised is not worth the risk
MAX_ANNUALISED_RETURN = 0.60     # above 60% annualised = the market is warning you; skip
MIN_IV_RANK_PROXY = 0.0          # set e.g. 0.3 to demand richer premium
RISK_FREE_RATE = 0.04

# ---- Stock health filters (trend + sanity) ------------------------------
REQUIRE_ABOVE_SMA200 = True      # only sell puts on stocks in a long-term uptrend
MAX_DRAWDOWN_FROM_HIGH = 0.20    # skip if stock is >20% below its 52w high
RSI_MAX_FOR_PUTS = 70            # do not sell puts on overheated stocks
EARNINGS_BUFFER_DAYS = 3         # expiry must be at least this many days BEFORE earnings... (see scan.py)
AVOID_EARNINGS_BEFORE_EXPIRY = True   # skip any trade where earnings fall before expiry

# ---- Market regime gate (no new trades in bad markets) ------------------
VIX_PAUSE_ABOVE = 30.0           # stand aside if VIX > 30
REQUIRE_SPY_ABOVE_SMA200 = True

# ---- Exit rules (shown for each trade and in the open-position monitor) -
TAKE_PROFIT_PCT = 0.50           # buy back the option when 50% of premium is captured
TIME_EXIT_DTE = 21               # close or roll with 21 days left (gamma risk rises)
STOP_MULTIPLE = 2.0              # close if option price reaches 2x the credit you received
