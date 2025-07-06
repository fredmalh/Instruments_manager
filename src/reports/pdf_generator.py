from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import subprocess
import platform

class PDFGenerator:
    """Base class for PDF report generation"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        # Field label style
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            textColor=colors.grey
        ))
        
        # Field value style
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            textColor=colors.black
        ))
    
    def create_pdf(self, filename, content_elements):
        """Create a PDF file with the given content"""
        try:
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build the PDF
            doc.build(content_elements)
            return True
        except Exception as e:
            print(f"Error creating PDF: {e}")
            return False
    
    def add_header(self, title):
        """Add a header to the PDF"""
        elements = []
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 20))
        return elements
    
    def add_footer(self, canvas, doc):
        """Add footer with page numbers"""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(doc.leftMargin, doc.bottomMargin/2, f"Page {doc.page}")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin/2, 
                             f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        canvas.restoreState()
    
    def create_info_table(self, data):
        """Create a formatted table for information display"""
        if not data:
            return []
        
        # Convert data to table format
        table_data = []
        for key, value in data.items():
            table_data.append([key, value])
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return [table, Spacer(1, 20)]
    
    def open_pdf(self, filename):
        """Open the generated PDF file"""
        try:
            if platform.system() == 'Windows':
                os.startfile(filename)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', filename])
            else:  # Linux
                subprocess.run(['xdg-open', filename])
            return True
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return False 