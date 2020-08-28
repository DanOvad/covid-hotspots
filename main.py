
# Import libraries
import pandas as pd
import numpy as np
import requests

import geopandas as gpd
#import matplotlib.pyplot as plt
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

# Get county geojson for county polygones
COUNTY_GEOJSON = data_processing.load_county_geojson()
# Get county coronavirus data
COVID_COUNTIES_DF = data_processing.get_covid_county_data()
# Get state coronavirus data
COVID_STATES_DF = data_processing.get_covid_state_data()

date_dict = data_processing.generate_slider_dates(COVID_COUNTIES_DF)

################################################################################

# Create Dash object
app = dash.Dash(
        external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'],
        meta_tags=[
            {"name": "viewport",
             "content": "width=device-width, initial-scale=1"}
        ]
    )

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
                            id='county-choropleth',
                            figure=plotting.choropleth_deaths_county(
                                COVID_COUNTIES_DF,
                                COUNTY_GEOJSON,
                                'deaths',
                                date = time.strftime('%Y-%m-%d',time.localtime(max(date_dict)))
                            )
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
                # County Scatter
                html.Div(className='six columns',
                    children=[
                        dcc.Dropdown(
                            id='dropdown-category-filter',
                            #className='row',
                            value='deaths',
                            options=[
                                {'label':'deaths','value':'deaths'},
                                {'label':'cases','value':'cases'}
                            ]
                        ), # close dcc dropdown
                        dcc.Graph(
                            id='scatter',
                            figure = plotting.scatter_deaths_county(
                                COVID_COUNTIES_DF,
                                'deaths',
                                time.strftime('%Y-%m-%d',time.localtime(max(date_dict))),
                                '01001'
                            )
                        ) # close dcc graph
                    ]
                ), # close div tag
            ]
        ),
        html.Div(id='state-section',className='row',
            children=[
                html.Div(id='state-choropleth-div',className='six columns',
                    children=[
                        dcc.Graph(
                            id='state-choropleth', 
                            figure=plotting.choropleth_state_deaths_density(
                                COVID_STATES_DF,
                                'death',
                                time.strftime('%Y-%m-%d',time.localtime(max(date_dict)))
                            )
                        )
                    ]
                ),
                html.Div(id='state-scatter-div',className='six columns',
                    children=[
                        dcc.Dropdown('state-dropdown'),
                        dcc.Graph(id='state-scatter',
                            figure=plotting.generate_state_scatter(
                                COVID_STATES_DF,
                                'NY'
                            )
                        )
                    ]
                )
            ]
        )
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
    [Input(component_id='county-choropleth', component_property='hoverData')],
    [State(component_id='dropdown-category-filter',component_property='value'),
    State('crossfilter_date_slider','value')]
)
def update_scatter_counter(fips_input,category,slider_date):
    # Convert from epoch time to time struct to string
    slider_date = time.strftime('%Y-%m-%d',time.localtime(slider_date))
    # Create a series of cases by date
    try:
        fips = fips_input['points'][0]['location']
    except:
        fips = '01001'
    scatter = plotting.scatter_deaths_county(COVID_COUNTIES_DF,category,slider_date,fips)
    return scatter


# UPDATE choropleth from dropdown or slider
@app.callback(
    Output('county-choropleth','figure'),
    [Input('dropdown-category-filter','value'),
     Input('crossfilter_date_slider','value')]
)

def update_county_choropleth(category, date):
    date = time.strftime('%Y-%m-%d',time.localtime(date))
    return plotting.choropleth_deaths_county(COVID_COUNTIES_DF,
                                             COUNTY_GEOJSON,
                                             category,
                                             date)


@app.callback(
    Output('state-choropleth','figure'),
    [Input('crossfilter_date_slider','value')]
)

def update_state_choropleth(date):
    date = time.strftime('%Y-%m-%d',time.localtime(date))
    return plotting.choropleth_state_deaths_density(COVID_STATES_DF,
                                             'death',
                                             date)

@app.callback(
    Output(component_id='state-scatter', component_property='figure'),
    [Input(component_id='state-choropleth', component_property='hoverData')],
)
def update_state_scatter(state_input):
    try:
        state = state_input['points'][0]['location']
    except:
        state = 'CA'
    scatter = plotting.generate_state_scatter(COVID_STATES_DF,state)
    return scatter




if __name__ == '__main__':
    app.run_server(debug=True, use_reloader = True)

    