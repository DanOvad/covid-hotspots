
# Import libraries
import pandas as pd
import numpy as np
import requests

import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
#import geoplot as gplt
from plotly.subplots import make_subplots

from urllib.request import urlopen
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import time
import datetime

# Custom libraries
import data_processing
import plotting
################################################################################
# IMPORT DATA

################################################################################
# Get the Map of US counties
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    COUNTY_GEOJSON = json.load(response)

################################################################################
# IMPORTING
    # Corona County Data
COVID_COUNTIES = data_processing.get_covid_county_data()

################################################################################
# Import the unemployment data because it has the fips codes
#df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
                  # dtype={"fips": str})
#df['prefix'] = [x[:2] for x in df['fips']]

################################################################################
# Coronavirus data by state from covidtracking API
states_url = "https://covidtracking.com/api/states/daily"
# Create requests object
r = requests.get(states_url)

# Create df of states
states_df = pd.DataFrame(r.json())

# Cleaning
# Set date as dateTime format
states_df['date'] = pd.to_datetime(states_df.date, format="%Y%m%d")

#Extract values for date, state, and death
states_df = states_df[['date', 'state', 'death', 'total']].sort_values('date')

deaths = states_df.reset_index()
################################################################################
# Read in states data
states = pd.read_csv('./data/tbl_states.csv')

# Fix fips code to be a string, prefix 0 to single digit codes
states['fips'] = states['fips'].astype(str).apply(lambda x: '0' + x if len(x) == 1 else x)
################################################################################
# DATA CLEANING

date = time.strftime('%Y-%m-%d')
state = 'New York'
state_mask = (COVID_COUNTIES['state'] == state)
date_mask = (COVID_COUNTIES['date'] == date)
min_date = int(time.mktime(COVID_COUNTIES['date'].min().timetuple()))

date_dict = data_processing.generate_slider_dates(COVID_COUNTIES)

################################################################################

# Create Dash object
app = dash.Dash(external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'])

colors = {
    'background': '#c8a2c8',# '#6495ED',  #FF69B4 == pink , #c8a2c8 = lilac
    'text': '#000000'#'#7FDBFF'
}
app.layout = html.Div(
    style={'backgroundColor': colors['background']},
    children=[
        # Title
        html.Div(id='header',
            children=[
                html.H1(children='COVID-19 Hotspot Tracker',
                    style={
                        'textAlign': 'center',
                        'color': colors['text']
                    }
                ), # Title H1
                # Text
                html.Div(children='A dashboard to track the spread of coronavirus in the United States.',
                         style={
                            'textAlign': 'center',
                            'color': colors['text']
                         }
                ), #Text div
        
        ]), # close header div
        html.Div(id='my-hover'),
        # open div for county graphs
        html.Div(id='county-section',className="row",
            children=[
            html.Div(className='six columns',
                children=[ # county choropleth div
                    dcc.Graph( # county choropleth graph
                        id='choropleth',
                        figure=plotting.choropleth_deaths_county(COVID_COUNTIES,
                                                COUNTY_GEOJSON,'deaths',
                                                date = COVID_COUNTIES['date'].max())
                    ),
                    html.Div(id='div-slider',
                        children=[
                            dcc.Slider(
                                id='crossfilter_date_slider',
                                min=min(date_dict),
                                max=max(date_dict),
                                value=max(date_dict),
                                marks=date_dict,
                                step=None
                            ) # slider dcc])
                        ]
                    ) # slider div
                ] 
            ), # choropleth div
            # Item 2 - Include County Deaths Scatter
            html.Div(className='six columns',children=[
                dcc.Dropdown(
                    id='dropdown-category-filter',
                    #className='row',
                    value='deaths',
                    options=[
                        {'label':'deaths','value':'deaths'},
                        {'label':'cases','value':'cases'}
                    ]
                ),
                dcc.Graph(
                    id='scatter',
                    figure = plotting.scatter_deaths_county(COVID_COUNTIES,
                                                            'deaths',
                                                            '01001')
                )
            ]), # close div tag
            ])
    ])

server = app.server
################################################################################
# Text OUTPUT from HOVER
@app.callback(
    Output(component_id='my-hover', component_property='children'),
    [Input(component_id='crossfilter_date_slider', component_property='value')]
)
def update_output_div(date):
    date = time.strftime('%Y-%m-%d',time.localtime(date))
    return 'You\'ve entered "{}"'.format(date)


# SCATTER PLOT from HOVER
@app.callback(
    Output(component_id='scatter', component_property='figure'),
    [Input(component_id='choropleth', component_property='hoverData')],
    [State(component_id='dropdown-category-filter',component_property='value')]
)
def update_scatter_counter(fips_input,category):
    # Create a series of cases by date
    try:
        fips = fips_input['points'][0]['location']
    except:
        fips = '01001'
    scatter = plotting.scatter_deaths_county(COVID_COUNTIES,category,fips)
    return scatter


#@app.callback(
#    Output(component_id='choropleth', component_property='figure'),
#    [Input(component_id='crossfilter_date_slider', component_property='value')],
#    [State(component_id='dropdown-category-filter',component_property='value')]
#)
#def update_county_choropleth(date, category):
#    date = time.strftime('%Y-%m-%d',time.localtime(date))
#    return plotting.choropleth_deaths_county(COVID_COUNTIES,
#                                             COUNTY_GEOJSON,
#                                             category,
#                                             date)

@app.callback(
    Output('choropleth','figure'),
    [Input('dropdown-category-filter','value')],
    [State('crossfilter_date_slider','value')]
)

def update_county_choropleth_category(category, date):
    date = time.strftime('%Y-%m-%d',time.localtime(date))
    return plotting.choropleth_deaths_county(COVID_COUNTIES,
                                             COUNTY_GEOJSON,
                                             category,
                                             date)



if __name__ == '__main__':
    app.run_server(debug=True, use_reloader = True)
