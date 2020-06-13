
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
from dash.dependencies import Input, Output
import time
import datetime
################################################################################
# IMPORT DATA

################################################################################
# Get the Map of US counties
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    county_json = json.load(response)

################################################################################
# IMPORTING
    # Corona County Data
url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
covid_counties = pd.read_csv(url)

# CLEANING
    # Reassign our fips to be a string of length 5
covid_counties['fipsnum'] = covid_counties['fips']
covid_counties['fips'] = covid_counties['fipsnum'].astype(str).apply(lambda x: '0'+x[:4] if len(x) == 6 else x[:5])
    # set date as index
covid_counties['date'] = pd.to_datetime(covid_counties['date'], format = '%Y-%m-%d')
    # Create log_deaths column
covid_counties['log_deaths'] = np.log(covid_counties['deaths'] + 1)
################################################################################
# Import the unemployment data because it has the fips codes
df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
                   dtype={"fips": str})
df['prefix'] = [x[:2] for x in df['fips']]

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


#covid_counties.set_index('date', inplace = True)

date = time.strftime('%Y-%m-%d')
state = 'New York'
state_mask = (covid_counties['state'] == state)
date_mask = (covid_counties['date'] == date)
min_date = int(time.mktime(covid_counties['date'].min().timetuple()))
max_date = int(time.mktime(covid_counties['date'].max().timetuple()))
date_list = range(min_date, max_date, 7*24*60*60)
date_dict = {day:time.strftime('%Y-%m-%d',time.localtime(day))  for day in date_list}

################################################################################
# DATA MUNGING

merged = pd.merge(df, states, left_on='prefix', right_on='fips', how='outer')
    # Rename convention
merged.rename(columns={'fips_x': 'fips_co', 'fips_y':'fips_st'}, inplace=True)

max_date = max(deaths['date'])
deaths = deaths[deaths['date'] == max_date]

final = pd.merge(merged, deaths, how='outer')
final = final.drop(columns=['prefix', 'index'])

# Create a log scale of lived in density
final['logd'] = np.log(final['Lived'])

# create a column for death_per_m
x = final['death']*1000000 / final['Pop']
final['death_per_m'] = x.copy()

final['log_std_density'] = np.log(final['Standard'])

################################################################################

# Brett's graph

def create_state_df(state):
    # Filters columns
    state_df = states_df[['date', 'state', 'death']].copy()
    # Extract state only
    state_df = state_df[state_df['state'] == state].copy()
    # Sort values
    state_df = state_df.sort_values('date')
    # Gets daily
    state_df['daily'] = state_df['death'].diff()
    return state_df

def scatter_deaths_states(state):

    test_df = create_state_df(state)

    fig = go.Figure()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.update_layout(height = 500,title_text="Daily and Total Deaths")
    fig.add_trace(go.Bar(x=test_df['date'],
            y=test_df['daily'], name="Daily"), secondary_y=False,
        )
    fig.add_trace(go.Scatter(x=test_df['date'],
            y=test_df['death'], name="Total"), secondary_y=True,
        )
    fig.update_yaxes(title_text="<b>Daily</b> Deaths", secondary_y=False)
    fig.update_yaxes(title_text="<b>Total</b> Deaths to Date", secondary_y=True)

    return fig

def plot_something_else():
    fig = px.bar(deaths.sort_values('death',ascending=False)[:30],
       x='state',
       y='death',
       title='Total Deaths by State (top 30)',
       height=500)
    return fig

def choropleth_deaths_per_capita():
    fig = go.Figure(data=go.Choropleth(
    locations=final['state'], # Spatial coordinates
    z = final['death_per_m'].astype(float), # Data to be color-coded
    locationmode = 'USA-states', # set of locations match entries in `locations`
    colorscale = 'jet',
    colorbar_title = "Deaths per million",
    zmin=0,
    zmax=1000
    ))

    fig.update_layout(
        height = 500,
        title_text = 'Covid-19 Deaths per capita',
        geo_scope='usa', # limite map scope to USA
    )
    return fig

def choropleth_deaths_density():
    fig = go.Figure(data=go.Choropleth(
    locations=final['state'], # Spatial coordinates
    z = final['death'].astype(float), # Data to be color-coded
    locationmode = 'USA-states', # set of locations match entries in `locations`
    colorscale = 'thermal',
    colorbar_title = "Total Deaths",
    zmin=0,
    zmax=6500,
    ))

    fig.update_layout(
        height = 500,
        title_text = 'Total Covid-19 Deaths by State',
        geo_scope='usa', # limite map scope to USA
    )
    return fig

def choropleth_deaths_lived_density():
    fig = go.Figure(data=go.Choropleth(
    locations=final['state'], # Spatial coordinates
    z = final['logd'].astype(float), # Data to be color-coded
    locationmode = 'USA-states', # set of locations match entries in `locations`
    colorscale = 'gray_r',
    colorbar_title = "Density(ppl/sq km)",
    zmin=0,
    zmax=9
    ))
    fig.update_layout(
        height = 500,
        title_text = 'Lived Density by State',
        title_x = 0.45,
        geo_scope='usa', # limite map scope to USA
    )
    return fig


def choropleth_deaths_stdlived_density():
    fig = go.Figure(data=go.Choropleth(
    locations=final['state'], # Spatial coordinates
    z = final['log_std_density'].astype(float), # Data to be color-coded
    locationmode = 'USA-states', # set of locations match entries in `locations`
    colorscale = 'gray_r',
    colorbar_title = "Density(ppl/sq km)",
    zmin=0,
    zmax=9
    ))
    fig.update_layout(
        height = 500,
        title_text = 'Standard Density by State',
        title_x = 0.45,
        geo_scope='usa', # limite map scope to USA
    )
    return fig


# CHOROPLETH deaths for COUNTY
def choropleth_deaths_county(date):
    date_mask = (covid_counties['date'] == date)
    fig = go.Figure(go.Choropleth(
        z = covid_counties[date_mask]['deaths'], # Data to be color-coded
        zmin=1,
        zmax=30,
        geojson = county_json,
        locations=covid_counties[date_mask]['fips'],
        locationmode = 'geojson-id',
        hovertext = covid_counties[date_mask]['county'],
        colorscale="Viridis",
        colorbar_title = "Deaths"
        #marker_opacity=0.5,
        #marker_line_width=0
    ))
    fig.update_geos(center = {"lat": 37.0902, "lon": -95.7129},
                   scope = 'usa')
    fig.update_layout(height=500, title_text = 'Deaths by county',
                      margin={"r":50,"t":50,"l":50,"b":50})
    return fig

# SCATTER deaths for COUNTY
def scatter_deaths_county(fips = '01001'):
    # Create a series of cases by date
    county_mask = (covid_counties['fips'] == fips)

    # Grab the last date and create date_mask
    date = max(covid_counties[county_mask]['date'])
    date_mask = (covid_counties['date'] == date)

    county_covid_series = covid_counties[county_mask].groupby(by = 'date')['cases'].sum()
    county_deaths_series = covid_counties[county_mask].groupby(by = 'date')['deaths'].sum()

    county_name = covid_counties[county_mask & date_mask]['county'].to_string(index = False)
    state_name = covid_counties[county_mask & date_mask]['state'].to_string(index = False)

    # Create scatter plotly
    scatter = px.scatter(data_frame = county_covid_series,
              x = county_covid_series.index,
              y = county_covid_series,
              title = f'{county_name},{state_name} COVID-19 Cases by Day')
    scatter.update_layout(height = 500, margin = {"r":40,"t":40,"l":40,"b":40})
    scatter.update_yaxes(title_text="<b>Total</b> Cases")
    scatter.update_xaxes(title_text="<b>Date</b>")
    return scatter

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
    # Item 1 - H1
        html.H1(
            children='COVID-19 Hotspot Tracker',
            style={
                'textAlign': 'center',
                'color': colors['text']
            }
        ),
    # Item 2 - Div for text
        html.Div(children='A dashboard to track the spread of coronavirus in the United States.', style={
            'textAlign': 'center',
            'color': colors['text']
        }),
        # Item 1
        html.Div(id='my-hover'),
    # Item 3 - Div for hover - Start of Graphs
        html.Div(children = [
        # Item 1 - Include County Choropleth Graph 
            html.Div([
                dcc.Graph(
                    id='choropleth',
                    figure=choropleth_deaths_county(date = covid_counties['date'].max())
                ),
                dcc.Slider(
                    id='crossfilter_date_slider',
                    min=1583222400,#1579593600,
                    max=time.mktime(datetime.datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d').timetuple()),
                    value=time.mktime(datetime.datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d').timetuple()),
                    marks=date_dict,
                    step=None
                )
            ], className = 'six columns'),
        # Item 2 - Include County Deaths Scatter
            html.Div(
                dcc.Graph(
                    id='scatter',
                    figure = scatter_deaths_county('01001'),
                className="six columns")
            ),
        ], className="row"),
        # Item 4 - Div for State Hover Choropleth Graph
        html.Div(children = [
            # Item 1 - Include State Choropleth Graph
            html.Div(
                    dcc.Graph(
                    id = 'choropleth_state_deaths',
                    figure = choropleth_deaths_density(),
                    className = 'six columns'
                    )
            ),
            # Item 2 - Include State Bar/Line Chart
            html.Div(dcc.Graph(
                id = 'scatter_state_deaths',
                figure = scatter_deaths_states(state = 'NY'),
                className = 'six columns'))
            ], className = "row"),
        html.Div([
             html.Div(dcc.Graph(
                id = 'choropleth_state_million',
                figure = choropleth_deaths_per_capita(),
                 className = 'six columns'
            )),
            html.Div(dcc.Graph(
                id = 'plot_something_else',
                figure = plot_something_else(),
                className = 'six columns'
            ))], className = "row"
        ),
        html.Div([
            html.Div(dcc.Graph(
                id = 'state_deaths_lived_density',
                figure = choropleth_deaths_lived_density(),
                className = 'six columns'
            )#,html.Div(className = 'six columns')
        ),
             html.Div(dcc.Graph(
                id = 'state_deaths_std_lived_density',
                figure = choropleth_deaths_stdlived_density(),
                className = 'six columns'
            ))#,html.Div(className = 'six columns')], className = "row")
        ], className = 'row')
    ])

server = app.server
################################################################################
# Text OUTPUT from HOVER
'''@app.callback(
    Output(component_id='my-hover', component_property='children'),
    [Input(component_id='crossfilter_date_slider', component_property='value')]
)
def update_output_div(input_value):
    #label = input_value['points'][0]['location']
    date = time.strftime('%Y-%m-%d',time.localtime(input_value))
    return 'You\'ve entered "{}"'.format(date)'''


# SCATTER PLOT from HOVER
@app.callback(
    Output(component_id='scatter', component_property='figure'),
    [Input(component_id='choropleth', component_property='hoverData')]
)
def update_scatter_counter(input_value):
    # Create a series of cases by date
    try:
        fips = input_value['points'][0]['location']
    except:
        fips = '01001'
    scatter = scatter_deaths_county(fips)
    return scatter


@app.callback(
    Output(component_id='choropleth', component_property='figure'),
    [Input(component_id='crossfilter_date_slider', component_property='value')]
)
def update_county_choropleth(input_value):
    #date = input_value['points'][0]['location']
    date = time.strftime('%Y-%m-%d',time.localtime(input_value))
    return choropleth_deaths_county(date)


# Brett


@app.callback(
    Output(component_id='scatter_state_deaths', component_property='figure'),
    [Input(component_id='choropleth_state_deaths', component_property='hoverData')]
)
def update_scatter_state(input_value):
    # Create a series of cases by date
    try:
        state = input_value['points'][0]['location']
    except:
        state = 'NY'
    scatter = scatter_deaths_states(state)
    return scatter


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader = True)
