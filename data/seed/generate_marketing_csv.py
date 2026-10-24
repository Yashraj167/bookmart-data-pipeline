import csv, os, random
from datetime import date, timedelta

random.seed(42)  # same data every run
campaigns = [
    (101, "Diwali Book Fest", "email"),
    (102, "Summer Reads",     "social"),
    (103, "Back to School",   "search"),
    (104, "Author Spotlight", "social"),
    (105, "Winter Sale",      "display"),
]
start = date(2026, 8, 1)

os.makedirs("data/csv", exist_ok=True)
with open("data/csv/marketing_spend.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["spend_date", "campaign_id", "campaign_name", "channel",
                "spend_usd", "impressions", "clicks"])
    for d in range(60):
        day = start + timedelta(days=d)
        for cid, name, channel in campaigns:
            impressions = random.randint(2000, 40000)
            clicks = int(impressions * random.uniform(0.01, 0.06))
            spend = round(random.uniform(20, 300), 2)
            w.writerow([day.isoformat(), cid, name, channel, spend, impressions, clicks])

print("Created data/csv/marketing_spend.csv")