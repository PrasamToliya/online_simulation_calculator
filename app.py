'''
ONLINE SIMULATION CALCULATOR

This script hosts a Dash web application that provides a 'Despiking' module that works to:
1. Upload an xlsx file that contains readings of Temperature and Coefficient of Thermal Expansion (CTE) at different heating rates.
2. Process and smooth the spikes in the data.
3. Download the processed file in Excel format.
'''

# Import required libraries
import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import base64
import re
from dash import ctx  # For callback context

# Global constants for column mapping and order
COLUMN_MAPPING = {
    'T[°C]': '1K/min_Temperature',
    'CTE': '1K/min_CTE',
    'T[°C].1': '3K/min_Temperature',
    'CTE.1': '3K/min_CTE',
    'T[°C].2': '6K/min_Temperature',
    'CTE.2': '6K/min_CTE',
    'T[°C].3': '10K/min_Temperature',
    'CTE.3': '10K/min_CTE'
}

ORDERED_COLUMNS = [
    "1K/min_Temperature", "1K/min_CTE",
    "3K/min_Temperature", "3K/min_CTE",
    "6K/min_Temperature", "6K/min_CTE",
    "10K/min_Temperature", "10K/min_CTE"
]

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Data Despiking and Smoothing"

#Define the main layout of the Dash app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

#Deifine the layout of the homepage
def home_page():
    return html.Div([
        html.H1("Online Simulation Calculator", style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
        
        # Add an image for better UI
        html.Div(style={'textAlign': 'center', 'marginBottom': '20px'}, children=[
            html.Img(src="./assets/despike_image.webp/", 
                     style={'width': '600px', 'height': '400px', 'borderRadius': '10px'})
        ]),
        html.P("Welcome to the Online Simulation Calculator. Navigate to the Despiking Module to upload and process your data.",
               style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif', 'fontSize': '18px'}),
        # Navigation Button
        html.Div(style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '30px'}, children=[
            html.Button("Go to Despiking Module", id="go-to-despiking", n_clicks=0)
        ])
    ])

# Layout for the Despiking Module page
despiking_layout = html.Div([
    dcc.Store(id="upload-status", data=False),          # Track file upload status
    dcc.Store(id="visualization-status", data=False),     # Track visualization status
    dcc.Store(id="original-column-names", data=[]),
    html.H2("Despiking Module", style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    # Upload file component 
    html.Div(style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '15px'}, children=[
        dcc.Upload(
            id='upload-data',
            children=html.Button("Upload Input File"),
            multiple=False
        )
    ]),
    html.Div(id='file-name-display', style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    # Data Table
    html.Div(id='table-container', style={'display': 'none'}, children=[
        html.Hr(),
        dash_table.DataTable(id='data-table', page_size=10),
        html.Hr(),
        html.Div(style={'display': 'flex', 'justifyContent': 'center', 'marginTop': '50px'}, children=[
            html.Button("Splinefit and Visualize", id='smooth-button', n_clicks=0, style={'display': 'none'})
        ])
    ]),
    # Visualization Graphs
    html.Div(id='graph-container', style={'display': 'none'}, children=[
        dcc.Graph(id='graph-1K'),
        dcc.Graph(id='graph-3K'),
        dcc.Graph(id='graph-6K'),
        dcc.Graph(id='graph-10K'),
    ]),
    # Download Button
    html.Div(id='download-container', style={'display': 'none', 'textAlign': 'center'}, children=[
        html.Button("Download Processed File", id='download-button', style={'margin': 'auto', 'marginBottom': '30px'}),
        dcc.Download(id="download-dataframe-csv"),
    ]),
    # Error message display
    html.Div(id='error-message', style={'color': 'red', 'textAlign': 'center'})
])

# Callback to handle page navigation
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    return despiking_layout if pathname == '/despiking' else home_page()

# Callback to navigate to the Despiking Module page
@app.callback(
    Output('url', 'pathname'),
    Input('go-to-despiking', 'n_clicks'),
    prevent_initial_call=True
)
def navigate_to_despiking(n_clicks):
    return '/despiking'

# Helper function to load and rename the uploaded file
def load_and_rename(contents):
    try:
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        buffer = io.BytesIO(decoded)
        df = pd.read_excel(buffer, sheet_name="Rawdata", skiprows=1, engine='openpyxl')
        df.rename(columns=COLUMN_MAPPING, inplace=True)
        return df, "File uploaded successfully."
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

# Function to smooth data using NumPy interpolation
def smooth_data(df):
    smoothed_df = df.copy()
    # Process each paired column (Temperature and CTE)
    temp_cte_pairs = [(df.columns[i], df.columns[i+1]) for i in range(0, len(df.columns), 2)]
    for temp_col, cte_col in temp_cte_pairs:
        if df[cte_col].notna().sum() > 10:
            x = df[temp_col].dropna().values
            y = df[cte_col].dropna().values
            smoothed_df[cte_col] = np.interp(df[temp_col], x, y)
    return smoothed_df

# Callback to update table, file info, and graphs
@app.callback(
    [Output('data-table', 'data'),
     Output('data-table', 'columns'),
     Output('file-name-display', 'children'),
     Output('error-message', 'children'),
     Output('table-container', 'style'),
     Output('smooth-button', 'style'),
     Output("upload-status", "data"),
     Output("original-column-names", "data"),
     Output('graph-container', 'style'),
     Output('download-container', 'style'),
     Output("visualization-status", "data"),
     Output('graph-1K', 'figure'),
     Output('graph-3K', 'figure'),
     Output('graph-6K', 'figure'),
     Output('graph-10K', 'figure')],
    [Input('upload-data', 'contents'),
     Input('smooth-button', 'n_clicks')],
    [State('upload-data', 'filename'),
     State('data-table', 'data'),
     State("original-column-names", "data")]
)
def update_table_and_graphs(contents, n_clicks, filename, existing_data, original_columns):
    trigger_id = ctx.triggered_id

    # Upload branch: load file and rename columns
    if trigger_id == 'upload-data':
        if contents is None:
            return ([], [], "No file uploaded yet.", "", {'display': 'none'},
                    {'display': 'none'}, False, [], {'display': 'none'},
                    {'display': 'none'}, False, go.Figure(), go.Figure(), go.Figure(), go.Figure())
        df, msg = load_and_rename(contents)
        if df is None:
            return ([], [], "", msg, {'display': 'none'},
                    {'display': 'none'}, False, [], {'display': 'none'},
                    {'display': 'none'}, False, go.Figure(), go.Figure(), go.Figure(), go.Figure())
        original_columns = df.columns.tolist()
        return (df.to_dict('records'),
                [{'name': col, 'id': col} for col in df.columns],
                f"Uploaded File: {filename}",
                "",
                {'display': 'block'},
                {'display': 'block', 'margin': 'auto'},
                True,
                original_columns,
                {'display': 'none'},
                {'display': 'none'},
                False,
                go.Figure(), go.Figure(), go.Figure(), go.Figure())

    # Smoothing branch: apply smoothing and update graphs
    elif trigger_id == 'smooth-button' and existing_data and original_columns:
        df = pd.DataFrame(existing_data)
        smoothed_df = smooth_data(df)
        # Create graphs for each column pair
        temp_cte_pairs = [(original_columns[i], original_columns[i+1]) for i in range(0, len(original_columns), 2)]
        figs = []
        for temp_col, cte_col in temp_cte_pairs:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df[temp_col], y=df[cte_col],
                                     mode='lines+markers',
                                     name=f"Raw Data ({temp_col})"))
            fig.add_trace(go.Scatter(x=smoothed_df[temp_col], y=smoothed_df[cte_col],
                                     mode='lines',
                                     name=f"Smoothed Data ({temp_col})"))
            match = re.search(r'(\d+)K', temp_col)
            heating_rate = match.group(1) + "K/min" if match else temp_col
            fig.update_layout(title=f"Despiking Analysis at {heating_rate} Heating Rate",
                              xaxis_title="Temperature (°C)",
                              yaxis_title="Coefficient of Thermal Expansion (CTE)")
            figs.append(fig)
        return (existing_data,
                [{'name': col, 'id': col} for col in df.columns],
                filename,
                "",
                {'display': 'block'},
                {'display': 'block', 'margin': 'auto'},
                True,
                original_columns,
                {'display': 'block'},
                {'display': 'block', 'textAlign': 'center'},
                True,
                figs[0], figs[1], figs[2], figs[3])
    return dash.no_update

# Callback to download the processed file
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-button", "n_clicks"),
    State('data-table', 'data'),
    State("original-column-names", "data"),
    prevent_initial_call=True
)
def download_processed_file(n_clicks, data, original_columns):
    if not data or not original_columns:
        return None
    df = pd.DataFrame(data)
    smoothed_df = smooth_data(df)
    # Reorder columns according to the desired order
    smoothed_df = smoothed_df[ORDERED_COLUMNS]

    # Define multi-level headers for the Excel file
    column_names = [
        ["1K/min", "1K/min", "3K/min", "3K/min", "6K/min", "6K/min", "10K/min", "10K/min"],
        ["Temperature", "CTE", "Temperature", "CTE", "Temperature", "CTE", "Temperature", "CTE"]
    ]

    # Write the DataFrame to an Excel file with multi-level headers
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        smoothed_df.to_excel(writer, sheet_name="Processed Data", index=False, header=False)
        worksheet = writer.sheets["Processed Data"]
        for col_num, (header1, header2) in enumerate(zip(column_names[0], column_names[1]), 1):
            worksheet.cell(row=1, column=col_num).value = header1
            worksheet.cell(row=2, column=col_num).value = header2
    excel_buffer.seek(0)
    encoded_excel = base64.b64encode(excel_buffer.getvalue()).decode()
    return dict(
        content=encoded_excel,
        filename="processed_data.xlsx",
        type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        base64=True
    )

server = app.server

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
