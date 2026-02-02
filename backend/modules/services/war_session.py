"""War session management service."""
from modules.models.models import WarSession, Member, AuditLog
from modules.services.torn_api import torn_api_service
from modules.services.auth import auth_service
from datetime import datetime
from typing import Dict, Any, cast

class WarSessionService:
    """Service for managing war sessions."""
    
    @staticmethod
    def create_war_session(war_name, torn_id, faction_id):
        """
        Create a new war session.
        
        Args:
            war_name: Name for the war session (optional, will use date if not provided)
            torn_id: User creating the session
            faction_id: Faction ID
            
        Returns:
            dict: Created war session info
        """
        # Generate war name if not provided
        if not war_name or war_name.strip() == '':
            war_name = f"War Session - {datetime.now().strftime('%b %d %Y')}"
        
        try:
            api_key = auth_service.get_session_api_key(torn_id)
            if not api_key:
                raise ValueError("Session API key not found. Please re-login.")

            ranked_summary = torn_api_service.get_latest_ranked_war_summary(api_key, faction_id)
            if not ranked_summary:
                raise ValueError("Unable to fetch ranked war data")

            start_ts = ranked_summary.get('start')
            end_ts = ranked_summary.get('end')

            war_session = cast(Dict[str, Any], WarSession.create(
                war_name,
                torn_id,
                ranked_war_id=ranked_summary.get('ranked_war_id'),
                opposing_faction_name=ranked_summary.get('opposing_faction_name'),
                war_start_timestamp=datetime.utcfromtimestamp(float(start_ts)) if start_ts else None,
                war_end_timestamp=datetime.utcfromtimestamp(float(end_ts)) if end_ts else None
            ))

            # Populate members from ranked war report (only on creation)
            members = ranked_summary.get('members', [])
            for member in members:
                Member.upsert(
                    war_session_id=war_session['session_id'],
                    torn_id=member.get('id'),
                    name=member.get('name'),
                    hit_count=member.get('attacks', 0),
                    score=member.get('score', 0),
                    member_status='active'
                )
            
            # Log creation
            AuditLog.create(
                action_type='WAR_SESSION_CREATED',
                user_torn_id=torn_id,
                war_session_id=war_session['session_id'],
                details=f"Created war session: {war_name}"
            )
            
            return war_session
            
        except ValueError as e:
            raise e

    @staticmethod
    def get_war_details(session_id):
        """
        Get detailed information for a specific war session.
        
        Args:
            session_id: War session UUID
            
        Returns:
            dict: War session details with members
        """
        # Get war session info
        war = cast(Dict[str, Any], WarSession.get_by_id(session_id))
        
        if not war:
            return None
        
        # Get members for this war
        members = cast(list[Dict[str, Any]], Member.get_by_session(session_id))
        
        # Format members - Member.get_by_session already decrypts values
        formatted_members = []
        for m in members:
            formatted_members.append({
                'member_id': str(m.get('member_id', '')),
                'torn_id': m.get('torn_id', 0),
                'name': m.get('name', ''),
                'hit_count': m.get('hit_count', 0),  # Already decrypted by Member.get_by_session
                'score': m.get('score', 0),  # Already decrypted by Member.get_by_session
                'bonus_amount': float(m.get('bonus_amount', 0)) if m.get('bonus_amount') else 0.0,
                'bonus_reason': m.get('bonus_reason'),
                'member_status': m.get('member_status', 'active')
            })
        
        # Format war session
        start_dt = war.get('war_start_timestamp')
        end_dt = war.get('war_end_timestamp')
        
        return {
            'session_id': str(war.get('session_id', '')),
            'war_name': war.get('war_name', ''),
            'status': 'completed' if war.get('completed_timestamp') else 'active',
            'ranked_war_id': war.get('ranked_war_id'),
            'opposing_faction_name': war.get('opposing_faction_name'),
            'war_start_timestamp': start_dt.isoformat() if start_dt else None,
            'war_end_timestamp': end_dt.isoformat() if end_dt else None,
            'total_earnings': float(war.get('total_earnings', 0)) if war.get('total_earnings') else 0.0,
            'price_per_hit': float(war.get('price_per_hit', 0)) if war.get('price_per_hit') else 0.0,
            'created_timestamp': war.get('created_timestamp').isoformat() if war.get('created_timestamp') else None,
            'completed_timestamp': war.get('completed_timestamp').isoformat() if war.get('completed_timestamp') else None,
            'members': formatted_members,
            'member_count': len(formatted_members)
        }
    
    @staticmethod
    def complete_war_session(session_id, torn_id):
        """
        Mark war session as completed and fetch final member data.
        
        Args:
            session_id: War session UUID
            torn_id: User completing the session
            
        Returns:
            dict: Completed war session info
        """
        # Get war details to fetch final rankedwarreport
        war = cast(Dict[str, Any], WarSession.get_by_id(session_id))
        
        if not war:
            raise ValueError("War session not found")
        
        # Fetch final rankedwarreport to get updated hit counts and scores
        faction_id = war.get('ranked_war_id')
        if faction_id:
            try:
                api_key = auth_service.get_session_api_key(torn_id)
                if api_key and war.get('ranked_war_id'):
                    ranked_summary = torn_api_service.get_latest_ranked_war_summary(api_key, 
                                                                                   war.get('created_by_torn_id') or torn_id)
                    if ranked_summary:
                        # Update members with final data
                        members = ranked_summary.get('members', [])
                        for member in members:
                            Member.upsert(
                                war_session_id=session_id,
                                torn_id=member.get('id'),
                                name=member.get('name'),
                                hit_count=member.get('attacks', 0),
                                score=member.get('score', 0),
                                member_status='active'
                            )
            except Exception as e:
                print(f"Warning: Could not fetch final rankedwarreport: {e}")
                # Continue with completion even if fetch fails
        
        # Mark war as completed
        result = cast(Dict[str, Any], WarSession.complete(session_id))
        
        if not result:
            raise ValueError("War session not found")
        
        # Log completion
        AuditLog.create(
            action_type='WAR_SESSION_COMPLETED',
            user_torn_id=torn_id,
            war_session_id=session_id,
            details=f"Completed war session"
        )
        
        return {
            'session_id': str(result['session_id']),
            'status': result['status'],
            'completed_timestamp': result['completed_timestamp'].isoformat()
        }

    @staticmethod
    def sync_members_from_torn(faction_id, war_session_id, torn_id):
        """
        Sync faction members and hit counts from Torn API into a war session.

        Args:
            faction_id: Faction ID
            war_session_id: War session UUID
            torn_id: User making the request

        Returns:
            dict: Result summary
        """
        api_key = auth_service.get_session_api_key(torn_id)
        if not api_key:
            raise ValueError("Session API key not found. Please re-login.")

        members = torn_api_service.get_faction_members_with_hits(faction_id, torn_id, api_key)

        updated_count = 0
        for member in members:
            Member.upsert(
                war_session_id=war_session_id,
                torn_id=member.get('torn_id'),
                name=member.get('name'),
                hit_count=member.get('hit_count', 0),
                score=None,
                member_status='active'
            )
            updated_count += 1

        AuditLog.create(
            action_type='MEMBERS_REFRESHED',
            user_torn_id=torn_id,
            war_session_id=war_session_id,
            details=f"Refreshed {updated_count} members from Torn"
        )

        return {
            'message': 'Members refreshed successfully',
            'updated_count': updated_count,
            'members': members
        }
    
    @staticmethod
    def get_active_session():
        """Get the currently active war session."""
        session = WarSession.get_active()
        
        if not session:
            return None
        
        start_dt = session.get('war_start_timestamp')
        end_dt = session.get('war_end_timestamp')

        return {
            'session_id': str(session['session_id']),
            'war_name': session['war_name'],
            'ranked_war_id': session.get('ranked_war_id'),
            'opposing_faction_name': session.get('opposing_faction_name'),
            'war_start_timestamp': start_dt.isoformat() if start_dt else None,
            'war_end_timestamp': end_dt.isoformat() if end_dt else None,
            'status': session['status'],
            'total_earnings': float(session.get('total_earnings', 0)) if session.get('total_earnings') else 0.0,
            'price_per_hit': float(session.get('price_per_hit', 0)) if session.get('price_per_hit') else 0.0,
            'total_paid': float(session.get('total_paid', 0)) if session.get('total_paid') else 0.0,
            'remaining_balance': float(session.get('remaining_balance', 0)) if session.get('remaining_balance') else 0.0,
            'created_timestamp': session['created_timestamp'].isoformat() if session.get('created_timestamp') else None
        }
    
    @staticmethod
    def get_completed_sessions():
        """Get all completed war sessions."""
        sessions = cast(list[Dict[str, Any]], WarSession.get_all_completed())
        
        results = []
        for s in sessions:
            # Get member count and total hits for this session
            members = cast(list[Dict[str, Any]], Member.get_by_session(s['session_id']))
            total_hits = sum(int(m.get('hit_count', 0) or 0) for m in members)
            
            start_dt = s.get('war_start_timestamp')
            end_dt = s.get('war_end_timestamp')
            results.append({
                'session_id': str(s['session_id']),
                'war_name': s['war_name'],
                'member_count': len(members),
                'total_hits': total_hits,
                'ranked_war_id': s.get('ranked_war_id'),
                'opposing_faction_name': s.get('opposing_faction_name'),
                'war_start_timestamp': start_dt.isoformat() if start_dt else None,
                'war_end_timestamp': end_dt.isoformat() if end_dt else None,
                'total_earnings': float(s.get('total_earnings', 0)) if s.get('total_earnings') else 0.0,
                'price_per_hit': float(s.get('price_per_hit', 0)) if s.get('price_per_hit') else 0.0,
                'created_timestamp': s['created_timestamp'].isoformat() if s.get('created_timestamp') else None,
                'completed_timestamp': s['completed_timestamp'].isoformat() if s.get('completed_timestamp') else None
            })

        return results

    @staticmethod
    def get_faction_wars(faction_id: int):
        """Get all war sessions for a faction."""
        sessions = cast(list[Dict[str, Any]], WarSession.get_by_faction(faction_id))
        
        results = []
        for s in sessions:
            start_dt = s.get('war_start_timestamp')
            end_dt = s.get('war_end_timestamp')
            status = 'completed' if s.get('completed_timestamp') else 'active'
            
            earnings = s.get('total_earnings')
            price_hit = s.get('price_per_hit')
            results.append({
                'session_id': str(s.get('session_id', '')),
                'war_name': s.get('war_name', ''),
                'status': status,
                'ranked_war_id': s.get('ranked_war_id'),
                'opposing_faction_name': s.get('opposing_faction_name'),
                'war_start_timestamp': start_dt.isoformat() if start_dt else None,
                'war_end_timestamp': end_dt.isoformat() if end_dt else None,
                'total_earnings': float(earnings) if earnings else 0.0,
                'price_per_hit': float(price_hit) if price_hit else 0.0,
                'created_timestamp': s.get('created_timestamp').isoformat() if s.get('created_timestamp') else None,
                'completed_timestamp': s.get('completed_timestamp').isoformat() if s.get('completed_timestamp') else None,
                'member_count': int(s.get('member_count', 0)) if s.get('member_count') else 0
            })

        return sorted(results, key=lambda x: x['created_timestamp'] or '', reverse=True)

war_session_service = WarSessionService()
