import requests
import datetime

key = "vdtGSukfoVMDqmp5"

wars_url = f"https://api.torn.com/v2/faction/rankedwars?offset=0&limit=20&sort=DESC&key={key}"
wars = requests.get(wars_url, timeout=30).json()
latest = wars["rankedwars"][0]
rw_id = latest["id"]

report_url = f"https://api.torn.com/v2/faction/{rw_id}/rankedwarreport?key={key}"
report = requests.get(report_url, timeout=30).json()["rankedwarreport"]

start_dt = datetime.datetime.utcfromtimestamp(report["start"]).isoformat() + "Z"
end_dt = datetime.datetime.utcfromtimestamp(report["end"]).isoformat() + "Z"

factions = report["factions"]
our_id = latest["winner"]
our_faction = next(f for f in factions if f["id"] == our_id)
opp_faction = next(f for f in factions if f["id"] != our_id)

print("RW ID:", rw_id)
print("Start:", start_dt)
print("End:", end_dt)
print("Opposing Faction:", opp_faction["name"])
print("Our Faction:", our_faction["name"])
print("\nMembers:")
for m in our_faction["members"]:
    print(f"{m['id']}, {m['name']}, L{m['level']}, Attacks {m['attacks']}, Score {m['score']}")
