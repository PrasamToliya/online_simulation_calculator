Online Simulation Calculator - Despiking Module
Overview
This repository hosts a Dash web application designed to provide a Despiking Module for processing and smoothing data related to Temperature and Coefficient of Thermal Expansion (CTE) at different heating rates. The application allows users to upload an Excel file containing raw data, process the data to remove spikes, visualize the smoothed data, and download the processed file in Excel format.

Features
File Upload: Users can upload an Excel file (xlsx) containing Temperature and CTE readings at different heating rates (1K/min, 3K/min, 6K/min, and 10K/min).

Data Processing: The application processes the uploaded data to smooth out spikes using NumPy interpolation.

Data Visualization: The processed data is visualized using interactive Plotly graphs, allowing users to compare raw and smoothed data for each heating rate.

Download Processed Data: Users can download the processed data as an Excel file with multi-level headers for better organization.

User-Friendly Interface: The application features a clean and intuitive interface with clear instructions and visual feedback.

How It Works
Upload Data: Users upload an Excel file containing Temperature and CTE data. The file should have a specific structure with columns for Temperature and CTE at different heating rates.

Data Table Display: Once the file is uploaded, the data is displayed in an interactive table for review.

Smoothing and Visualization: Users can click the "Splinefit and Visualize" button to smooth the data and generate interactive graphs comparing raw and smoothed data.

Download Processed Data: After processing, users can download the smoothed data as an Excel file with multi-level headers.

Key Components
Dash Framework: The application is built using the Dash framework, which combines Python, HTML, and JavaScript for creating interactive web applications.

Plotly Graphs: Interactive graphs are generated using Plotly, allowing users to explore the data visually.

NumPy Interpolation: The smoothing process uses NumPy's interpolation function to remove spikes from the data.

Excel File Handling: The application reads and writes Excel files using pandas and openpyxl.

Acknowledgments
Dash: For providing an excellent framework for building interactive web applications.

Plotly: For creating interactive and visually appealing graphs.

NumPy: For providing powerful numerical computation tools.

