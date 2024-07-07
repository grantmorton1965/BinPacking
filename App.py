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

st.title("Packing Optimization")

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

    if best_fit_container is not None:
        st.write(f'The best fit container is {best_fit_container["Description"]} with a volume utilization of {best_fit_volume_utilized_percentage:.2f}%')
    else:
        st.write('No suitable container found.')

    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(111, projection='3d')
    for b in packer.bins:
        for item in b.items:
            color = get_random_color()
            add_box(ax, item, color)
    ax.set_xlim([0, best_fit_container['ID Length (in)']])
    ax.set_ylim([0, best_fit_container['ID Width (in)']])
    ax.set_zlim([0, best_fit_container['ID Height (in)']])
    ax.set_box_aspect([best_fit_container['ID Length (in)'], best_fit_container['ID Width (in)'], best_fit_container['ID Height (in)']])
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    ax.set_title(f'3D Visualization of Items in {best_fit_container["Description"]}')
    plt.tight_layout(pad=2.0)
    st.pyplot(fig)

