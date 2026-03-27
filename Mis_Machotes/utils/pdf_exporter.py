from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def export_machote_pdf(pdf_path, filename, empresa, rfc, fecha, items, app_instance=None):
    """
    Exporta la información de un machote a un PDF con estilo profesional.
    """
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=10,
        alignment=1 # Center
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )

    # Header Information
    title_text = f"Reporte de Machote"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(f"<b>Archivo:</b> {filename}", subtitle_style))
    elements.append(Paragraph(f"<b>Empresa:</b> {empresa}", subtitle_style))
    elements.append(Paragraph(f"<b>RFC:</b> {rfc}", subtitle_style))
    elements.append(Paragraph(f"<b>Fecha de Creación:</b> {fecha}", subtitle_style))
    elements.append(Paragraph(f"<b>Total de Piezas:</b> {len(items)}", subtitle_style))

    elements.append(Spacer(1, 0.3 * inch))

    # Table Data
    data = [["Sucursal", "Modelo", "Serie", "Total"]]

    total_sum = 0
    for item in items:
        # Formatear el total (ej. $ 1,000.00)
        try:
            val = float(item['total'])
            total_sum += val
            formatted_total = f"${val:,.2f}"
        except:
            formatted_total = str(item['total'])

        data.append([
            str(item['sucursal']),
            str(item['modelo']),
            str(item['serie']),
            formatted_total
        ])

    # Add Total Row
    data.append(["", "", "Total General:", f"${total_sum:,.2f}"])

    # Create Table
    col_widths = [1.5*inch, 2*inch, 2*inch, 1*inch]
    table = Table(data, colWidths=col_widths)

    # Table Style
    t_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#ECF0F1")),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        # Total Row Style
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#BDC3C7")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, -1), (3, -1), 'RIGHT'),
        ('GRID', (2, -1), (3, -1), 1, colors.black),
    ])

    table.setStyle(t_style)
    elements.append(table)

    # Build PDF
    doc.build(elements)
