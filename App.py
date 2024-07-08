#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import streamlit as st
import pandas as pd
from py3dbp import Packer, Bin, Item
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile

# Custom CSS to enhance the look
def add_custom_css():
    st.markdown(
        """
        <style>
        body {
            background-color: #f4f4f9;
            color: #333;
            font-family: 'Arial', sans-serif;
        }
        .main {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            border: 1px solid #e0e0e0;
            margin: 20px;
        }
        .report-container {
            margin-top: 40px;
            margin-bottom: 40px;
        }
        h1, h2, h3 {
            color: #003366;
        }
        h1 {
            font-size: 36px;
            text-align: center;
            margin-bottom: 40px;
        }
        h2 {
            font-size: 22px;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .container-info {
            font-size: 16px;
            font-weight: normal;
            color: #333;
            margin-bottom: 5px;
        }
        .plot-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            margin-bottom: 40px;
            background-color: #fff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border: 1px solid #ddd;
        }
        .plot-container h2, .plot-container .container-info {
            margin: 0;
            padding: 0;
        }
        .plot {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            margin-top: 10px;
        }
        .plot img {
            display: block;
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        .best-fit {
            font-weight: bold;
            color: #cc3300;
            margin-top: 20px;
            font-size: 20px;
            text-align: center;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #6c757d;
            font-size: 14px;
        }
        .pdf-button-container {
            text-align: center;
            margin-top: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

add_custom_css()

# Load the Excel file
file_path = 'Optimization Problem.xlsx'
packages_df = pd.read_excel(file_path, sheet_name='Packages')
cartons_df = pd.read_excel(file_path, sheet_name='Cartons')

# Function to generate a random color
def get_random_color():
    return np.random.rand(3,)

# Function to add a 3D box (representing an item) without labels
def add_box(ax, item, color):
    pos = np.array(item.position, dtype=float)
    dim = np.array(item.get_dimension(), dtype=float)

    xx, yy = np.meshgrid([pos[0], pos[0] + dim[0]], [pos[1], pos[1] + dim[1]])
    ax.plot_surface(xx, yy, np.full_like(xx, pos[2]), color=color, alpha=0.6, edgecolor='k', linewidth=0.3)
    ax.plot_surface(xx, yy, np.full_like(xx, pos[2] + dim[2]), color=color, alpha=0.6, edgecolor='k', linewidth=0.3)

    yy, zz = np.meshgrid([pos[1], pos[1] + dim[1]], [pos[2], pos[2] + dim[2]])
    ax.plot_surface(np.full_like(yy, pos[0]), yy, zz, color=color, alpha=0.6, edgecolor='k', linewidth=0.3)
    ax.plot_surface(np.full_like(yy, pos[0] + dim[0]), yy, zz, color=color, alpha=0.6, edgecolor='k', linewidth=0.3)

    xx, zz = np.meshgrid([pos[0], pos[0] + dim[0]], [pos[2], pos[2] + dim[2]])
    ax.plot_surface(xx, np.full_like(xx, pos[1]), zz, color=color, alpha=0.6, edgecolor='k', linewidth=0.3)
    ax.plot_surface(xx, np.full_like(xx, pos[1] + dim[1]), zz, color=color, alpha=0.6, edgecolor='k', linewidth=0.3)

# Streamlit app layout
st.title("Packing Optimization Report")

use_custom_dimensions = st.radio("Do you want to use custom package dimensions?", ('No', 'Yes'))

if use_custom_dimensions == "Yes":
    length = st.number_input("Enter the package length (in inches):", min_value=0.0)
    width = st.number_input("Enter the package width (in inches):", min_value=0.0)
    height = st.number_input("Enter the package height (in inches):", min_value=0.0)
else:
    package_id = st.selectbox("Select the Package ID to pack:", packages_df['Package_ID'].unique())
    selected_package = packages_df[packages_df['Package_ID'] == package_id].iloc[0]
    length = selected_package['PKG_LNGTH_IN']
    width = selected_package['PKG_WIDTH_IN']
    height = selected_package['PKG_DEPTH_IN']

if st.button("Optimize Packing"):
    item_data = {"name": "CustomPackage" if use_custom_dimensions == "Yes" else package_id, "length": length, "width": width, "height": height, "weight": 0}

    best_fit_container = None
    best_fit_volume_utilized_percentage = 0

    plot_index = 0
    plot_columns = []

    for index, carton in cartons_df.iterrows():
        if plot_index % 3 == 0:
            plot_columns = st.columns(3)  # Create a new row of three columns

        storage_unit = Bin(carton['Description'], carton['ID Length (in)'], carton['ID Width (in)'], carton['ID Height (in)'], 1)
        packer = Packer()
        packer.add_bin(storage_unit)

        batch_size = 100
        num_batches = 10

        for i in range(num_batches):
            batch_items = [Item(item_data["name"], item_data["length"], item_data["width"], item_data["height"], item_data["weight"]) for _ in range(batch_size)]
            for item in batch_items:
                packer.add_item(item)

        packer.pack()
        storage_volume = float(storage_unit.width * storage_unit.height * storage_unit.depth)
        item_volume = float(item_data["length"] * item_data["width"] * item_data["height"])
        total_items_fit = sum(len(b.items) for b in packer.bins)
        total_volume_utilized = float(total_items_fit * item_volume)
        volume_utilized_percentage = (total_volume_utilized / storage_volume) * 100

        if volume_utilized_percentage > best_fit_volume_utilized_percentage:
            best_fit_container = carton
            best_fit_volume_utilized_percentage = volume_utilized_percentage

        # Display container information above the plot
        plot_columns[plot_index % 3].markdown(f"""
        <div class='plot-container'>
            <h2>Container: {carton['Description']}</h2>
            <div class='container-info'>Package: {item_data['name']} ({item_data['length']} x {item_data['width']} x {item_data['height']})</div>
            <div class='container-info'>Total number of items fit: {total_items_fit}</div>
            <div class='container-info'>Percentage of volume utilized: {volume_utilized_percentage:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

        # Generate 3D plot
        fig = plt.figure(figsize=(6, 5))
        ax = fig.add_subplot(111, projection='3d')
        for b in packer.bins:
            for item in b.items:
                color = get_random_color()
                add_box(ax, item, color)
        ax.set_xlim([0, carton['ID Length (in)']])
        ax.set_ylim([0, carton['ID Width (in)']])
        ax.set_zlim([0, carton['ID Height (in)']])
        ax.set_box_aspect([carton['ID Length (in)'], carton['ID Width (in)'], carton['ID Height (in)']])
        ax.set_title('')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_zticklabels([])
        plt.tight_layout(pad=2.0)
        plot_columns[plot_index % 3].pyplot(fig)  # Display the plot in one of the three columns

        plot_index += 1

    # Save report as PDF
    def save_as_pdf():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            c = canvas.Canvas(tmpfile.name, pagesize=letter)
            width, height = letter
            c.drawString(30, height - 40, "Packing Optimization Report")
            y = height - 60
            for index, carton in cartons_df.iterrows():
                if y < 100:
                    c.showPage()
                    y = height - 40
                storage_unit = Bin(carton['Description'], carton['ID Length (in)'], carton['ID Width (in)'], carton['ID Height (in)'], 1)
                storage_volume = float(storage_unit.width * storage_unit.height * storage_unit.depth)
                total_items_fit = sum(len(b.items) for b in packer.bins)
                total_volume_utilized = float(total_items_fit * item_volume)
                volume_utilized_percentage = (total_volume_utilized / storage_volume) * 100
                c.drawString(30, y, f"Container: {carton['Description']}")
                y -= 20
                c.drawString(30, y, f"Package: {item_data['name']} ({item_data['length']} x {item_data['width']} x {item_data['height']})")
                y -= 20
                c.drawString(30, y, f"Total number of items fit: {total_items_fit}")
                y -= 20
                c.drawString(30, y, f"Percentage of volume utilized: {volume_utilized_percentage:.2f}%")
                y -= 40
            if best_fit_container is not None:
                c.drawString(30, y, f"The best fit container is {best_fit_container['Description']} with a volume utilization of {best_fit_volume_utilized_percentage:.2f}%")
            else:
                c.drawString(30, y, "No suitable container found.")
            c.save()
            st.success("PDF generated successfully!")
            with open(tmpfile.name, "rb") as file:
                st.download_button(
                    label="Download PDF",
                    data=file,
                    file_name="Packing_Optimization_Report.pdf",
                    mime="application/pdf",
                )

    if st.button("Save as PDF"):
        save_as_pdf()

st.markdown("<div class='footer'>&copy; 2024 Packing Optimization Report</div>", unsafe_allow_html=True)
