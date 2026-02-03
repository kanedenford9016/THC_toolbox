"""Debug script to see what get_faction_wars returns"""
import sys
sys.path.insert(0, 'backend')

from app.services.war_session import war_session_service

# Use a test faction ID - we know from test results there's at least one war
print("\n=== Debugging get_faction_wars ===\n")

# Get wars (this will use the local DB)
wars = war_session_service.get_faction_wars(faction_id=1)

print(f"Total wars returned: {len(wars)}")
for war in wars:
    print(f"\nWar: {war.get('name')}")
    print(f"  Status: {war.get('status')}")
    print(f"  Completed Timestamp: {war.get('completed_timestamp')}")
    print(f"  War ID: {war.get('id')}")
