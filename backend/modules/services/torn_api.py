"""Torn API integration service."""
import requests
from config.settings import config
from modules.models.models import AuditLog, FactionConfig
from datetime import datetime

class TornAPIService:
    """Service for interacting with Torn API."""
    
    def __init__(self):
        """Initialize Torn API service."""
        self.base_url = config.TORN_API_BASE_URL
        self.rate_limit = config.RATE_LIMIT_PER_MINUTE
    
    def validate_api_key(self, api_key):
        """
        Validate Torn API key and get user info.
        
        Args:
            api_key: Torn API key
            
        Returns:
            dict: User information including faction details
        """
        try:
            # Use v2 API with correct query parameter format
            url = f"{self.base_url}/user?key={api_key}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                print(f"Torn API error: {data['error']}")
                return None
            
            profile = data.get('profile', {})
            
            # Verify user has faction
            if not profile.get('faction_id'):
                return None
            
            # Return data in expected format
            return {
                'player_id': profile.get('id'),
                'name': profile.get('name'),
                'faction_id': profile.get('faction_id')
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Torn API error: {e}")
            return None
    
    def verify_faction_admin(self, api_key, torn_id):
        """
        Verify if user is a faction admin.
        
        Args:
            api_key: Torn API key
            torn_id: User's Torn ID
            
        Returns:
            dict: Faction info if admin, None otherwise
        """
        try:
            # Use v2 API with correct query parameter format
            url = f"{self.base_url}/faction?key={api_key}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                print(f"Torn API error: {data['error']}")
                return None
            
            faction = data.get('faction', {})
            
            # Check if user is in leadership position
            members = faction.get('members', {})
            user_member = members.get(str(torn_id))
            
            if not user_member:
                return None
            
            # Check position - leader, co-leader, or officer typically have admin rights
            position = user_member.get('position', '').lower()
            admin_positions = ['leader', 'co-leader', 'officer']
            
            if position in admin_positions:
                return {
                    'faction_id': faction.get('id'),
                    'faction_name': faction.get('name'),
                    'position': position
                }
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Torn API error: {e}")
            return None

    def get_latest_ranked_war_summary(self, api_key, faction_id):
        """
        Fetch latest ranked war and return summary for our faction.

        Args:
            api_key: Torn API key
            faction_id: Our faction ID

        Returns:
            dict: Ranked war summary with member list
        """
        try:
            wars_url = f"{self.base_url}/faction/rankedwars"
            params = {"offset": 0, "limit": 20, "sort": "DESC", "key": api_key}
            wars_resp = requests.get(wars_url, params=params, timeout=10)
            wars_resp.raise_for_status()
            wars_data = wars_resp.json()

            ranked_wars = wars_data.get('rankedwars', [])
            if not ranked_wars:
                return None

            latest = ranked_wars[0]
            ranked_war_id = latest.get('id')

            report_url = f"{self.base_url}/faction/{ranked_war_id}/rankedwarreport"
            report_resp = requests.get(report_url, params={"key": api_key}, timeout=10)
            report_resp.raise_for_status()
            report = report_resp.json().get('rankedwarreport')

            if not report:
                return None

            factions = report.get('factions', [])
            our_faction = next((f for f in factions if f.get('id') == faction_id), None)
            opponent = next((f for f in factions if f.get('id') != faction_id), None)

            if not our_faction or not opponent:
                return None

            return {
                'ranked_war_id': ranked_war_id,
                'start': report.get('start'),
                'end': report.get('end'),
                'opposing_faction_name': opponent.get('name'),
                'our_faction_name': our_faction.get('name'),
                'members': our_faction.get('members', [])
            }

        except requests.exceptions.RequestException as e:
            print(f"Torn API error: {e}")
            return None
    
    def get_faction_members_with_hits(self, faction_id, user_torn_id, api_key):
        """
        Get faction members and their war hit counts.
        
        Args:
            faction_id: Faction ID
            user_torn_id: User making the request (for audit logging)
            api_key: Torn API key (cached for session only)
            
        Returns:
            list: Member data with hit counts
        """
        try:
            if not api_key:
                raise ValueError("Session API key not found")
            
            # Get faction data with war stats
            url = f"{self.base_url}/faction"
            headers = {"Authorization": f"Bearer {api_key}"}
            params = {"selections": "basic,attacks"}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            faction_data = response.json()
            
            # Extract member info
            members = []
            faction_members = faction_data.get('members', {})
            attacks = faction_data.get('attacks', {})
            
            # Count hits per member from attacks
            hit_counts = {}
            for attack_id, attack in attacks.items():
                attacker_id = attack.get('attacker_id')
                if attacker_id and attack.get('result') in ['Hospitalized', 'Mugged', 'Lost']:
                    hit_counts[attacker_id] = hit_counts.get(attacker_id, 0) + 1
            
            for torn_id, member_data in faction_members.items():
                members.append({
                    'torn_id': int(torn_id),
                    'name': member_data.get('name'),
                    'hit_count': hit_counts.get(int(torn_id), 0),
                    'level': member_data.get('level'),
                    'status': member_data.get('last_action', {}).get('status')
                })
            
            # Update last refresh timestamp
            FactionConfig.update_refresh_timestamp(faction_id)
            
            # Log API call
            AuditLog.create(
                action_type='TORN_API_FETCH',
                user_torn_id=user_torn_id,
                details=f"Fetched {len(members)} faction members with hit counts"
            )
            
            return members
            
        except requests.exceptions.RequestException as e:
            print(f"Torn API error: {e}")
            # Log error
            AuditLog.create(
                action_type='TORN_API_ERROR',
                user_torn_id=user_torn_id,
                details=f"Error fetching faction data: {str(e)}"
            )
            raise Exception(f"Failed to fetch faction data: {str(e)}")

torn_api_service = TornAPIService()
