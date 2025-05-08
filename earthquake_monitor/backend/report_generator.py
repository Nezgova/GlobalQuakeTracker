
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
import math

# FIX: Import functions from hazard_analysis instead of openquake_analysis
from hazard_analysis import perform_hazard_analysis, perform_openquake_hazard_analysis, get_seismic_hazard_summary

def generate_report(earthquakes, analysis_results, title, lat, lon, radius, analysis_type='standard'):
    """
    Generate a PDF report for earthquake hazard analysis.
    
    This is a wrapper function that calls the appropriate report generator based on analysis type.
    
    Args:
        earthquakes (dict): Processed earthquake data
        analysis_results (dict): Results of hazard analysis
        title (str): Report title
        lat (float): Latitude of location
        lon (float): Longitude of location
        radius (float): Analysis radius in kilometers
        analysis_type (str): Type of analysis ('standard', 'advanced', etc.)
        
    Returns:
        str: Path to generated PDF file
    """
    if analysis_type == 'advanced':
        # For advanced analysis, use the enhanced report generator
        traditional_analysis = analysis_results
        openquake_analysis = analysis_results.get('advanced_analysis', {})
        
        return generate_enhanced_report(
            earthquakes, 
            traditional_analysis, 
            openquake_analysis, 
            title, 
            lat, 
            lon, 
            radius
        )
    else:
        # For standard analysis, use the basic report generator
        return generate_basic_report(
            earthquakes,
            analysis_results,
            title,
            lat,
            lon,
            radius
        )

def generate_basic_report(earthquakes, analysis_results, title, center_lat, center_lon, radius_km):
    """
    Generate a basic PDF report for earthquake hazard analysis.
    
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
    try:
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
        
        # Add earthquake statistics - with proper type checking
        content.append(Paragraph("Earthquake Statistics", heading_style))
        
        # Safely extract data from analysis with defaults
        nearby_quakes = analysis_results.get("nearby_earthquakes", [])
        if not isinstance(nearby_quakes, (list, tuple)):
            nearby_quakes = []
            
        mag_distribution = analysis_results.get("magnitude_distribution", {})
        if not isinstance(mag_distribution, dict):
            mag_distribution = {}
            
        time_stats = analysis_results.get("time_statistics", {})
        if not isinstance(time_stats, dict):
            time_stats = {}
        
        quake_count = len(nearby_quakes)
        
        # Add key metrics from analysis
        content.append(Paragraph("Recent Seismic Activity", heading2_style))
        
        time_data = [
            ["Time Period", "Number of Earthquakes"],
            ["Last 24 Hours", str(time_stats.get("last_24h", 0))],
            ["Last 7 Days", str(time_stats.get("last_7d", 0))],
            ["Last 30 Days", str(time_stats.get("last_30d", 0))],
            ["Total in Analysis", str(quake_count)]
        ]
        
        time_table = Table(time_data, colWidths=[2*inch, 2*inch])
        time_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(time_table)
        content.append(Spacer(1, 0.25*inch))
        
        # Add magnitude distribution - with proper type checking
        content.append(Paragraph("Magnitude Distribution", heading2_style))
        
        mag_data = [["Magnitude Range", "Number of Earthquakes"]]
        
        if isinstance(mag_distribution, dict):
            for mag_range, count in mag_distribution.items():
                mag_data.append([str(mag_range), str(count)])
        
        mag_table = Table(mag_data, colWidths=[2*inch, 2*inch])
        mag_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        content.append(mag_table)
        content.append(Spacer(1, 0.25*inch))
        
        # Add magnitude distribution chart if we have enough data
        features = earthquakes.get("features", [])
        if isinstance(features, (list, tuple)) and len(features) >= 3:
            content.append(Paragraph("Earthquake Magnitude Distribution", heading_style))
            
            # Generate magnitude distribution chart
            try:
                magnitude_chart = create_magnitude_chart(earthquakes)
                content.append(magnitude_chart)
                content.append(Spacer(1, 0.25*inch))
            except Exception as e:
                print(f"Error creating magnitude chart: {str(e)}")
                content.append(Paragraph("Could not generate magnitude distribution chart", normal_style))
        
        # Create a new page for earthquake details
        content.append(PageBreak())
        
        # Add nearest earthquakes list with proper type checking
        content.append(Paragraph("Nearest Earthquakes", heading_style))
        
        if nearby_quakes and isinstance(nearby_quakes, (list, tuple)):
            quake_data = [["Magnitude", "Depth (km)", "Distance (km)", "Date", "Location"]]
            for quake in nearby_quakes[:10]:  # Limit to 10 earthquakes
                try:
                    props = quake.get("properties", {})
                    geometry = quake.get("geometry", {})
                    coords = geometry.get("coordinates", [0, 0, 0])
                    
                    quake_data.append([
                        str(props.get("mag", "N/A")),
                        str(props.get("depth", "N/A") if "depth" in props else 
                            (coords[2] if len(coords) > 2 else "N/A")),
                        str(props.get("distance", "N/A")),
                        datetime.fromtimestamp(props.get("time", 0) / 1000).strftime("%Y-%m-%d") if props.get("time") else "N/A",
                        props.get("place", "Unknown")
                    ])
                except Exception as e:
                    print(f"Error processing earthquake data: {str(e)}")
                    continue
            
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
        
        # Add risk assessment
        content.append(Paragraph("Risk Assessment", heading_style))
        
        # Determine risk level based on magnitude and proximity
        risk_level = "Low"
        risk_color = colors.green
        
        # Check for significant earthquakes nearby with proper type checking
        if isinstance(nearby_quakes, (list, tuple)):
            significant_quakes = [q for q in nearby_quakes if isinstance(q, dict) and 
                                q.get("properties", {}).get("mag", 0) >= 5.0]
            close_quakes = [q for q in nearby_quakes if isinstance(q, dict) and 
                           q.get("properties", {}).get("distance", float('inf')) <= 100]
            
            if any(q for q in nearby_quakes if isinstance(q, dict) and 
                  q.get("properties", {}).get("mag", 0) >= 7.0):
                risk_level = "High"
                risk_color = colors.red
            elif significant_quakes and close_quakes:
                risk_level = "Moderate"
                risk_color = colors.orange
        
        risk_style = ParagraphStyle(
            name='RiskText',
            parent=styles['Normal'],
            textColor=risk_color,
            fontName='Helvetica-Bold'
        )
        
        content.append(Paragraph(f"Based on historical earthquake data, this location has a {risk_level.upper()} seismic risk.", risk_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Add recommendations based on risk level
        content.append(Paragraph("Recommendations:", heading2_style))
        
        if risk_level == "High":
            recommendations = [
                "Consider professional assessment of building safety and potential retrofitting needs.",
                "Develop a detailed family emergency and communication plan.",
                "Prepare a comprehensive emergency kit for at least 72 hours of self-sufficiency.",
                "Consider earthquake insurance coverage.",
                "Stay informed about local seismic hazards and preparedness measures."
            ]
        elif risk_level == "Moderate":
            recommendations = [
                "Review and practice earthquake safety procedures with all household members.",
                "Check home for potential hazards and consider basic retrofitting if needed.",
                "Prepare a more comprehensive emergency kit.",
                "Stay informed about local seismic hazards and preparedness measures."
            ]
        else:  # Low
            recommendations = [
                "Implement basic earthquake preparedness despite low hazard.",
                "Consider a basic emergency kit with water, food, and first aid supplies.",
                "Stay informed about local seismic hazards and preparedness measures."
            ]
        
        for rec in recommendations:
            content.append(Paragraph(f"• {rec}", normal_style))
            content.append(Spacer(1, 0.1*inch))
        
        content.append(Spacer(1, 0.25*inch))
        
        # Add disclaimer
        content.append(Paragraph("Disclaimer", heading2_style))
        disclaimer_text = (
            "This report provides an assessment based on historical earthquake data. While it provides valuable insights, "
            "it should not be the sole basis for critical infrastructure or life-safety decisions. For such applications, "
            "please consult with qualified seismic hazard experts and refer to official hazard maps from geological surveys."
        )
        content.append(Paragraph(disclaimer_text, styles['SmallText']))
        
        # Build the PDF document
        doc.build(content)
        
        return file_path
    
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise ValueError(f"Failed to generate report: {str(e)}")
def generate_enhanced_report(earthquakes, traditional_analysis, openquake_analysis, title, center_lat, center_lon, radius_km):
    """
    Generate an enhanced PDF report for earthquake hazard analysis incorporating OpenQuake results.
    
    Args:
        earthquakes (dict): Processed earthquake data
        traditional_analysis (dict): Results of traditional hazard analysis
        openquake_analysis (dict): Results of OpenQuake hazard analysis
        title (str): Report title
        center_lat (float): Latitude of location
        center_lon (float): Longitude of location
        radius_km (float): Analysis radius in kilometers
        
    Returns:
        str: Path to generated PDF file
    """
    # Create a temporary file for the PDF
    temp_dir = tempfile.gettempdir()
    file_name = f"enhanced_earthquake_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
    
    # Add OpenQuake hazard summary
    content.append(Paragraph("Seismic Hazard Assessment", heading_style))
    
    # Extract OpenQuake data
    oq_hazard_summary = openquake_analysis.get("hazard_summary", {})
    risk_score = oq_hazard_summary.get("risk_score", 0)
    hazard_category = oq_hazard_summary.get("category", "Unknown")
    pga_10_50 = oq_hazard_summary.get("pga_10_50", 0)
    a_value = oq_hazard_summary.get("a_value", 0)
    
    # Determine hazard color
    hazard_color = {
        "Low": colors.green,
        "Moderate": colors.orange,
        "High": colors.red,
        "Unknown": colors.grey
    }.get(hazard_category, colors.grey)
    
    # Create hazard level paragraph with correct color
    hazard_style = ParagraphStyle(
        name='HazardLevel',
        parent=styles['Heading2'],
        textColor=hazard_color
    )
    
    content.append(Paragraph(f"Hazard Level: {hazard_category.upper()} (Score: {risk_score}/100)", hazard_style))
    content.append(Paragraph(oq_hazard_summary.get("description", ""), normal_style))
    content.append(Spacer(1, 0.15*inch))
    
    # Add Seismic Analysis Results
    content.append(Paragraph("Probabilistic Seismic Hazard Analysis", heading2_style))
    
    # Create a table for the PSHA results
    psha_data = [
        ["Metric", "Value", "Interpretation"],
        ["PGA (10% in 50 years)", f"{pga_10_50:.3f}g", interpret_pga(pga_10_50)],
        ["Seismicity Rate (a-value)", f"{a_value:.2f}", interpret_a_value(a_value)]
    ]
    
    psha_table = Table(psha_data, colWidths=[2*inch, 1.2*inch, 3.3*inch])
    psha_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(psha_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add explanation text for PSHA
    psha_explanation = (
        "The Probabilistic Seismic Hazard Analysis (PSHA) estimates ground motion levels that have a certain probability "
        "of being exceeded in a given time period. The PGA (10% in 50 years) value represents the Peak Ground Acceleration "
        "with a 10% probability of exceedance in 50 years, which is commonly used for building code requirements."
    )
    content.append(Paragraph(psha_explanation, normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add hazard curves from OpenQuake if available
    hazard_curves = openquake_analysis.get("hazard_curves", {})
    if "PGA()" in hazard_curves:
        content.append(Paragraph("Seismic Hazard Curves", heading2_style))
        
        # Create hazard curve chart
        hazard_chart = create_hazard_curve_chart(hazard_curves["PGA()"])
        content.append(hazard_chart)
        content.append(Spacer(1, 0.15*inch))
        
        # Add hazard curve explanation
        curve_explanation = (
            "The hazard curve shows the annual probability of exceeding different levels of Peak Ground Acceleration (PGA). "
            "This curve is fundamental to understanding the seismic risk at this location across different probability levels."
        )
        content.append(Paragraph(curve_explanation, normal_style))
        content.append(Spacer(1, 0.25*inch))
    
    # Add earthquake statistics
    content.append(Paragraph("Earthquake Statistics", heading_style))
    
    # Extract data from traditional analysis
    nearby_quakes = traditional_analysis.get("nearby_earthquakes", [])
    mag_distribution = traditional_analysis.get("magnitude_distribution", {})
    time_stats = traditional_analysis.get("time_statistics", {})
    
    quake_count = len(nearby_quakes)
    
    # Add key metrics from traditional analysis
    content.append(Paragraph("Recent Seismic Activity", heading2_style))
    
    time_data = [
        ["Time Period", "Number of Earthquakes"],
        ["Last 24 Hours", str(time_stats.get("last_24h", 0))],
        ["Last 7 Days", str(time_stats.get("last_7d", 0))],
        ["Last 30 Days", str(time_stats.get("last_30d", 0))],
        ["Total in Analysis", str(quake_count)]
    ]
    
    time_table = Table(time_data, colWidths=[2*inch, 2*inch])
    time_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(time_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add magnitude distribution
    content.append(Paragraph("Magnitude Distribution", heading2_style))
    
    mag_data = [
        ["Magnitude Range", "Number of Earthquakes"]
    ]
    
    for mag_range, count in mag_distribution.items():
        mag_data.append([mag_range, str(count)])
    
    mag_table = Table(mag_data, colWidths=[2*inch, 2*inch])
    mag_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    content.append(mag_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Create a new page for earthquake details
    content.append(PageBreak())
    
    # Add magnitude distribution chart if we have enough data
    if len(earthquakes.get("features", [])) >= 3:
        content.append(Paragraph("Earthquake Magnitude Distribution", heading_style))
        
        # Generate magnitude distribution chart
        magnitude_chart = create_magnitude_chart(earthquakes)
        content.append(magnitude_chart)
        content.append(Spacer(1, 0.25*inch))
    
    # Add nearest earthquakes list
    content.append(Paragraph("Nearest Earthquakes", heading_style))
    
    if nearby_quakes:
        quake_data = [["Magnitude", "Depth (km)", "Distance (km)", "Date", "Location"]]
        for quake in nearby_quakes[:10]:  # Limit to 10 earthquakes
            props = quake.get("properties", {})
            quake_data.append([
                str(props.get("mag", "N/A")),
                str(props.get("depth", "N/A") if "depth" in props else 
                    (quake["geometry"]["coordinates"][2] if len(quake["geometry"]["coordinates"]) > 2 else "N/A")),
                str(props.get("distance", "N/A")),
                datetime.fromtimestamp(props.get("time", 0) / 1000).strftime("%Y-%m-%d"),
                props.get("place", "Unknown")
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
    
    # Add page break before recommendations
    content.append(PageBreak())
    
    # Add risk assessment and recommendations
    content.append(Paragraph("Risk Assessment & Recommendations", heading_style))
    
    # Add risk explanation based on hazard level from OpenQuake
    risk_explanations = {
        "Low": ("Low seismic risk in this area based on probabilistic analysis. However, this does not rule out the possibility of earthquakes.", colors.green),
        "Moderate": ("Moderate seismic risk in this area. The probabilistic analysis indicates a notable level of seismic hazard that warrants attention.", colors.orange),
        "High": ("High seismic risk in this area. The probabilistic analysis indicates significant seismic hazard potential for damaging earthquakes.", colors.red),
        "Unknown": ("Unable to determine seismic risk from available data.", colors.grey)
    }
    
    risk_text, risk_color = risk_explanations.get(hazard_category, risk_explanations["Unknown"])
    
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
    
    recommendations = get_enhanced_recommendations(hazard_category, pga_10_50)
    for rec in recommendations:
        content.append(Paragraph(f"• {rec}", normal_style))
        content.append(Spacer(1, 0.1*inch))
    
    content.append(Spacer(1, 0.25*inch))
    
    # Add technical notes
    content.append(Paragraph("Technical Notes", heading2_style))
    technical_notes = (
        "This analysis combines traditional earthquake statistics with probabilistic seismic hazard analysis (PSHA) using OpenQuake. "
        f"The a-value of {a_value:.2f} represents the seismic activity rate in the Gutenberg-Richter relationship. "
        f"The PGA value of {pga_10_50:.3f}g (10% probability in 50 years) is derived from the hazard curves and "
        "can be used for preliminary building design considerations. For critical infrastructure, a more detailed site-specific "
        "analysis is recommended."
    )
    content.append(Paragraph(technical_notes, normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add disclaimer
    content.append(Paragraph("Disclaimer", heading2_style))
    disclaimer_text = (
        "This report provides a probabilistic assessment based on open-source seismic hazard analysis (OpenQuake) and "
        "recent earthquake data. While it provides valuable insights, it should not be the sole basis for critical infrastructure "
        "or life-safety decisions. For such applications, please consult with qualified seismic hazard experts and refer to "
        "official hazard maps from geological surveys. The results are based on available data and simplified models, and actual "
        "ground motions during an earthquake may vary."
    )
    content.append(Paragraph(disclaimer_text, styles['SmallText']))
    
    # Build the PDF document
    doc.build(content)
    
    return file_path

def interpret_pga(pga):
    """Interpret Peak Ground Acceleration significance"""
    if pga is None or pga == "N/A":
        return "Insufficient data"
    
    if isinstance(pga, str):
        try:
            pga = float(pga)
        except ValueError:
            return "Insufficient data"
    
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

def interpret_a_value(a_val):
    """Interpret the a-value from the Gutenberg-Richter relationship"""
    if a_val is None or a_val == "N/A":
        return "Insufficient data"
        
    if isinstance(a_val, str):
        try:
            a_val = float(a_val)
        except ValueError:
            return "Insufficient data"
    
    if a_val < 3.5:
        return "Very low seismic activity rate"
    elif a_val < 4.0:
        return "Low seismic activity rate"
    elif a_val < 5.0:
        return "Moderate seismic activity rate"
    elif a_val < 5.5:
        return "High seismic activity rate"
    else:
        return "Very high seismic activity rate"

def get_enhanced_recommendations(hazard_category, pga_10_50):
    """Get enhanced recommendations based on hazard level and PGA"""
    common_recs = [
        "Stay informed about local seismic hazards and preparedness measures.",
        "Have an emergency plan and supplies ready for all household members.",
        "Secure heavy furniture and objects that could fall during an earthquake.",
        "Know how to shut off utilities in case of emergency."
    ]
    
    # Add building recommendations based on PGA
    building_recs = []
    if pga_10_50 >= 0.4:
        building_recs = [
            "Buildings should be designed to withstand severe ground shaking (PGA > 0.4g). Consult a structural engineer for retrofitting options.",
            "Consider seismic isolation or energy dissipation systems for critical structures.",
            "Conduct a detailed seismic vulnerability assessment of existing structures."
        ]
    elif pga_10_50 >= 0.2:
        building_recs = [
            "Buildings should be designed for significant ground motion (PGA > 0.2g).",
            "Consider moderate seismic retrofitting measures for older structures.",
            "Ensure compliance with modern seismic building codes."
        ]
    elif pga_10_50 >= 0.1:
        building_recs = [
            "Buildings should incorporate basic seismic design features.",
            "Consider basic retrofitting for vulnerable structures.",
            "Ensure proper anchoring of heavy equipment and furniture."
        ]
    else:
        building_recs = [
            "Basic seismic considerations for new construction are advisable.",
            "Focus on non-structural mitigation measures like securing furniture."
        ]
    
    # Category-specific recommendations
    if hazard_category == "High":
        specific_recs = [
            "Consider professional assessment of building safety and potential retrofitting needs.",
            "Develop a detailed family emergency and communication plan.",
            "Prepare a comprehensive emergency kit for at least 72 hours of self-sufficiency.",
            "Consider earthquake insurance coverage."
        ]
    elif hazard_category == "Moderate":
        specific_recs = [
            "Review and practice earthquake safety procedures with all household members.",
            "Check home for potential hazards and consider basic retrofitting if needed.",
            "Prepare a more comprehensive emergency kit."
        ]
    else:  # Low
        specific_recs = [
            "Implement basic earthquake preparedness despite low hazard.",
            "Consider a basic emergency kit with water, food, and first aid supplies."
        ]
    
    return specific_recs + building_recs + common_recs

def create_magnitude_chart(earthquakes):
    """Create a chart showing the magnitude distribution of earthquakes"""
    # Set up the figure
    plt.figure(figsize=(7, 4))
    
    # Extract magnitudes from earthquake data
    magnitudes = []
    for feature in earthquakes.get("features", []):
        props = feature.get("properties", {})
        if "mag" in props and props["mag"] is not None:
            magnitudes.append(props["mag"])
    
    if not magnitudes:
        # If no magnitude data, return empty drawing
        d = Drawing(400, 200)
        return d
    
    # Create histogram
    plt.hist(magnitudes, bins=10, edgecolor='black', alpha=0.7)
    plt.xlabel('Magnitude')
    plt.ylabel('Number of Earthquakes')
    plt.title('Earthquake Magnitude Distribution')
    plt.grid(True, alpha=0.3)
    
    # Save the plot to a BytesIO object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    
    # Create an Image object
    img = Image(buffer)
    img.drawHeight = 3*inch
    img.drawWidth = 5*inch
    
    # Close the plot to free memory
    plt.close()
    
    return img

def create_hazard_curve_chart(hazard_data):
    """Create a chart showing the seismic hazard curve"""
    # Set up the figure
    plt.figure(figsize=(7, 4))
    
    # Extract data from hazard curve
    poes = hazard_data.get("poes", [])
    imls = hazard_data.get("imls", [])
    
    if not poes or not imls or len(poes) != len(imls):
        # If data is invalid, return empty drawing
        d = Drawing(400, 200)
        return d
    
    # Convert annual probability of exceedance (1-poe) to return periods in years
    return_periods = [1.0 / (1.0 - p) if p < 1.0 else float('inf') for p in poes]
    
    # Plot the hazard curve
    plt.plot(imls, return_periods, marker='o', linestyle='-', linewidth=2, markersize=5)
    plt.xlabel('Peak Ground Acceleration (g)')
    plt.ylabel('Return Period (years)')
    plt.title('Seismic Hazard Curve')
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    plt.xscale('log')
    
    # Add reference lines for common return periods
    common_periods = [475, 2475]  # 10% in 50 years, 2% in 50 years
    for period in common_periods:
        plt.axhline(y=period, color='red', linestyle='--', alpha=0.7)
        # Add label
        if period == 475:
            plt.text(min(imls), period, '475 years (10% in 50 years)', va='bottom')
        elif period == 2475:
            plt.text(min(imls), period, '2475 years (2% in 50 years)', va='bottom')
    
    # Save the plot to a BytesIO object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    
    # Create an Image object
    img = Image(buffer)
    img.drawHeight = 3*inch
    img.drawWidth = 5*inch
    
    # Close the plot to free memory
    plt.close()
    
    return img

if __name__ == "__main__":
    # Test function
    test_file = generate_basic_report(
        {"features": []},
        {"nearby_earthquakes": [], "magnitude_distribution": {}, "time_statistics": {}},
        "Test Earthquake Report",
        37.7749,
        -122.4194,
        100
    )
    print(f"Test report generated at {test_file}")