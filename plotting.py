

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
def scatter_deaths_county(df,category,fips = '01001'):
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
    scatter.update_layout(height = 600, margin = {"r":40,"t":40,"l":40,"b":40})
    scatter.update_yaxes(title_text=f"<b>Total</b> {category}")
    scatter.update_xaxes(title_text="<b>Date</b>")
    return scatter

# CHOROPLETH deaths for COUNTY
def choropleth_deaths_county(df, geojson, category, date):
    print("Generating Plot")
    date_mask = (df['date'] == date)
    median = round(df[date_mask][category].mean(),-1)
    fig = go.Figure(go.Choropleth(
        z = df[date_mask][category], # Data to be color-coded
        zmin=1,
        zmax=median,
        geojson = geojson,
        locations=df[date_mask]['fips'],
        locationmode = 'geojson-id',
        hovertext = df[date_mask]['county'],
        colorscale="Viridis",
        colorbar_title = f"{category}"
        #marker_opacity=0.5,
        #marker_line_width=0
    ))
    fig.update_geos(center = {"lat": 37.0902, "lon": -95.7129},
                   scope = 'usa')
    fig.update_layout(height=600, title_text = f'Deaths by county on {date}',
                      margin={"r":5,"t":40,"l":5,"b":40})
    print("Finished Generating Plot")
    return fig