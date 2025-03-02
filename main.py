import streamlit as st
from fpdf import FPDF
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import tempfile
import os

# Set matplotlib params for better font rendering
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']


# Function to calculate body composition metrics
def calculate_metrics(weight, height, age, gender):
    # BMI
    bmi = np.round(weight / ((height / 100) ** 2), 1)

    # Body Fat Percentage (Adjusted Deurenberg formula)
    if gender == "Male":
        body_fat_rate = np.round(1.39 * bmi + 0.16 * age - 10.34 - 3.9, 1)
    else:  # Female
        body_fat_rate = np.round(1.39 * bmi + 0.16 * age - 9.34, 1)

    body_fat_rate = np.round(max(5, min(50, body_fat_rate - 0.2)), 1)

    # Lean Body Weight
    lean_body_weight = np.round(weight - (weight * body_fat_rate / 100), 1)

    # Muscle Mass
    muscle_mass = np.round(weight * (1 - body_fat_rate / 100) * 0.95, 1)

    # Visceral Fat Level
    visceral_fat_level = np.round(0.6 * bmi + 0.2 * age - 10.7, 1)
    visceral_fat_level = max(1, min(visceral_fat_level, 15))

    # Body Water Rate
    body_water_rate = np.round(50 + 0.15 * bmi, 1)

    # Bone Mass
    bone_mass = np.round(weight * 0.038, 1)

    # Basal Metabolic Rate (BMR)
    bmr = np.round(370 + (21.6 * lean_body_weight), 1)

    # Protein Level
    protein_level = np.round(15 + 0.08 * bmi, 1)

    # Metabolic Age
    average_bmr_for_age = 1600 if gender == "Male" else 1400
    metabolic_age = np.round(age + (bmr - average_bmr_for_age) / 80, 1)
    metabolic_age = max(18, metabolic_age)  # Ensure metabolic age is realistic

    return {
        "BMI": bmi,
        "Body Fat Rate": body_fat_rate,
        "Muscle Mass (kg)": muscle_mass,
        "Lean Body Weight (kg)": lean_body_weight,
        "Visceral Fat Level": visceral_fat_level,
        "Body Water Rate (%)": body_water_rate,
        "Bone Mass (kg)": bone_mass,
        "BMR (kcal)": bmr,
        "Protein Level (%)": protein_level,
        "Metabolic Age": metabolic_age,
        "Weight": weight  # Add weight to the metrics dictionary
    }


# Function to create a modern pie chart
def create_pie_chart(metrics):
    labels = ['Fat', 'Muscle', 'Water', 'Bone']
    sizes = [
        metrics['Body Fat Rate'],
        metrics['Muscle Mass (kg)'] / metrics['Weight'] * 100,
        metrics['Body Water Rate (%)'],
        metrics['Bone Mass (kg)'] / metrics['Weight'] * 100
    ]

    # Modern color palette
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFBE0B']
    explode = (0.05, 0.05, 0.05, 0.05)  # Explode all slices slightly

    plt.figure(figsize=(7, 5))
    plt.style.use('ggplot')  # Using a modern style

    # Create pie chart with shadow and exploded slices
    wedges, texts, autotexts = plt.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        explode=explode,
        shadow=True,
        textprops={'fontsize': 11, 'fontweight': 'bold'}
    )

    # Style the percentage labels
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')

    # Equal aspect ratio ensures that pie is drawn as a circle
    plt.axis('equal')
    plt.tight_layout()

    # Save with transparent background for better PDF embedding
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_file.name, format='png', dpi=200, transparent=True)
    plt.close()
    return temp_file.name


# Function to create a modern bar chart
def create_bar_chart(metrics):
    labels = ['BMI', 'Body Fat %', 'Visceral Fat']
    values = [metrics['BMI'], metrics['Body Fat Rate'], metrics['Visceral Fat Level']]

    # Modern color palette with gradient
    colors = ['#2E8B57', '#3CB371', '#66CDAA']

    plt.figure(figsize=(7, 5))
    plt.style.use('ggplot')  # Using a modern style

    # Create bar chart with rounded corners
    bars = plt.bar(
        labels,
        values,
        color=colors,
        width=0.6,
        edgecolor='white',
        linewidth=1
    )

    # Add data labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.,
            height + 0.3,
            f'{height:.1f}',
            ha='center',
            fontweight='bold',
            fontsize=10
        )

    # Style improvements
    plt.title('Key Health Metrics', fontsize=14, fontweight='bold', pad=15)
    plt.ylabel('Value', fontsize=12)
    plt.ylim(0, max(values) * 1.2)  # Add some headroom for labels
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    # Save with transparent background for better PDF embedding
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_file.name, format='png', dpi=200, transparent=True)
    plt.close()
    return temp_file.name


# Function to generate dynamic insights based on metrics
def generate_insights(metrics, age):
    insights = []

    # BMI Insights
    if metrics["BMI"] < 18.5:
        insights.append(
            "- Your BMI indicates underweight [Warning]. Consider gaining healthy weight through balanced nutrition.")
    elif 18.5 <= metrics["BMI"] < 24.9:
        insights.append("- Your BMI is within the healthy range [Good!]. Maintain your current lifestyle.")
    elif 25 <= metrics["BMI"] < 29.9:
        insights.append(
            "- Your BMI suggests being slightly overweight [Caution]. Focus on weight management through diet and exercise.")
    else:
        insights.append("- Your BMI indicates obesity [High Risk]. Prioritize weight loss through diet and exercise.")

    # Body Fat Rate Insights
    if metrics["Body Fat Rate"] < 10:
        insights.append(
            "- Your Body Fat Rate is very low [Warning]. Ensure adequate nutrition to maintain healthy fat levels.")
    elif 10 <= metrics["Body Fat Rate"] < 20:
        insights.append("- Your Body Fat Rate is optimal [Great!]. Keep up the good work.")
    elif 20 <= metrics["Body Fat Rate"] < 30:
        insights.append("- Your Body Fat Rate is moderate [OK]. Monitor it to prevent excessive fat gain.")
    else:
        insights.append(
            "- Your Body Fat Rate is high [High Risk]. Focus on fat loss while preserving lean muscle mass.")

    # Visceral Fat Level Insights
    if metrics["Visceral Fat Level"] < 5:
        insights.append("- Your Visceral Fat Level is low [Great!]. Continue maintaining a healthy lifestyle.")
    elif 5 <= metrics["Visceral Fat Level"] < 10:
        insights.append(
            "- Your Visceral Fat Level is moderate [Caution]. Aim to reduce it through diet and cardio exercises.")
    else:
        insights.append(
            "- Your Visceral Fat Level is high [High Risk]. Take immediate action to reduce it through diet and exercise.")

    # Metabolic Age Insights
    if metrics["Metabolic Age"] < age:
        insights.append(
            f"- Your Metabolic Age ({metrics['Metabolic Age']}) is younger than your actual age ({age}) [Great!]. Keep up the good work!")
    elif metrics["Metabolic Age"] == age:
        insights.append(
            f"- Your Metabolic Age ({metrics['Metabolic Age']}) matches your actual age ({age}) [OK]. Maintain your current habits.")
    else:
        insights.append(
            f"- Your Metabolic Age ({metrics['Metabolic Age']}) is older than your actual age ({age}) [Caution]. Focus on improving your metabolism through exercise and diet.")

    # General Recommendations
    insights.append("- Focus on maintaining a balance between lean muscle gain and fat loss.")
    insights.append("- Incorporate strength training exercises to further improve muscle mass.")
    insights.append("- Monitor visceral fat levels to ensure they remain in the healthy range.")

    return insights


# Function to generate PDF report with improved design
def generate_pdf_report(name, weight, height, metrics, insights):
    pdf = FPDF()
    pdf.add_page()

    # Set Font and Colors
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("Arial", "", "arial.ttf", uni=True)
    pdf.add_font("Arial", "B", "arialbd.ttf", uni=True)

    # Header with gradient effect
    pdf.set_fill_color(46, 139, 87)  # Green background
    pdf.rect(0, 0, 210, 40, style="F")
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font("Arial", style="B", size=24)
    pdf.cell(0, 20, txt="BODY COMPOSITION SUMMARY", ln=True, align="C")
    pdf.set_font("Arial", style="", size=12)
    pdf.cell(0, 10, txt=f"Generated for: {name}", ln=True, align="C")
    pdf.ln(10)

    # User Profile Section with colored box
    pdf.set_fill_color(240, 248, 255)  # Light blue background
    pdf.rect(10, 50, 190, 30, style="F")
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.set_font("Arial", style="B", size=14)
    pdf.set_xy(15, 55)
    pdf.cell(0, 10, txt="USER PROFILE", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.set_x(15)
    pdf.cell(95, 10, txt=f"Weight: {weight} kg", ln=0)
    pdf.cell(95, 10, txt=f"Height: {height} cm", ln=1)
    pdf.ln(10)

    # Metrics Section with styled table
    pdf.set_font("Arial", style="B", size=16)
    pdf.set_fill_color(46, 139, 87)  # Green header
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.cell(0, 12, txt="KEY BODY METRICS", ln=True, align="C", fill=True)

    # Table header
    pdf.set_font("Arial", style="B", size=12)
    pdf.set_fill_color(220, 220, 220)  # Light gray for alternating rows
    pdf.set_text_color(0, 0, 0)  # Black text

    # Table data with alternating row colors
    data = [
        ["BMI", f"{metrics['BMI']}"],
        ["Body Fat Rate", f"{metrics['Body Fat Rate']}%"],
        ["Muscle Mass", f"{metrics['Muscle Mass (kg)']} kg"],
        ["Lean Body Weight", f"{metrics['Lean Body Weight (kg)']} kg"],
        ["Visceral Fat Level", f"{metrics['Visceral Fat Level']}"],
        ["Body Water Rate", f"{metrics['Body Water Rate (%)']}%"],
        ["Bone Mass", f"{metrics['Bone Mass (kg)']} kg"],
        ["Basal Metabolic Rate (BMR)", f"{metrics['BMR (kcal)']} kcal"],
        ["Protein Level", f"{metrics['Protein Level (%)']}%"],
        ["Metabolic Age", f"{metrics['Metabolic Age']} years"]
    ]

    col_width = [120, 70]
    row_height = 10
    for i, row in enumerate(data):
        # Alternating row colors
        if i % 2 == 0:
            pdf.set_fill_color(245, 245, 245)  # Very light gray
        else:
            pdf.set_fill_color(255, 255, 255)  # White

        pdf.set_font("Arial", style="B", size=11)
        pdf.cell(col_width[0], row_height, txt=row[0], border="LTB", fill=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(col_width[1], row_height, txt=row[1], border="RTB", ln=True, fill=True)
    pdf.ln(10)

    # Visual Section Header
    pdf.set_fill_color(46, 139, 87)  # Green header
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 12, txt="VISUAL BREAKDOWN", ln=True, align="C", fill=True)
    pdf.ln(5)

    # Two charts side by side
    pie_chart_path = create_pie_chart(metrics)
    bar_chart_path = create_bar_chart(metrics)

    # Chart titles
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(95, 10, txt="Body Composition", ln=0, align="C")
    pdf.cell(95, 10, txt="Key Metrics", ln=1, align="C")

    # Add charts
    pdf.image(pie_chart_path, x=10, y=pdf.get_y(), w=90)
    pdf.image(bar_chart_path, x=110, y=pdf.get_y(), w=90)
    os.unlink(pie_chart_path)
    os.unlink(bar_chart_path)
    pdf.ln(100)  # Space for the charts

    # Insights Section with styled box
    pdf.set_fill_color(46, 139, 87)  # Green header
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 12, txt="PERSONALIZED INSIGHTS", ln=True, align="C", fill=True)
    pdf.ln(5)

    # Style for insights
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.set_font("Arial", size=11)
    pdf.set_fill_color(240, 248, 255)  # Light blue background
    pdf.rect(10, pdf.get_y(), 190, 8 * len(insights), style="F")

    pdf.set_xy(15, pdf.get_y() + 5)
    for insight in insights:
        pdf.multi_cell(180, 8, txt=insight)
    pdf.ln(10)

    # Custom footer with gradient
    pdf.set_y(-35)
    pdf.set_fill_color(46, 139, 87)  # Green background
    pdf.rect(0, pdf.get_y(), 210, 35, style="F")
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(0, 10, txt="Thank you for using the Body Composition Analyzer!", ln=True, align="C")
    pdf.set_font("Arial", size=9)
    pdf.cell(0, 7, txt=f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.cell(0, 7, txt="For more information, contact support@bodycomposition.com", ln=True, align="C")

    # Save PDF
    pdf.output(f"{name}_body_composition_summary.pdf")


# Streamlit App
st.title("Body Composition Analyzer")

# User Inputs
name = st.text_input("Enter your name:")
weight = st.number_input("Enter your weight (kg):", min_value=30.0, max_value=200.0, step=0.1)
height = st.number_input("Enter your height (cm):", min_value=100.0, max_value=250.0, step=0.1)
age = st.number_input("Enter your age:", min_value=18, max_value=100, step=1)
gender = st.selectbox("Select your gender:", ["Male", "Female"])

# Generate Report Button
if st.button("Generate Report"):
    if not name or weight <= 0 or height <= 0:
        st.error("Please fill in all fields correctly.")
    else:
        # Calculate metrics
        metrics = calculate_metrics(weight, height, age, gender)

        # Generate insights
        insights = generate_insights(metrics, age)

        # Generate PDF report
        generate_pdf_report(name, weight, height, metrics, insights)

        # Display success message and download link
        st.success("Report generated successfully!")
        with open(f"{name}_body_composition_summary.pdf", "rb") as file:
            st.download_button(
                label="Download Report",
                data=file,
                file_name=f"{name}_body_composition_summary.pdf",
                mime="application/pdf"
            )