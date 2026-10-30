# Quarterly universe step (about 10 minutes, free)

1. Go to Stockanalysis.com > Screener (free CSV export). Finviz works too but its CSV export is a paid feature.
2. Filters: Country USA; Market cap over $10B; Price over $5; Avg volume over 1M; Sector NOT Financial and NOT Real Estate; EPS positive; ROE positive; Debt/Equity under 1; Free cash flow positive.
3. Add columns if you can: Sector, Market Cap, Price, Avg Volume, Debt/Equity, ROE, EPS (TTM), Free Cash Flow. Export as CSV.
4. Save as `input/universe.csv` (exactly one screener CSV in `input/`).
5. Run `python build_universe.py`. It writes `eligible_universe.json` and prints why stocks were dropped.
6. Commit the JSON. The daily scan reads it.

Target: 100 to 250 stocks. The daily scan applies the options-specific filters on top.
Why exclude Financials and Real Estate: debt ratios are not comparable for them.
