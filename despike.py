'''
ONLINE SIMULATION CALCULATOR

This script hosts a Dash web application that provides a 'Despiking' module that works to:
1. Upload an xlsx file that contains readings of Temperature and Coefficient of Thermal Expansion (CTE) at different heating rates.
2. Process and smooth the spikes in the data.
3. Download the processed file in CSV format.
'''

# Import required libraries
import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import base64

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Data Despiking and Smoothing"

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

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

# Layout for the app (main container)
despiking_layout = html.Div([
    dcc.Store(id="upload-status", data=False),  # Track file upload status
    dcc.Store(id="visualization-status", data=False),  # Track visualization status
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
    if pathname == '/despiking':
        return despiking_layout
    return home_page()

# Callback to navigate to the despiking page
@app.callback(
    Output('url', 'pathname'),
    Input('go-to-despiking', 'n_clicks'),
    prevent_initial_call=True
)
def navigate_to_despiking(n_clicks):
    return '/despiking'  # Redirects to the Despiking module page

# Function to parse uploaded file
def parse_contents(contents, filename):
    try:
        # Decode the uploaded file
        _ , content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        buffer = io.BytesIO(decoded)

        # Read the Excel file into a DataFrame
        df = pd.read_excel(buffer, sheet_name="Rawdata", skiprows=1, engine='openpyxl')

        # Rename columns for consistency
        df.rename(columns={
            'T[°C]': '1K_Temperature',
            'CTE': '1K_CTE',
            'T[°C].1': '3K_Temperature',
            'CTE.1': '3K_CTE',
            'T[°C].2': '6K_Temperature',
            'CTE.2': '6K_CTE',
            'T[°C].3': '10K_Temperature',
            'CTE.3': '10K_CTE'
        }, inplace=True)

        return df, "File uploaded successfully."
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

# Callback to update table and show "Splinefit and Visualize" button after file upload
@app.callback(
    [Output('data-table', 'data'), Output('data-table', 'columns'),
     Output('file-name-display', 'children'), Output('error-message', 'children'),
     Output('table-container', 'style'), Output('smooth-button', 'style'),
     Output("upload-status", "data"), Output("original-column-names", "data")],  # Store column names
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_table(contents, filename):
    if contents is None:
        return [], [], "No file uploaded yet.", "", {'display': 'none'}, {'display': 'none'}, False, []

    # Read file but **DO NOT rename columns**
    try:
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        buffer = io.BytesIO(decoded)

        df = pd.read_excel(buffer, sheet_name="Rawdata", skiprows=1, engine='openpyxl')

        # Store original column names
        original_columns = df.columns.tolist()

        return df.to_dict('records'), [{'name': i, 'id': i} for i in df.columns], f"Uploaded File: {filename}", "", \
               {'display': 'block'}, {'display': 'block', 'margin': 'auto'}, True, original_columns  # Store original columns

    except Exception as e:
        return [], [], "", f"Error processing file: {str(e)}", {'display': 'none'}, {'display': 'none'}, False, []

# Function to smooth data
def smooth_data(df):
    smoothed_df = df.copy()

    # Identify column pairs for Temperature (T[°C]) and CTE
    temp_cte_pairs = [(df.columns[i], df.columns[i + 1]) for i in range(0, len(df.columns), 2)]

    for temp_col, cte_col in temp_cte_pairs:
        if df[cte_col].notna().sum() > 10:  # Apply smoothing only if enough data exists
            x = df[temp_col].dropna().values
            y = df[cte_col].dropna().values
            smoothed_df[cte_col] = np.interp(df[temp_col], x, y)  # Fast NumPy interpolation

    return smoothed_df


# Callback to process data, update plots, and show the visualization and download button
@app.callback(
    [Output('graph-1K', 'figure'), Output('graph-3K', 'figure'),
     Output('graph-6K', 'figure'), Output('graph-10K', 'figure'),
     Output('graph-container', 'style'), Output('download-container', 'style'),
     Output("visualization-status", "data")],
    Input('smooth-button', 'n_clicks'),
    State('data-table', 'data'),
    State("original-column-names", "data"),  # Retrieve stored column names
    prevent_initial_call=True
)
def update_graphs(n_clicks, data, original_columns):
    if not data or not original_columns:
        return [go.Figure(layout_title_text="No data available.")]*4, {'display': 'none'}, {'display': 'none'}, False

    df = pd.DataFrame(data)
    smoothed_df = smooth_data(df)

    # Identify column pairs dynamically
    temp_cte_pairs = [(original_columns[i], original_columns[i + 1]) for i in range(0, len(original_columns), 2)]

    figs = []
    for idx, (temp_col, cte_col) in enumerate(temp_cte_pairs):
        fig = go.Figure()

        # Plot raw data
        fig.add_trace(go.Scatter(
            x=df[temp_col], y=df[cte_col], mode='lines+markers', name=f"Raw {temp_col}"
        ))

        # Plot smoothed data
        fig.add_trace(go.Scatter(
            x=smoothed_df[temp_col], y=smoothed_df[cte_col], mode='lines', name=f"Smoothed {temp_col}"
        ))

        fig.update_layout(title=f"Comparison: Raw vs Smoothed ({temp_col})",
                          xaxis_title="Temperature", yaxis_title="CTE")
        figs.append(fig)

    return figs + [{'display': 'block'}, {'display': 'block', 'textAlign': 'center'}, True]  # Show graphs and download button

# Callback to allow users to download the processed file with original column names
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-button", "n_clicks"),
    State('data-table', 'data'),
    State("original-column-names", "data"),  # Retrieve stored column names
    prevent_initial_call=True
)
def download_processed_file(n_clicks, data, original_columns):
    if not data or not original_columns:
        return None

    df = pd.DataFrame(data)
    smoothed_df = smooth_data(df)  # Process data **without renaming columns**

    # Ensure that column names are exactly as in the original file
    smoothed_df.columns = original_columns

    # **Optimized Excel Writing**
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        smoothed_df.to_excel(writer, sheet_name="Processed Data", index=False)

    excel_buffer.seek(0)  # Move pointer to the beginning

    # **Convert to Base64 for Dash Download**
    encoded_excel = base64.b64encode(excel_buffer.getvalue()).decode()

    return dict(
        content=encoded_excel,
        filename="processed_data.xlsx",
        type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        base64=True  # Ensure proper decoding when downloaded
    )


# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
