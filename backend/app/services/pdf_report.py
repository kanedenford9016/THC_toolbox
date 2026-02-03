"""PDF report generation service."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
from models.models import WarSession, Member, OtherPayment
from services.calculator import calculator_service

# Blue/Gray professional color scheme
BLUE_DARK = colors.HexColor('#1a365d')
BLUE_MED = colors.HexColor('#2c5282')
BLUE_LIGHT = colors.HexColor('#4299e1')
GRAY_DARK = colors.HexColor('#2d3748')
GRAY_MED = colors.HexColor('#718096')
GRAY_LIGHT = colors.HexColor('#e2e8f0')

class PDFReportService:
    """Service for generating professional PDF war reports."""
    
    @staticmethod
    def generate_war_report(war_session_id, generated_by_name):
        """
        Generate a professional PDF war report.
        
        Args:
            war_session_id: War session UUID
            generated_by_name: Name of the user generating the report
            
        Returns:
            BytesIO: PDF file buffer
        """
        # Get war session data
        war_session = WarSession.get_by_id(war_session_id)
        if not war_session:
            raise ValueError("War session not found")
        
        # Get payout data - use saved payouts if available, otherwise calculate
        from models.models import MemberPayout
        saved_payouts = MemberPayout.get_by_session(war_session_id)
        
        if saved_payouts and len(saved_payouts) > 0:
            # Use saved payouts (fast)
            payout_data = {
                'member_payouts': saved_payouts,
                'total_payout': sum(float(p.get('total_payout', 0)) for p in saved_payouts),
                'total_hits': sum(int(p.get('hit_count', 0)) for p in saved_payouts),
            }
        else:
            # Fall back to calculation if no saved payouts (slow, for backwards compatibility)
            payout_data = calculator_service.calculate_payouts(
                war_session_id,
                war_session['total_earnings'],  # type: ignore
                war_session['price_per_hit']  # type: ignore
            )
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=1*inch, bottomMargin=0.75*inch)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=BLUE_DARK,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=BLUE_MED,
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=GRAY_DARK,
            spaceAfter=12
        )
        
        # Title
        title = Paragraph(f"<b>War Report</b>", title_style)
        elements.append(title)
        
        # War session info
        war_name = Paragraph(f"<b>{war_session['war_name']}</b>", heading_style)  # type: ignore
        elements.append(war_name)
        
        date_created = war_session['created_timestamp'].strftime('%B %d, %Y %I:%M %p') if war_session.get('created_timestamp') else 'N/A'  # type: ignore
        info_text = f"<b>Date:</b> {date_created}<br/>"
        info_text += f"<b>Status:</b> {war_session['status'].title()}"  # type: ignore
        
        if war_session.get('completed_timestamp'):  # type: ignore
            date_completed = war_session['completed_timestamp'].strftime('%B %d, %Y %I:%M %p')  # type: ignore
            info_text += f"<br/><b>Completed:</b> {date_completed}"
        
        info = Paragraph(info_text, normal_style)
        elements.append(info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary section
        summary_heading = Paragraph("<b>Financial Summary</b>", heading_style)
        elements.append(summary_heading)
        
        summary_data = [
            ['Total War Earnings', f"${payout_data['total_earnings']:,.2f}"],
            ['Price Per Hit', f"${payout_data['price_per_hit']:,.2f}"],
            ['Total Member Payouts', f"${payout_data['total_member_payout']:,.2f}"],
            ['Total Other Payments', f"${payout_data['total_other_payments']:,.2f}"],
            ['Total Paid', f"${payout_data['total_paid']:,.2f}"],
            ['Remaining Balance', f"${payout_data['remaining_balance']:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), GRAY_LIGHT),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), GRAY_DARK),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY_MED),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [GRAY_LIGHT, colors.white]),
            # Highlight remaining balance
            ('BACKGROUND', (0, 5), (-1, 5), BLUE_LIGHT),
            ('TEXTCOLOR', (0, 5), (-1, 5), colors.white),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Member payouts table
        member_heading = Paragraph("<b>Member Payouts</b>", heading_style)
        elements.append(member_heading)
        
        member_headers = ['Member Name', 'Hits', 'Base Payout', 'Bonus', 'Total', 'Status']
        member_data = [member_headers]
        
        for member in payout_data['member_payouts']:
            status_text = '⚠ Left' if member['member_status'] == 'left_faction' else '✓ Active'
            bonus_text = f"${member['bonus_amount']:,.2f}"
            if member['bonus_reason']:
                bonus_text += f"\n({member['bonus_reason'][:20]}...)" if len(member['bonus_reason']) > 20 else f"\n({member['bonus_reason']})"
            
            member_data.append([
                member['name'],
                str(member['hit_count']),
                f"${member['base_payout']:,.2f}",
                bonus_text,
                f"${member['total_payout']:,.2f}",
                status_text
            ])
        
        member_table = Table(member_data, colWidths=[1.8*inch, 0.6*inch, 1*inch, 1.2*inch, 1*inch, 0.9*inch])
        member_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), GRAY_DARK),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY_MED),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
        ]))
        
        elements.append(member_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Other payments table (if any)
        if payout_data['other_payments']:
            other_heading = Paragraph("<b>Other Payments</b>", heading_style)
            elements.append(other_heading)
            
            other_headers = ['Description', 'Amount']
            other_data = [other_headers]
            
            for payment in payout_data['other_payments']:
                other_data.append([
                    payment['description'],
                    f"${payment['amount']:,.2f}"
                ])
            
            other_table = Table(other_data, colWidths=[4.5*inch, 2*inch])
            other_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), GRAY_DARK),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, GRAY_MED),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
            ]))
            
            elements.append(other_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_text = f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>"
        footer_text += f"Generated by: {generated_by_name}"
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=GRAY_MED,
            alignment=TA_CENTER
        )
        
        footer = Paragraph(footer_text, footer_style)
        elements.append(Spacer(1, 0.5*inch))
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and return it
        buffer.seek(0)
        return buffer

pdf_report_service = PDFReportService()
