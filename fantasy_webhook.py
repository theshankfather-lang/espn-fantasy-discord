import os
import time
import requests
from datetime import datetime

# --- Config from environment ---
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
LEAGUE_ID = int(os.getenv("LEAGUE_ID", "284261"))  # default to your league
SEASON_YEAR = int(os.getenv("SEASON_YEAR", "2025"))
SWID = os.getenv("SWID")           # e.g., "{...}"
ESPN_S2 = os.getenv("ESPN_S2")     # long token

if not WEBHOOK_URL:
    raise SystemExit("❌ Missing WEBHOOK_URL environment variable")

COOKIES = {}
if SWID and ESPN_S2:
    COOKIES = {"SWID": SWID, "espn_s2": ESPN_S2}

BASE_URL = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON_YEAR}/segments/0/leagues/{LEAGUE_ID}"

def fetch_json(url: str):
    try:
        resp = requests.get(url, cookies=COOKIES, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"_error": str(e)}

def bold(text: str) -> str:
    return f"**{text}**"

def build_team_map(teams):
    return {team.get("id"): team for team in teams}

def format_standings(data) -> str:
    teams = data.get("teams", [])
    if not teams:
        return "No teams found."

    def wl(team):
        rec = team.get("record", {}).get("overall", {})
        return rec.get("wins", 0), rec.get("losses", 0)

    sorted_teams = sorted(teams, key=lambda t: wl(t)[0], reverse=True)
    lines = []
    for t in sorted_teams:
        name = f'{t.get("location","")} {t.get("nickname","")}'.strip() or f'Team {t.get("id")}'
        wins, losses = wl(t)
        lines.append(f"{bold(name)}: {wins}-{losses}")
    return f"{bold('Fantasy League Standings')}\n" + "\n".join(lines)

def format_matchups(data) -> str:
    teams = data.get("teams", [])
    schedule = data.get("schedule", [])
    week = data.get("scoringPeriodId")

    if not teams or not schedule or week is None:
        return "No schedule data available."

    team_by_id = build_team_map(teams)
    matchups = [m for m in schedule if m.get("matchupPeriodId") == week]
    if not matchups:
        return f"{bold(f'Week {week} Matchups')}\nNo matchups found."

    def team_name(team_id):
        t = team_by_id.get(team_id, {})
        return f'{t.get("location","")} {t.get("nickname","")}'.strip() or f"Team {team_id}"

    lines = []
    for m in matchups:
        home_id = m.get("home", {}).get("teamId")
        away_id = m.get("away", {}).get("teamId")
        home_score = m.get("home", {}).get("totalPoints", 0)
        away_score = m.get("away", {}).get("totalPoints", 0)

        status = m.get("status", {}).get("type", "STATUS_UNKNOWN")
        if status == "STATUS_SCHEDULED":
            status_emoji = "🕑 Scheduled"
        elif status == "STATUS_IN_PROGRESS":
            status_emoji = "🔴 In Progress"
        elif status == "STATUS_FINAL":
            status_emoji = "✅ Final"
        else:
            status_emoji = "ℹ️ Status Unknown"

        home = team_name(home_id) if home_id is not None else "TBD"
        away = team_name(away_id) if away_id is not None else "TBD"

        lines.append(f"{bold(home)} ({home_score:.1f}) vs {bold(away)} ({away_score:.1f}) — {status_emoji}")

    return f"{bold(f'Week {week} Matchups')}\n" + "\n".join(lines)

def run_update():
    data = fetch_json(BASE_URL)
    if "_error" in data:
        msg = f"⚠️ ESPN API error: {data['_error']}"
    else:
        standings = format_standings(data)
        matchups = format_matchups(data)
        msg = f"{standings}\n\n{matchups}"

    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
        print(f"✅ Update sent at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    except Exception as e:
        print(f"❌ Failed to post to Discord: {e}")

if __name__ == "__main__":
    while True:
        run_update()
        time.sleep(300)  # wait 5 minutes
