import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import UnivariateSpline
import io
import base64

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Data Despiking and Smoothing"

# Layout for the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Define layout for the Home Page
def home_page():
    return html.Div([
        html.H1("Online Simulation Calculator", style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
        html.P("Navigate to the Despiking to upload and process your data.", style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
        html.Button('Despiking', id='go-to-despiking', n_clicks=0, style={'display': 'block', 'margin': 'auto', 'fontFamily': 'Arial, sans-serif'}),
        dcc.Location(id='url', refresh=False)  # This component handles navigation
    ])

@app.callback(
    Output('url', 'pathname'),
    Input('go-to-despiking', 'n_clicks'),
    prevent_initial_call=True  # Ensures it only triggers on button click
)
def navigate_to_despiking(n_clicks):
    return '/despiking'


# Define layout for the Despiking Module
despiking_layout = html.Div([
    html.H2("Despiking Module", style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    dcc.Upload(
        id='upload-data',
        children=html.Button("Upload Input File"),
        multiple=False
    ),
    html.Hr(),
    html.Div(id='file-name-display', style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    dash_table.DataTable(id='data-table', page_size=10),
    html.Hr(),
    html.Button("Slpinefit and Visualise", id='smooth-button', n_clicks=0, style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    dcc.Graph(id='graph-1K', style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    dcc.Graph(id='graph-3K', style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    dcc.Graph(id='graph-6K', style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    dcc.Graph(id='graph-10K', style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
    html.Button("Download Processed File", id='download-button'),
    dcc.Download(id="download-dataframe-csv"),
    html.Div(id='error-message', style={'color': 'red'})  # Error message display
])

# Function to parse uploaded file
def parse_contents(contents):
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded), sheet_name="Rawdata", skiprows=1)
        
        # Rename columns to match expected format
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
        
        print("File successfully processed.")
        return df, "File uploaded successfully."
    except Exception as e:
        print("Error processing file:", e)
        return None, f"Error processing file: {str(e)}"

# Callback to handle page navigation
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/despiking':
        return despiking_layout
    return home_page()

# Callback to read and display file
@app.callback(
    [Output('data-table', 'data'), Output('data-table', 'columns'), Output('file-name-display', 'children'), Output('error-message', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_table(contents, filename):
    if contents is None:
        return [], [], "No file uploaded yet.", ""
    df, message = parse_contents(contents)
    if df is None:
        return [], [], "", message
    return df.to_dict('records'), [{'name': i, 'id': i} for i in df.columns], f"Uploaded File: {filename}", ""

# Function to smooth data
def smooth_data(df):
    smoothed_df = df.copy()
    for rate in ["1K", "3K", "6K", "10K"]:
        temp_col = f"{rate}_Temperature"
        cte_col = f"{rate}_CTE"
        if temp_col in df.columns and cte_col in df.columns and df[cte_col].notna().sum() > 10:
            x = df[temp_col].dropna().values
            y = df[cte_col].dropna().values
            spline = UnivariateSpline(x, y, s=1)
            smoothed_df[cte_col] = np.interp(df[temp_col], x, spline(x))
    return smoothed_df

# Callback to process data and update multiple plots
@app.callback(
    [Output('graph-1K', 'figure'), Output('graph-3K', 'figure'),
     Output('graph-6K', 'figure'), Output('graph-10K', 'figure')],
    Input('smooth-button', 'n_clicks'),
    State('data-table', 'data')
)
def update_graphs(n_clicks, data):
    if not data:
        return [go.Figure(layout_title_text="No data available.")]*4
    df = pd.DataFrame(data)
    smoothed_df = smooth_data(df)
    
    figs = []
    for rate in ["1K", "3K", "6K", "10K"]:
        temp_col = f"{rate}_Temperature"
        cte_col = f"{rate}_CTE"
        
        if temp_col in df.columns and cte_col in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df[temp_col], y=df[cte_col], mode='lines+markers', name=f"Raw {rate}", line=dict(dash='dot', color='blue')))
            fig.add_trace(go.Scatter(x=smoothed_df[temp_col], y=smoothed_df[cte_col], mode='lines', name=f"Smoothed {rate}", line=dict(color='red')))
            fig.update_layout(title=f"Comparison: Raw {rate} vs Smoothed {rate}", xaxis_title="Temperature", yaxis_title="CTE")
            figs.append(fig)
        else:
            figs.append(go.Figure(layout_title_text=f"Data missing for {rate}"))
    
    return figs

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-button", "n_clicks"),
    State('data-table', 'data'),
    prevent_initial_call=True  # Ensures it only triggers when the button is clicked
)
def download_processed_file(n_clicks, data):
    if not data:
        return None  # Prevents the download if no data is available

    df = pd.DataFrame(data)
    smoothed_df = smooth_data(df)  # Apply the smoothing function

    # Convert DataFrame to CSV
    csv_buffer = io.StringIO()
    smoothed_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    return dict(content=csv_data, filename="processed_data.csv")


# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
