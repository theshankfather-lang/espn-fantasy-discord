name: Fantasy Discord Updates

on:
  schedule:
    # Every 5 minutes on Sundays and Mondays (game windows) — times are UTC
    - cron: "*/5 * * * 0"
    - cron: "*/5 * * * 1"
    # Daily standings at 13:00 UTC (~9:00 AM EDT during DST)
    - cron: "0 13 * * *"
  workflow_dispatch: {}

jobs:
  run-updates:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests

      - name: Run updater
        env:
          WEBHOOK_URL: ${{ secrets.WEBHOOK_URL }}
          LEAGUE_ID: ${{ secrets.LEAGUE_ID }}
          SEASON_YEAR: ${{ secrets.SEASON_YEAR }}
          SWID: ${{ secrets.SWID }}
          ESPN_S2: ${{ secrets.ESPN_S2 }}
        run: |
          python fantasy_webhook.py
