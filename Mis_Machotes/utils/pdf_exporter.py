from reportlab.lib import colors
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def get_logo_table(app_instance, title_text, title_style):
    logo_path = Path("Mis_Machotes/app_data/custom_logo.png").resolve()
    if app_instance:
        from core.config import OUTPUT_DIR
        logo_path = Path(app_instance.app_state.config.get("output_dir", OUTPUT_DIR)).parent / "app_data" / "custom_logo.png"

    if logo_path.exists():
        try:
            from PIL import Image
            img = Image.open(logo_path)
            w, h = img.size
            max_width = 2 * inch
            if w > max_width:
                aspect = h / float(w)
                w = max_width
                h = w * aspect
            else:
                aspect = h / float(w)
                w = max_width
                h = w * aspect

            rl_img = RLImage(str(logo_path), width=w, height=h)
            header_table = Table([[rl_img, Paragraph(title_text, title_style)]], colWidths=[2.5*inch, 4*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
            ]))
            return header_table
        except Exception as e:
            print(f"Error cargando logo para PDF: {e}")
            return None
    return None

def export_executive_report_pdf(pdf_path, kpis, filters, summary_rows, state_rows, app_instance=None):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, spaceAfter=10, alignment=1)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=6)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=16, spaceAfter=10, spaceBefore=15, textColor=colors.HexColor("#2C3E50"))

    # Header
    title_text = f"Reporte Ejecutivo"
    logo_table = get_logo_table(app_instance, title_text, title_style)

    if logo_table:
        elements.append(logo_table)
        elements.append(Spacer(1, 0.3 * inch))
    else:
        elements.append(Paragraph(title_text, title_style))
        elements.append(Spacer(1, 0.2 * inch))

    # Meta
    elements.append(Paragraph(f"<b>Generado:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    elements.append(Paragraph(f"<b>Estado Filtrado:</b> {filters.get('Estado', 'Todos')}", subtitle_style))
    elements.append(Paragraph(f"<b>Periodo:</b> {filters.get('Periodo', 'Todo')} (De {filters.get('Desde')} a {filters.get('Hasta')})", subtitle_style))
    elements.append(Spacer(1, 0.2 * inch))

    # KPIs Table
    elements.append(Paragraph("Indicadores Clave de Rendimiento (KPIs)", section_style))
    kpi_data = []
    for k, v in kpis.items():
        kpi_data.append([Paragraph(f"<b>{k}</b>", styles['Normal']), Paragraph(str(v), styles['Normal'])])

    kpi_table = Table(kpi_data, colWidths=[3*inch, 4*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#DEE2E6")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(kpi_table)

    # Branches Table
    elements.append(Paragraph("Resumen por Sucursal", section_style))
    summary_data = [["Sucursal", "Cantidad", "% del Total", "Total ($)"]] + summary_rows
    summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#FFFFFF")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
    ]))
    elements.append(summary_table)

    # State by Branch Table
    elements.append(Paragraph("Desglose de Estados por Sucursal", section_style))
    state_data = [["Sucursal", "% Disponibles", "% Usados", "% XML"]] + state_rows
    state_table = Table(state_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    state_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#34495E")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#FFFFFF")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
    ]))
    elements.append(state_table)

    doc.build(elements)


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

    # Check for custom logo
    logo_path = Path("Mis_Machotes/app_data/custom_logo.png").resolve()
    # If app_instance is passed, try to use its config path
    if app_instance:
        from core.config import OUTPUT_DIR
        logo_path = Path(app_instance.app_state.config.get("output_dir", OUTPUT_DIR)).parent / "app_data" / "custom_logo.png"

    if logo_path.exists():
        try:
            from PIL import Image
            img = Image.open(logo_path)
            w, h = img.size
            # Max width 2 inches, keep aspect ratio
            max_width = 2 * inch
            if w > max_width:
                aspect = h / float(w)
                w = max_width
                h = w * aspect
            else:
                aspect = h / float(w)
                w = max_width
                h = w * aspect

            rl_img = RLImage(str(logo_path), width=w, height=h)

            # Use a table to place logo and title side by side
            header_table = Table([[rl_img, Paragraph(title_text, title_style)]], colWidths=[2.5*inch, 4*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 0.3 * inch))
        except Exception as e:
            print(f"Error cargando logo para PDF: {e}")
            elements.append(Paragraph(title_text, title_style))
            elements.append(Spacer(1, 0.2 * inch))
    else:
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
