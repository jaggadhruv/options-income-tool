# Options for complete beginners (read this first)

You do not need to understand all of options. This tool uses only two strategies, both with a known worst case and no borrowed money. Read this once, then paper trade before using real money.

## 1. What an option is
A contract between a buyer and a seller about 100 shares of a stock. Two kinds:

- **Put**: the buyer pays for the right to SELL 100 shares at a fixed price (the **strike**) by a fixed date (the **expiry**).
- **Call**: the buyer pays for the right to BUY 100 shares at the strike by the expiry.

The price the buyer pays is the **premium**. It is quoted per share, so a premium of $0.60 means $60 per contract.

Most people lose money **buying** options because time works against them. This tool never buys options to speculate. It **sells** them, so time works for you. The trade-off: you earn small, frequent amounts and carry the risk of a big bad day.

## 2. Strategy A: the cash-secured put (the main trade)
You say: "I will buy 100 shares of company X at $25 if it falls to $25 by expiry. Pay me $60 to promise that."

- You keep **cash equal to strike x 100** ($2,500) set aside. That is the "cash-secured" part. No borrowing.
- If the stock stays above $25 at expiry: the promise expires. You keep the $60. Nothing else happens.
- If the stock ends below $25: you **buy 100 shares at $25**, but you already got $60, so your real cost is $24.40. You now own a strong company at a discount to where it traded when you sold the put.
- Your real risk is the same as owning the shares: if the company collapses you lose most of the $2,500. That is why the tool only picks financially strong companies in uptrends. **Only sell a put on a stock you would be happy to own at the strike.**

## 3. Strategy B: the covered call (only if you already own 100 shares)
You say: "I will sell my 100 shares at $30 if the price reaches $30. Pay me $40 for that promise."

- If the stock stays below $30: you keep the shares and the $40.
- If it rises above $30: your shares are sold at $30. You keep the $40 and the gain up to $30, but miss any rise beyond.
- The tool never offers a strike below your cost basis, so you are never forced to sell at a loss.

## 4. The only number you need: delta
Delta is roughly the market's estimate of the chance the option ends up in the money. A delta of 0.15 is about a 15% chance you get assigned, about 85% chance you keep the full premium. The tool sells options with delta 0.10 to 0.25. Lower delta = safer and smaller premium.

## 5. Other words you will see
- **DTE**: days to expiry. Tool targets 30 to 45. That is where premium decays fastest relative to risk.
- **Break-even**: strike minus premium. Below this price on expiry day you have a loss.
- **Assignment**: the buyer exercises. Puts: you buy the shares. Calls: you sell the shares. Rarely happens early, more likely right before a dividend for calls.
- **Bid / ask / mid**: what buyers pay / sellers want / the middle. Always use a **limit order** at the mid or better, never a market order.
- **Open interest**: how many contracts exist. Low number = hard to exit. Tool requires 500+.
- **IV (implied volatility)**: how big a move the market expects. High IV pays more but warns of danger. The tool skips extremes.
- **Earnings**: companies can jump 10%+ overnight on results. The tool skips any trade where earnings fall before expiry.
- **Rolling**: closing the option and opening a later one. Beginners should prefer simply closing.

## 6. The risks, honestly
1. **A crash hurts.** A strong stock can still drop 20% in a bad month. Your loss would be the same as a shareholder's, minus the premium.
2. **Small wins, rare big losses.** Win rate may be 80%+, but one unmanaged loss can erase many wins. That is why the exit rules matter more than the entry.
3. **Gaps skip your stop.** If a stock drops overnight, your stop at 2x premium may fill much worse.
4. **Small account problem.** One contract on a $50 stock ties up $5,000. With $5,000 and the default 50% rule, only stocks priced under about $25 fit, and those are rarely top-quality. Expect the tool to often show nothing. Do not "fix" that by loosening risk rules.
5. **Data is delayed and imperfect** (free Yahoo data). Check live prices in your broker.
6. **Tax and access.** Confirm your broker offers US options to Netherlands residents and ask a tax adviser how option income is taxed for you.

## 7. Rules this tool enforces for you
- Maximum 2 trades at once, at most 50% of capital in one, always keep 20%+ in cash.
- One trade per sector.
- Only stocks above their 200-day average, not overheated, not 20% below their high, no earnings before expiry.
- No new trades if VIX > 30 or the S&P 500 is below its 200-day average.
- Close at 50% profit, at 21 days left, or if the option costs 2x what you got.

## 8. How to start (recommended order)
1. **Weeks 1 to 2**: read this, run the scan with `--mock`, read the report.
2. **Weeks 3 to 10**: paper trade. Most brokers offer a practice account. Log each trade in `input/journal.csv`. Follow the exit rules exactly.
3. **After 8 to 10 paper trades**: if you followed the rules and understand every number on the card, go live with **one** contract and the smallest sensible position.
4. Never add money to a losing trade. Never sell options on a stock you would not own.

## 9. Checklist before every trade
- [ ] Do I want to own 100 shares of this company at the break-even price?
- [ ] Is the cash set aside and free (not needed for rent or bills)?
- [ ] Did I check the live bid/ask and use a limit order?
- [ ] Do I know my three exits: profit target, time exit, stop?
- [ ] Is this still the only trade in this sector?
