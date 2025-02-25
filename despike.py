import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import numpy as np
import plotly.express as px
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
        html.P("This tool allows you to process experimental data by identifying and removing spikes, as well as applying smoothing techniques to enhance data accuracy.", 
               style={'textAlign': 'center', 'maxWidth': '600px', 'margin': '0 auto', 'fontFamily': 'Arial, sans-serif'}),
        html.Img(
            src='./assets/despike_image.webp',  # Change the file name accordingly
            style={'display': 'block', 'margin': '20px auto', 'width': '50%', 'maxWidth': '400px'}
        ),
        html.Div(style={'textAlign': 'center', 'marginTop': '20px', 'fontFamily': 'Arial, sans-serif'}, children=[
            dcc.Link(html.Button('Despike', style={'padding': '10px 20px', 'fontSize': '16px', 'fontFamily': 'Arial, sans-serif'}), href='/despiking')
        ])
    ])

# Define layout for the Despiking Module
def despiking_page():
    return html.Div([
        html.H2("Despiking Module"),
        dcc.Upload(
            id='upload-data',
            children=html.Button("Upload Excel File"),
            multiple=False
        ),
        html.Hr(),
        html.Div(id='file-name-display'),
        dash_table.DataTable(id='data-table', page_size=10),
        html.Hr(),
        html.Label("Select Smoothing Factor for Each Heating Rate"),
        dcc.Slider(id='smoothing-factor-1K', min=0, max=10, step=0.1, value=1, 
                   marks={i: str(i) for i in range(11)}, 
                   tooltip={'placement': 'bottom'}),
        dcc.Slider(id='smoothing-factor-3K', min=0, max=10, step=0.1, value=1),
        dcc.Slider(id='smoothing-factor-6K', min=0, max=10, step=0.1, value=1),
        dcc.Slider(id='smoothing-factor-10K', min=0, max=10, step=0.1, value=1),
        html.Button("Apply Smoothing", id='smooth-button', n_clicks=0),
        dcc.Graph(id='graph-plot'),
        html.Button("Download Processed File", id='download-button'),
        dcc.Download(id="download-dataframe-csv")
    ])

# Function to parse uploaded file
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded), sheet_name="Rawdata", skiprows=1)
    return df

# Callback to handle page navigation
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/despiking':
        return despiking_page()
    return home_page()

# Callback to read and display file
@app.callback(
    [Output('data-table', 'data'), Output('data-table', 'columns'), Output('file-name-display', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_table(contents, filename):
    if contents is None:
        return [], [], "No file uploaded yet."
    df = parse_contents(contents)
    return df.to_dict('records'), [{'name': i, 'id': i} for i in df.columns], f"Uploaded File: {filename}"

# Function to apply smoothing
def smooth_data(df, smoothing_factors):
    heating_rates = ["1K", "3K", "6K", "10K"]
    for rate, s_factor in zip(heating_rates, smoothing_factors):
        temp_col = f"{rate}_Temperature"
        cte_col = f"{rate}_CTE"
        
        if cte_col in df.columns and df[cte_col].notna().sum() > 10:
            x = df[temp_col].dropna().values
            y = df[cte_col].dropna().values
            
            spline = UnivariateSpline(x, y, s=s_factor)
            df[cte_col] = spline(x)
    
    return df

# Callback to process data and update plot
@app.callback(
    Output('graph-plot', 'figure'),
    Input('smooth-button', 'n_clicks'),
    [State('data-table', 'data')] +
    [State(f'smoothing-factor-{rate}', 'value') for rate in ["1K", "3K", "6K", "10K"]]
)
def update_graph(n_clicks, data, s1, s3, s6, s10):
    if not data:
        return px.line(title="No data available.")
    df = pd.DataFrame(data)
    smoothed_df = smooth_data(df, [s1, s3, s6, s10])
    fig = px.line(smoothed_df, x="T[°C]", y="CTE", title="Smoothed Data")
    return fig

# Callback to download processed data
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-button", "n_clicks"),
    State('data-table', 'data'),
    prevent_initial_call=True,
)
def download_data(n_clicks, data):
    df = pd.DataFrame(data)
    return dcc.send_data_frame(df.to_excel, "processed_data.xlsx", index=False)

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
