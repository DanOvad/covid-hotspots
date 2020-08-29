
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
max_date_str = time.strftime('%Y-%m-%d',time.localtime(max(date_dict)))

style_dictionary = {'national-stats-div':{
                            'textAlign': 'center',
                            'align-self':'center',
                            "border":"4px black solid",
                            "height":100,
                            "width":323, 
                            'backgroundColor':'#A99A96'
                        },
                   'national-stats-item-div':{
                       'align-content':'center',
                       'textAlign': 'center'}
                   }

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
        html.Br(),
        html.H4('National Section'),
        html.Div(id='national-section', children=[
            html.Div(id='national-stats', className='row', children=[
                # Alignment is handled on this Div below.
                html.Div(className='four columns',
                        style={'align-content':'center','textAlign': 'center'},
                        children=[
                    html.Div(id='div-national-deaths', 
                        style={
                            'textAlign': 'center',
                            'align-self':'center',
                            'display':'inline-block',
                            "border":"4px black solid",
                            "height":100,
                            "width":323, 
                            'backgroundColor':'#D6DBDF'
                        },
                        children=[
                            html.H4(id='H4-national-deaths',
                                children=data_processing.generate_state_aggregate_stat(
                                    COVID_STATES_DF,
                                    max_date_str,
                                    'death')
                            ), 
                            html.H5('Total Deaths')
                        ]
                    )
                ]),
                html.Div(className='four columns',
                         style={'align-content':'center','textAlign': 'center'},
                         children=[
                    html.Div(id='div-national-cases',
                        style={
                            'textAlign': 'center',
                            'align-self':'center',
                            'display':'inline-block',
                            "border":"4px black solid",
                            "height":100,
                            "width":323,
                            'backgroundColor':'#D6DBDF'
                        },
                        children=[
                            html.H4(id='H4-national-cases',
                                children=data_processing.generate_state_aggregate_stat(
                                    COVID_STATES_DF,
                                    max_date_str,
                                    'positive')
                            ), 
                            html.H5('Total Positive Cases')
                        ]
                    )
                ]),
                html.Div(className='four columns',
                         style={'align-content':'center','textAlign': 'center'},
                         children=[
                    html.Div(id='div-national-hospitalizedCurrently',
                        style={
                            'textAlign': 'center',
                            'align-self':'center',
                            'display':'inline-block',
                            "border":"4px black solid",
                            "height":100,
                            "width":323,
                            'backgroundColor':'#D6DBDF'
                            #,'margin':dict(
                            #    l=50,
                            #    r=50,
                            #    b=100,
                            #    t=100,
                            #    pad=4
                            #)
                        },
                        children=[
                            html.H4(id='H4-national-hospitalized',
                                children=data_processing.generate_state_aggregate_stat(
                                    COVID_STATES_DF,
                                    max_date_str,
                                    'hospitalizedCurrently')
                            ),
                            html.H5('Current Hospitalization')
                        ]
                    )
                ])
            ]) # close national stats div
            ,html.Div(id='national-graphs', className='row',children=[
                dcc.Graph(id='graph-national-deaths', className='four columns', 
                         figure=plotting.plot_national(COVID_STATES_DF,'death')),
                dcc.Graph(id='graph-national-cases', className='four columns',
                         figure=plotting.plot_national(COVID_STATES_DF,'positive')),
                dcc.Graph(id='graph-national-hospitalizedCurrently', className='four columns',
                         figure=plotting.plot_national(
                             COVID_STATES_DF,
                             'hospitalizedCurrently'))
            ])
            
        ]), # close national section div
            
        html.Br(),
        html.Br(),
        html.Div(id='debug-div'),
        html.Br(),
        html.Div(id='div-slider',style={'height':'100px'},
            children=[
                dcc.Slider(
                    id='date-slider',
                    min=min(date_dict),
                    max=max(date_dict),
                    value=max(date_dict),
                    marks=date_dict,
                    step=None
                ) # slider dcc])
            ]
        ), # slider div
        html.H4('State Section'),
        html.Div(id='state-section',className='row',style={'textAlign':'center'},
            children=[
                html.Div(id='state-choropleth-div',className='six columns',
                    children=[
                        dcc.Graph(
                            id='state-choropleth', 
                            figure=plotting.plot_choropleth_state(
                                COVID_STATES_DF,
                                max_date_str,
                                'death'
                            )
                        )
                    ]
                ),
                html.Div(id='state-scatter-div',className='six columns',
                    children=[
                        dcc.Dropdown(id='state-dropdown',
                            value='death',
                            options=[
                                {'label':'death','value':'death'},
                                {'label':'deathIncrease','value':'deathIncrease'},
                                {'label':'positive','value':'positive'},
                                {'label':'positiveIncrease','value':'positiveIncrease'},
                                {'label':'hospitalizedCurrently','value':'hospitalizedCurrently'},
                                {'label':'hospitalizedCumulative','value':'hospitalizedCumulative'},
                                {'label':'hospitalizedIncrease', 'value':'hospitalizedIncrease'}
                            ]),
                        dcc.Graph(id='state-scatter',
                            figure=plotting.plot_scatter_state(
                                COVID_STATES_DF,
                                'NY',
                                ['deathIncrease','death']
                            )
                        )
                    ]
                )
            ]
        ),
        html.Br(),
        # open div for county graphs
        html.H4('County Section'),
        html.Div(id='county-section', className="row",
            children=[
                html.Div(className='six columns',
                    children=[ # county choropleth div
                        dcc.Graph( # county choropleth graph
                            id='county-choropleth',
                            figure=plotting.plot_choropleth_county(
                                COVID_COUNTIES_DF,
                                COUNTY_GEOJSON,
                                'deaths',
                                date = max_date_str
                            )
                        )
                    ] 
                ), # choropleth div
                # County Scatter
                html.Div(className='six columns',
                    children=[
                        dcc.Dropdown(
                            id='county-dropdown',
                            value='deaths',
                            options=[
                                {'label':'deaths','value':'deaths'},
                                {'label':'cases','value':'cases'}
                            ]
                        ), # close dcc dropdown
                        dcc.Graph(
                            id='county-scatter',
                            figure = plotting.scatter_deaths_county(
                                COVID_COUNTIES_DF,
                                'deaths',
                                max_date_str,
                                '01001'
                            )
                        ) # close dcc graph
                    ]
                ), # close div tag
            ]
        )
    ])

server = app.server
################################################################################
# Text OUTPUT from HOVER
@app.callback(
    Output(component_id='debug-div', component_property='children'),
    [Input(component_id='date-slider', component_property='value')]
)
def update_output_div(date):
    date = time.strftime('%Y-%m-%d',time.localtime(date))
    return 'You\'ve entered "{}"'.format(date)



# National Statistics
@app.callback(
    [Output('H4-national-deaths','children'),
    Output('H4-national-cases','children'),
    Output('H4-national-hospitalized','children')],
    [Input(component_id='date-slider', component_property='value')]
)
def update_national_stats(date):

    date = time.strftime('%Y-%m-%d',time.localtime(date))
    death=data_processing.generate_state_aggregate_stat(
        COVID_STATES_DF,date,'death')
    positive=data_processing.generate_state_aggregate_stat(
        COVID_STATES_DF,date,'positive')
    hospitalizedCurrently=data_processing.generate_state_aggregate_stat(
        COVID_STATES_DF,date,'hospitalizedCurrently')
    return death, positive, hospitalizedCurrently
    
    
# County Choropleth
@app.callback(
    Output('county-choropleth','figure'),
    [Input('county-dropdown','value'),
     Input('date-slider','value')]
)

def update_county_choropleth(category, date):
    date = time.strftime('%Y-%m-%d',time.localtime(date))
    return plotting.plot_choropleth_county(COVID_COUNTIES_DF,
                                             COUNTY_GEOJSON,
                                             category,
                                             date)

# County Scatter
@app.callback(
    Output(component_id='county-scatter', component_property='figure'),
    [Input(component_id='county-choropleth', component_property='hoverData')],
    [State(component_id='county-dropdown',component_property='value'),
    State('date-slider','value')]
)
def update_county_scatter(fips_input,category,slider_date):
    # Convert from epoch time to time struct to string
    slider_date = time.strftime('%Y-%m-%d',time.localtime(slider_date))
    try:
        fips = fips_input['points'][0]['location']
    except:
        fips = '01001'
        # plot county scatter
    scatter = plotting.scatter_deaths_county(COVID_COUNTIES_DF,category,slider_date,fips)
    return scatter


# State Choropleth
@app.callback(
    Output('state-choropleth','figure'),
    [Input('date-slider','value'),
    Input(component_id='state-dropdown',component_property='value')]
)
def update_state_choropleth(date,category):
    date = time.strftime('%Y-%m-%d',time.localtime(date))
    return plotting.plot_choropleth_state(COVID_STATES_DF,
                                             date,
                                             category)
# State Scatter
@app.callback(
    Output(component_id='state-scatter', component_property='figure'),
    [Input(component_id='state-choropleth', component_property='hoverData')],
    [State(component_id='state-dropdown',component_property='value')]
)
def update_state_scatter(state_input,category):
    # Check categories to plot daily and cumulative values for each category type
    if category in ('death','deathIncrease'):
        category_tuple = ('deathIncrease','death')
    elif category in ('positiveIncrease','positive'):
        category_tuple = ('positiveIncrease','positive')
    elif category in ('hospitalizedIncrease','hospitalizedCurrently','hospitalizedCumulative'):
        category_tuple = ('hospitalizedIncrease','hospitalizedCurrently')
    else:
        category_tuple = ('deathIncrease','death')
        
    # Extract state string from hoverData Dict
    try:
        state = state_input['points'][0]['location']
    except:
        state = 'CA'
    
    # Plot State Scatter
    scatter = plotting.plot_scatter_state(COVID_STATES_DF, state, category_tuple)
    return scatter


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader = True)

    