"""Calculator service for war payouts.""" 
from models.models import Member, OtherPayment, WarSession, MemberPayout, AuditLog
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any

class CalculatorService:
    """Service for calculating war payouts."""
    
    @staticmethod
    def calculate_payouts(war_session_id, total_earnings, price_per_hit):
        """
        Calculate all payouts for a war session.
        
        Args:
            war_session_id: War session UUID
            total_earnings: Total money earned from war
            price_per_hit: Price per hit
            
        Returns:
            dict: Complete payout breakdown
        """
        # Get all members
        members = Member.get_by_session(war_session_id)
        
        # Get all other payments
        other_payments = OtherPayment.get_by_session(war_session_id)
        
        # Calculate member payouts
        member_payouts: List[Dict[str, Any]] = []
        total_member_payout = Decimal('0')
        
        for member in members:
            hit_count = int(member.get('hit_count', 0))
            base_payout = Decimal(str(price_per_hit)) * Decimal(str(hit_count))
            
            bonus_amount = Decimal('0')
            if member.get('bonus_amount'):
                try:
                    bonus_amount = Decimal(str(member['bonus_amount']))
                except:
                    bonus_amount = Decimal('0')
            
            member_total = base_payout + bonus_amount
            total_member_payout += member_total
            
            member_payouts.append({
                'member_id': member['member_id'],
                'torn_id': member['torn_id'],
                'name': member['name'],
                'hit_count': hit_count,
                'base_payout': float(base_payout.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'bonus_amount': float(bonus_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'bonus_reason': member.get('bonus_reason', ''),
                'total_payout': float(member_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'member_status': member.get('member_status', 'active')
            })
        
        # Calculate other payments total
        total_other_payments = Decimal('0')
        other_payment_list: List[Dict[str, Any]] = []
        
        for payment in other_payments:
            try:
                amount = Decimal(str(payment['amount']))
            except:
                amount = Decimal('0')
            
            total_other_payments += amount
            
            other_payment_list.append({
                'payment_id': payment['payment_id'],
                'amount': float(amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'description': payment['description']
            })
        
        # Calculate totals
        total_paid = total_member_payout + total_other_payments
        total_earnings_decimal = Decimal(str(total_earnings))
        remaining_balance = total_earnings_decimal - total_paid
        
        # Update war session with calculations
        WarSession.update_calculations(
            session_id=war_session_id,
            total_earnings=float(total_earnings_decimal),
            price_per_hit=float(Decimal(str(price_per_hit))),
            total_paid=float(total_paid.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            remaining_balance=float(remaining_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        )
        
        # Delete existing payouts and save new ones
        try:
            MemberPayout.delete_by_session(war_session_id)
            for mp in member_payouts:
                MemberPayout.create(
                    war_session_id=war_session_id,
                    member_id=mp['member_id'],
                    torn_id=mp['torn_id'],
                    name=mp['name'],
                    hit_count=mp['hit_count'],
                    base_payout=mp['base_payout'],
                    bonus_amount=mp['bonus_amount'],
                    total_payout=mp['total_payout'],
                    bonus_reason=mp.get('bonus_reason'),
                    member_status=mp.get('member_status', 'active')
                )
            print(f"[CALCULATOR] ✓ Saved {len(member_payouts)} member payouts to database")
        except Exception as e:
            print(f"[CALCULATOR] ⚠ Could not save member payouts to database: {e}")
            import traceback
            traceback.print_exc()
            # Continue anyway - calculations are still valid, just not persisted
        
        return {
            'war_session_id': str(war_session_id),
            'total_earnings': float(total_earnings_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'price_per_hit': float(Decimal(str(price_per_hit)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'member_payouts': member_payouts,
            'total_member_payout': float(total_member_payout.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'other_payments': other_payment_list,
            'total_other_payments': float(total_other_payments.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'total_paid': float(total_paid.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'remaining_balance': float(remaining_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        }
    
    @staticmethod
    def get_payout_summary(war_session_id):
        """Get payout summary for a war session."""
        war_session = WarSession.get_by_id(war_session_id)
        
        if not war_session:
            return None
        
        members = Member.get_by_session(war_session_id)
        other_payments = OtherPayment.get_by_session(war_session_id)
        
        # Calculate current totals
        total_hits = sum(int(m.get('hit_count', 0)) for m in members)
        
        return {
            'war_session_id': str(war_session_id),
            'war_name': war_session['war_name'],  # type: ignore
            'status': war_session['status'],  # type: ignore
            'total_earnings': float(war_session.get('total_earnings', 0)),  # type: ignore
            'price_per_hit': float(war_session.get('price_per_hit', 0)),  # type: ignore
            'total_paid': float(war_session.get('total_paid', 0)) if war_session.get('total_paid') else 0,  # type: ignore
            'remaining_balance': float(war_session.get('remaining_balance', 0)) if war_session.get('remaining_balance') else 0,  # type: ignore
            'total_members': len(members),
            'total_hits': total_hits,
            'total_other_payments': len(other_payments),
            'created_timestamp': war_session['created_timestamp'].isoformat() if war_session.get('created_timestamp') else None  # type: ignore
        }

calculator_service = CalculatorService()
