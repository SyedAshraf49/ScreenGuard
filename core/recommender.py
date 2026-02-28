from datetime import datetime, timedelta
from backend.db import get_usage_for_date

STUDY_APPS = ["Code","VSCode","PyCharm","Word","Excel","PowerPoint"]
DISTRACTION_APPS = ["Chrome","YouTube","Netflix","Instagram"]

def get_recommendations():
    today = datetime.now().date()
    usage_entries = get_usage_for_date(str(today))
    aggregates = {}
    for entry in usage_entries:
        aggregates[entry["app"]] = aggregates.get(entry["app"], 0) + entry["duration"]
    data = [(app, duration) for app, duration in aggregates.items()]

    total = sum(d[1] for d in data)
    rec = []

    yesterday = today - timedelta(days=1)
    yesterday_entries = get_usage_for_date(str(yesterday))
    yesterday_total = sum(entry["duration"] for entry in yesterday_entries)

    if total >= 480:
        rec.append("🚨 Very high screen usage today. Plan a low-screen evening to recover.")
    elif total > 360:
        rec.append("⚠ High screen usage detected. Limit usage to under 6 hours.")
    elif total < 60:
        rec.append("🌱 Light screen usage so far. Keep this balance through the day.")

    if datetime.now().hour >= 23:
        rec.append("🌙 Avoid screens after 11 PM for healthy sleep.")

    distraction = sum(d[1] for d in data if any(a in d[0] for a in DISTRACTION_APPS))
    study = sum(d[1] for d in data if any(a in d[0] for a in STUDY_APPS))

    if distraction > study:
        rec.append("📵 Distraction apps dominate usage. Plan focused study sessions.")
    elif study >= 120:
        rec.append("📚 Productive app usage is strong today. Keep focus blocks consistent.")

    if total > 120:
        rec.append("⏱ Take a short break every hour to reduce eye strain.")

    if data:
        top_app, top_minutes = max(data, key=lambda item: item[1])
        if top_minutes >= max(90, int(total * 0.5)):
            rec.append(f"📌 {top_app} is taking most of your time. Consider app-specific limits.")

    if len(usage_entries) >= 25:
        rec.append("🧭 Usage is highly fragmented. Try 25-minute focus sessions with fewer app switches.")

    if yesterday_total > 0:
        diff = total - yesterday_total
        if diff >= 120:
            rec.append("📈 You are up more than 2 hours vs yesterday. Schedule a cooldown break.")
        elif diff <= -120:
            rec.append("📉 Great improvement vs yesterday. Keep the same routine tomorrow.")

    if not rec:
        rec.append("✅ Healthy digital habits detected.")

    return rec[:8]
