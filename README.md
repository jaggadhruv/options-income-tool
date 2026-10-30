# Options Income Tool

Conservative US options income scanner for strong companies. Cash-secured puts and covered calls only. No spreads, no naked options, no leverage.

Start with **LEARN.md**.

## Setup
```
pip install -r requirements.txt
```
1. Edit `config.py` (capital and risk rules).
2. Quarterly: follow `SCREENING.md` to build `eligible_universe.json`.
3. Daily: `python scan.py`. Open `reports/latest.html`.
4. Test without internet: `python scan.py --mock` (fake data, labelled MOCK).

## Optional inputs (see `input/*.example.csv`; copy to drop `.example`)
- `input/holdings.csv`: shares you own, for covered-call ideas.
- `input/positions.csv`: options you have sold. The report tells you daily whether to take profit, close or roll.
- `input/journal.csv`: your own trade log for paper trading review.

## Automation
`.github/workflows/daily-scan.yml` runs Mon to Fri after the US close and commits the report, same pattern as your other tools. No secrets needed.

## Files
`config.py` rules · `scan.py` engine · `bs.py` option maths · `data.py` Yahoo + mock data · `report.py` HTML · `build_universe.py` quarterly universe

Educational tool, not financial advice.
