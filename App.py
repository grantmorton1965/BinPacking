#!/usr/bin/env python
# coding: utf-8

# In[ ]:
import streamlit as st
import pandas as pd
from py3dbp import Packer, Bin, Item
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from collections import defaultdict
from io import BytesIO
import base64

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
    ax.plot_surface(xx, yy, np.full_like(xx, pos[2]), color=color, alpha=0.5, edgecolor='k', linewidth=0.5)
    ax.plot_surface(xx, yy, np.full_like(xx, pos[2] + dim[2]), color=color, alpha=0.5, edgecolor='k', linewidth=0.5)

    yy, zz = np.meshgrid([pos[1], pos[1] + dim[1]], [pos[2], pos[2] + dim[2]])
    ax.plot_surface(np.full_like(yy, pos[0]), yy, zz, color=color, alpha=0.5, edgecolor='k', linewidth=0.5)
    ax.plot_surface(np.full_like(yy, pos[0] + dim[0]), yy, zz, color=color, alpha=0.5, edgecolor='k', linewidth=0.5)

    xx, zz = np.meshgrid([pos[0], pos[0] + dim[0]], [pos[2], pos[2] + dim[2]])
    ax.plot_surface(xx, np.full_like(xx, pos[1]), zz, color=color, alpha=0.5, edgecolor='k', linewidth=0.5)
    ax.plot_surface(xx, np.full_like(xx, pos[1] + dim[1]), zz, color=color, alpha=0.5, edgecolor='k', linewidth=0.5)

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

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f5f5f5;
                color: #333333;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #ffffff;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
            h1 {
                color: #004080;
                text-align: center;
                font-size: 24px;
                margin-bottom: 20px;
            }
            h2 {
                color: #0056b3;
                border-bottom: 2px solid #0056b3;
                padding-bottom: 10px;
                font-size: 20px;
                margin-top: 40px;
            }
            .container-info {
                font-weight: bold;
                color: #006600;
                margin-top: 10px;
                font-size: 16px;
            }
            .instructions {
                margin-top: 20px;
            }
            .instructions h3 {
                color: #e69500;
                font-size: 18px;
            }
            .instructions ul {
                list-style-type: none;
                padding-left: 0;
            }
            .instructions ul li {
                background: #f8f9fa;
                padding: 10px;
                margin-bottom: 5px;
                border-radius: 5px;
            }
            .plot img {
                display: block;
                max-width: 100%;
                height: auto;
                margin: 20px 0;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            .best-fit {
                font-weight: bold;
                color: #cc3300;
                margin-top: 20px;
                font-size: 16px;
            }
            .footer {
                text-align: center;
                margin-top: 20px;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Packing Optimization Report</h1>
    """

    for index, carton in cartons_df.iterrows():
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

        instructions = defaultdict(int)
        for b in packer.bins:
            for item in b.items:
                pos = tuple(item.position)
                dim = tuple(item.get_dimension())
                key = (pos, dim)
                instructions[key] += 1

        container_html = f"""
            <h2>Container: {carton['Description']} ({carton['ID Length (in)']} x {carton['ID Width (in)']} x {carton['ID Height (in)']})</h2>
            <div class="container-info">Package: {item_data['name']} ({item_data['length']} x {item_data['width']} x {item_data['height']})</div>
            <div class="container-info">Total number of items fit: {total_items_fit}</div>
            <div class="container-info">Percentage of volume utilized: {volume_utilized_percentage:.2f}%</div>
            <div class="instructions">
                <h3>Packing Instructions:</h3>
                <ul>
        """
        for (pos, dim), count in instructions.items():
            container_html += f"<li>{count} items at position (x, y, z): ({pos[0]}, {pos[1]}, {pos[2]}) with dimensions (L x W x H): ({dim[0]} x {dim[1]} x {dim[2]})</li>"

        container_html += """
                </ul>
            </div>
        """

        html_content += container_html

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
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.set_zlabel('Z axis')
        ax.set_title(f'3D Visualization of Items (SKU: {item_data["name"]}) in {carton["Description"]} ({carton["ID Length (in)"]} x {carton["ID Width (in)"]} x {carton["ID Height (in)"]})')
        plt.tight_layout(pad=2.0)
        img_bytes = BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight')
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
        html_content += f'<div class="plot"><img src="data:image/png;base64,{img_base64}" alt="3D Visualization"></div>'
        plt.close()

    if best_fit_container is not None:
        html_content += f'<div class="best-fit">The best fit container is {best_fit_container["Description"]} with a volume utilization of {best_fit_volume_utilized_percentage:.2f}%</div>'
    else:
        html_content += '<div class="best-fit">No suitable container found.</div>'

    html_content += """
        </div>
        <div class="footer">
            &copy; 2024 Packing Optimization Report
        </div>
    </body>
    </html>
    """

    st.markdown(html_content, unsafe_allow_html=True)

