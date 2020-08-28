

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


# SCATTER deaths for COUNTY
def scatter_deaths_county(df, category, slider_date, fips = '01001'):
    # Create a series of cases by date
    county_mask = (df['fips'] == fips)

    # Grab the last date and create date_mask
    date = max(df[county_mask]['date'])
    date_mask = (df['date'] == date)

    county_covid_series = df[county_mask].groupby(by = 'date')['cases'].sum()
    county_deaths_series = df[county_mask].groupby(by = 'date')['deaths'].sum()
    
    county_series = df[county_mask].groupby(by = 'date')[category].sum()
    
    county_name = df[county_mask & date_mask]['county'].to_string(index = False)
    state_name = df[county_mask & date_mask]['state'].to_string(index = False)

    # Create scatter plotly
    scatter = px.scatter(data_frame = county_series,
              x = county_series.index,
              y = county_series,
              title = f'{county_name},{state_name} {category} by day')
    scatter.update_layout(
        height = 400, 
        margin = {"r":40,"t":40,"l":40,"b":40},
        shapes=[
            dict(
              type= 'line',
              yref= 'paper', y0= 0, y1= 1,
              xref= 'x', x0= slider_date, x1= slider_date
            )
        ]
    )
    scatter.update_yaxes(title_text=f"<b>Total</b> {category}")
    scatter.update_xaxes(title_text="<b>Date</b>")
    return scatter

# CHOROPLETH deaths for COUNTY
def choropleth_deaths_county(df, geojson, category, date):
    print("Generating Plot")
    date_mask = (df['date'] == date)
    mean = round(df[date_mask][category].mean(),-1)
    
    # Generate Plot
    fig = go.Figure(
        go.Choropleth(
            z = df[date_mask][category], # Data to be color-coded
            zmin=1,
            zmax=mean,
            geojson = geojson,
            locations=df[date_mask]['fips'],
            locationmode = 'geojson-id',
            hovertext = df[date_mask]['county'],
            colorscale="Viridis",
            colorbar_title = f"{category}"
            #marker_opacity=0.5,
            #marker_line_width=0
        )
    )
    fig.update_geos(center = {"lat": 37.0902, "lon": -95.7129},
                   scope = 'usa')
    fig.update_layout(
        #height = 400,
        title_text = f'Deaths by county on {date}',
        margin={"r":5,"t":30,"l":5,"b":5}
    )
    print("Finished Generating Plot")
    return fig


# States

def choropleth_state_deaths_density(covid_states_df, category, date):
    # Create a mask to filter the df to only a specific date
    date_mask = (covid_states_df['date'] == date)
    # Determine the median of values to plot for legend
    mean = round(covid_states_df[date_mask][category].mean(),-1)
    
    # Create Figure
    fig = go.Figure(data=go.Choropleth(
        locations=covid_states_df[date_mask]['state'],
        z = covid_states_df[date_mask][category].astype(float),
        locationmode = 'USA-states',
        colorscale = 'thermal',
        colorbar_title = f"Total {category}",
        zmin=0,
        zmax=mean,
    ))

    fig.update_layout(
        #height = 400,
        title_text = f'Total Covid-19 {category} by State on {date}',
        geo_scope='usa', # limite map scope to USA
    )
    return fig


def generate_state_scatter(covid_state_df,state):
    
    state_mask = (covid_state_df['state'] == state)
    covid_state_df[state_mask]

    fig = go.Figure()
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.update_layout(height=500,title_text="Daily and Total Deaths")
    fig.add_trace(go.Bar(x=covid_state_df[state_mask]['date'],
            y=covid_state_df[state_mask]['deathIncrease'], name="deathIncrease"), secondary_y=False,
        )
    fig.add_trace(
            go.Scatter(x=covid_state_df[state_mask]['date'],
                y=covid_state_df[state_mask]['death'], 
                name="Total"
            ),secondary_y=True
        )
    fig.update_yaxes(title_text="<b>Daily</b> Deaths", secondary_y=False)
    fig.update_yaxes(title_text="<b>Total</b> Deaths to Date", secondary_y=True)

    return fig