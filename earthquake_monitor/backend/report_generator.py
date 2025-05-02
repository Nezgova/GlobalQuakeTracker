from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus import PageBreak, KeepTogether, ListFlowable, ListItem
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime
import os
import tempfile
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import numpy as np
import io
import base64

def generate_report(earthquakes, analysis_results, title, center_lat, center_lon, radius_km):
    """
    Generate a PDF report for the earthquake hazard analysis.
    
    Args:
        earthquakes (dict): Processed earthquake data
        analysis_results (dict): Results of hazard analysis
        title (str): Report title
        center_lat (float): Latitude of location
        center_lon (float): Longitude of location
        radius_km (float): Analysis radius in kilometers
        
    Returns:
        str: Path to generated PDF file
    """
    # Create a temporary file for the PDF
    temp_dir = tempfile.gettempdir()
    file_name = f"earthquake_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(temp_dir, file_name)
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading1']
    heading2_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='SmallText',
        parent=styles['Normal'],
        fontSize=8
    ))
    
    styles.add(ParagraphStyle(
        name='Warning',
        parent=styles['Normal'],
        textColor=colors.red,
        fontName='Helvetica-Bold'
    ))
    
    # Create document content
    content = []
    
    # Add title
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add report generation info
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content.append(Paragraph(f"Report Generated: {report_date}", styles['SmallText']))
    content.append(Spacer(1, 0.25*inch))
    
    # Add location information
    content.append(Paragraph("Analysis Location", heading_style))
    location_data = [
        ["Latitude:", f"{center_lat:.4f}°"],
        ["Longitude:", f"{center_lon:.4f}°"],
        ["Analysis Radius:", f"{radius_km} km"]
    ]
    location_table = Table(location_data, colWidths=[2*inch, 2*inch])
    location_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(location_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add hazard summary
    content.append(Paragraph("Hazard Summary", heading_style))
    
    hazard_level = analysis_results.get("hazard_level", "unknown")
    hazard_score = analysis_results.get("hazard_score", 0)
    hazard_color = {
        "low": colors.green,
        "moderate": colors.orange,
        "high": colors.red,
        "very_high": colors.darkred,
        "unknown": colors.grey
    }.get(hazard_level, colors.grey)
    
    # Create hazard level paragraph with correct color
    hazard_style = ParagraphStyle(
        name='HazardLevel',
        parent=styles['Heading2'],
        textColor=hazard_color
    )
    
    content.append(Paragraph(f"Hazard Level: {hazard_level.upper()} (Score: {hazard_score}/100)", hazard_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add key metrics
    content.append(Paragraph("Key Metrics", heading2_style))
    
    metrics = analysis_results.get("metrics", {})
    earthquake_count = metrics.get("earthquake_count", 0)
    max_magnitude = metrics.get("max_magnitude", "N/A")
    avg_magnitude = metrics.get("avg_magnitude", "N/A")
    days_since_recent = metrics.get("days_since_recent", "N/A")
    avg_interval = metrics.get("avg_interval_days", "N/A")
    pga_estimate = metrics.get("pga_estimate", "N/A")
    
    metrics_data = [
        ["Metric", "Value", "Interpretation"],
        ["Earthquake Count", str(earthquake_count), interpret_count(earthquake_count)],
        ["Maximum Magnitude", str(max_magnitude), interpret_magnitude(max_magnitude)],
        ["Average Magnitude", str(avg_magnitude), ""],
        ["Days Since Recent Event", str(days_since_recent), interpret_recency(days_since_recent)],
        ["Avg. Interval (days)", str(avg_interval), ""],
        ["Est. Peak Ground Acceleration", f"{pga_estimate} g" if pga_estimate != "N/A" else "N/A", interpret_pga(pga_estimate)]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2*inch, 1.2*inch, 3.3*inch])
    metrics_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(metrics_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add nearest earthquakes list
    content.append(Paragraph("Nearest Earthquakes", heading2_style))
    
    nearest_quakes = analysis_results.get("nearest_earthquakes", [])
    if nearest_quakes:
        quake_data = [["Magnitude", "Depth (km)", "Distance (km)", "Date", "Location"]]
        for quake in nearest_quakes:
            quake_data.append([
                str(quake.get("magnitude", "N/A")),
                str(quake.get("depth", "N/A")),
                str(quake.get("distance", "N/A")),
                quake.get("date", "N/A").split("T")[0],  # Just show the date part
                quake.get("location", "Unknown")
            ])
        
        quakes_table = Table(quake_data, colWidths=[0.7*inch, 0.8*inch, 1*inch, 1*inch, 3*inch])
        quakes_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        content.append(quakes_table)
    else:
        content.append(Paragraph("No nearby earthquakes found.", normal_style))
    
    content.append(Spacer(1, 0.25*inch))
    
    # Add magnitude distribution chart if we have enough data
    if len(earthquakes.get("features", [])) >= 3:
        content.append(Paragraph("Magnitude Distribution", heading2_style))
        
        # Generate magnitude distribution chart
        magnitude_chart = create_magnitude_chart(earthquakes)
        content.append(magnitude_chart)
        content.append(Spacer(1, 0.25*inch))
    
    # Add page break before recommendations
    content.append(PageBreak())
    
    # Add recommendations
    content.append(Paragraph("Risk Assessment & Recommendations", heading_style))
    
    # Add risk explanation based on hazard level
    risk_explanations = {
        "low": ("Low seismic risk in this area based on recent activity. However, this does not rule out the possibility of earthquakes.", colors.green),
        "moderate": ("Moderate seismic risk in this area. There is notable seismic activity that warrants attention.", colors.orange),
        "high": ("High seismic risk in this area. Significant seismic activity indicates potential for damaging earthquakes.", colors.red),
        "very_high": ("Very high seismic risk in this area. Recent significant seismic activity indicates high potential for damaging earthquakes.", colors.darkred),
        "unknown": ("Unable to determine seismic risk from available data.", colors.grey)
    }
    
    risk_text, risk_color = risk_explanations.get(hazard_level, risk_explanations["unknown"])
    
    risk_style = ParagraphStyle(
        name='RiskText',
        parent=styles['Normal'],
        textColor=risk_color,
        fontName='Helvetica-Bold'
    )
    
    content.append(Paragraph(risk_text, risk_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add general recommendations
    content.append(Paragraph("General Recommendations:", heading2_style))
    
    recommendations = get_recommendations(hazard_level)
    for rec in recommendations:
        content.append(Paragraph(f"• {rec}", normal_style))
        content.append(Spacer(1, 0.1*inch))
    
    content.append(Spacer(1, 0.25*inch))
    
    # Add disclaimer
    content.append(Paragraph("Disclaimer", heading2_style))
    disclaimer_text = (
        "This report provides a simplified assessment based on recent seismic activity and "
        "does not constitute a comprehensive seismic hazard analysis. The analysis uses "
        "publicly available earthquake data and applies simplified models to estimate hazard levels. "
        "For critical infrastructure or safety decisions, please consult with qualified "
        "seismic hazard experts and refer to official hazard maps from geological surveys."
    )
    content.append(Paragraph(disclaimer_text, styles['SmallText']))
    
    # Build the PDF document
    doc.build(content)
    
    return file_path

def interpret_count(count):
    """Interpret earthquake count significance"""
    if count is None or count == "N/A":
        return "Insufficient data"
    count = float(count)
    if count == 0:
        return "No recent seismic activity in this area"
    elif count < 5:
        return "Low level of seismic activity"
    elif count < 15:
        return "Moderate level of seismic activity"
    elif count < 30:
        return "High level of seismic activity"
    else:
        return "Very high level of seismic activity"

def interpret_magnitude(magnitude):
    """Interpret earthquake magnitude significance"""
    if magnitude is None or magnitude == "N/A":
        return "Insufficient data"
    magnitude = float(magnitude)
    if magnitude < 4.0:
        return "Minor earthquakes, rarely cause damage"
    elif magnitude < 5.0:
        return "Light earthquakes, minor damage possible"
    elif magnitude < 6.0:
        return "Moderate earthquakes, can cause damage"
    elif magnitude < 7.0:
        return "Strong earthquakes, potential for significant damage"
    else:
        return "Major earthquakes, serious damage likely"

def interpret_recency(days):
    """Interpret significance of days since most recent earthquake"""
    if days is None or days == "N/A":
        return "Insufficient data"
    days = float(days)
    if days < 1:
        return "Very recent activity (less than 24 hours)"
    elif days < 7:
        return "Recent activity (less than a week)"
    elif days < 30:
        return "Activity within the past month"
    else:
        return "No very recent activity"

def interpret_pga(pga):
    """Interpret Peak Ground Acceleration significance"""
    if pga is None or pga == "N/A":
        return "Insufficient data"
    pga = float(pga)
    if pga < 0.01:
        return "Not felt (I on Modified Mercalli Scale)"
    elif pga < 0.05:
        return "Weak shaking (II-III on Modified Mercalli Scale)"
    elif pga < 0.10:
        return "Light shaking (IV on Modified Mercalli Scale)"
    elif pga < 0.20:
        return "Moderate shaking (V on Modified Mercalli Scale)"
    elif pga < 0.40:
        return "Strong shaking (VI-VII on Modified Mercalli Scale)"
    else:
        return "Very strong to severe shaking (VIII+ on Modified Mercalli Scale)"

def get_recommendations(hazard_level):
    """Get recommendations based on hazard level"""
    common_recs = [
        "Stay informed about local seismic hazards and preparedness measures.",
        "Have an emergency plan and supplies ready for all household members.",
        "Secure heavy furniture and objects that could fall during an earthquake.",
        "Know how to shut off utilities in case of emergency."
    ]
    
    specific_recs = {
        "low": [
            "Basic earthquake preparedness is still recommended despite low recent activity.",
            "Consider a basic emergency kit with water, food, and first aid supplies."
        ],
        "moderate": [
            "Review and practice earthquake safety procedures with all household members.",
            "Check home for potential hazards and consider basic retrofitting if needed.",
            "Prepare a more comprehensive emergency kit."
        ],
        "high": [
            "Consider professional assessment of building safety and potential retrofitting needs.",
            "Develop a detailed family emergency and communication plan.",
            "Prepare a comprehensive emergency kit for at least 72 hours of self-sufficiency.",
            "Consider earthquake insurance coverage."
        ],
        "very_high": [
            "Urgently assess building safety and implement recommended retrofits.",
            "Prepare for potential extended disruption to utilities and services.",
            "Develop evacuation plans and identify safe locations.",
            "Consider temporary relocation if in a highly vulnerable structure.",
            "Ensure comprehensive earthquake insurance coverage."
        ],
        "unknown": [
            "Consult local geological surveys for more accurate hazard assessment.",
            "Follow general earthquake preparedness guidelines for your region."
        ]
    }
    
    return specific_recs.get(hazard_level, specific_recs["unknown"]) + common_recs

def create_magnitude_chart(earthquakes):
    """Create a magnitude distribution chart"""
    features = earthquakes.get("features", [])
    
    # Extract magnitudes
    magnitudes = [eq["properties"]["mag"] for eq in features if "mag" in eq["properties"]]
    
    if not magnitudes:
        return Paragraph("No magnitude data available for chart.", getSampleStyleSheet()['Normal'])
    
    # Create bins for magnitude ranges
    bins = np.arange(math.floor(min(magnitudes)), math.ceil(max(magnitudes)) + 0.5, 0.5)
    
    # Create Matplotlib figure
    plt.figure(figsize=(6, 4))
    plt.hist(magnitudes, bins=bins, edgecolor='black', alpha=0.7)
    plt.xlabel('Magnitude')
    plt.ylabel('Number of Earthquakes')
    plt.title('Earthquake Magnitude Distribution')
    plt.grid(True, alpha=0.3)
    
    # Save figure to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    buf.seek(0)
    
    # Create ReportLab Image
    img = Image(buf)
    img.drawHeight = 3*inch
    img.drawWidth = 4.5*inch
    
    return img

import math  # Added for math.floor and math.ceil functions