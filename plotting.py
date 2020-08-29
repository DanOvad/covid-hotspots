

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


def plot_national(covid_states_df, category='hospitalizedCurrently'):
    figure = px.bar(data_frame = covid_states_df,
           x='date',
           y = category,
           color='state')
    figure.update_layout(autosize = True, showlegend=False,margin={"r":5,"t":0,"l":5,"b":5}
        #legend=dict(
        #    yanchor="top",
        #    y=0.99,
        #    xanchor="left",
        #    x=0.01
        #)
    )
    return figure
################################################################################
# COUNTY
# SCATTER deaths for COUNTY
def scatter_deaths_county(df, category, slider_date, fips = '01001'):
    # Create a county mask to extract stats across dates.
    county_mask = (df['fips'] == fips)

    # Create series of stats for one county over time
    county_series = df[county_mask].groupby(by = 'date')[category].sum()
    
    # Grab the last date and create date_mask to return one value for names
    date = max(df[county_mask]['date'])
    date_mask = (df['date'] == date)
    
    county_name = df[county_mask & date_mask]['county'].to_string(index = False)
    state_name = df[county_mask & date_mask]['state'].to_string(index = False)
    
    # Greate figure
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(x = county_series.index,
                  y = county_series, 
                name=category
        )
    )
    
    fig.update_layout(
        title=f'{county_name},{state_name} {category} by day',
        margin = {"r":40,"t":40,"l":40,"b":40},
        paper_bgcolor='#D6DBDF',#'rgb(200,200,200)',
        shapes=[
            dict(
              type= 'line',
              yref= 'paper', y0= 0, y1= 1,
              xref= 'x', x0= slider_date, x1= slider_date
            )
        ]
    )
    fig.update_yaxes(title_text=f"<b>Total</b> {category}")
    fig.update_xaxes(title_text="<b>Date</b>")
    return fig

# CHOROPLETH deaths for COUNTY
def plot_choropleth_county(df, geojson, category, date):
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
            colorbar={
                'yanchor':'middle',
                'thicknessmode':'fraction',
                'thickness':.03,
                'title':{'text':f"{category}",'side':'right'}}
            #marker_opacity=0.5,
            #marker_line_width=0
        )
    )
    fig.update_geos(center = {"lat": 37.0902, "lon": -95.7129},
                   scope = 'usa')
    fig.update_layout(
        #height = 400,
        paper_bgcolor='#D6DBDF',
        title_text = f'Deaths by county on {date}',
        margin={"r":5,"t":30,"l":5,"b":5}
    )
    print("Finished Generating Plot")
    return fig

################################################################################
# STATES
# CHOROPLETH for STATES
def plot_choropleth_state(covid_states_df, date, category='death'):
    # Create a mask to filter the df to only a specific date
    date_mask = (covid_states_df['date'] == date)
    # Determine the median of values to plot for legend
    #mean = round(covid_states_df[date_mask][category].mean(),-1)
    
    # Create Figure
    fig = go.Figure(data=
        go.Choropleth(
            locations=covid_states_df[date_mask]['state'],
            z = covid_states_df[date_mask][category].astype(float),
            text=covid_states_df[date_mask]['state'],
            locationmode = 'USA-states',
            colorscale = 'Viridis',
            colorbar={
                'yanchor':'middle',
                'thicknessmode':'fraction',
                'thickness':.03,
                'title':{'text':f"{category}",'side':'right'}}
            #zmin=0,
            #zmax=mean,
        )
    )
    fig.update_geos(center = {"lat": 37.0902, "lon": -95.7129},
                   scope = 'usa')
    
    fig.update_layout(
        autosize=True,
        #height = 400,
        #width = 400,
        margin={"r":5,"t":40,"l":5,"b":5},
        title_text = f'{category} by State on {date}',
        geo_scope='usa',
        paper_bgcolor='#D6DBDF',
        plot_bgcolor='#DCDCDC'
        
    )
    
    return fig

# SCATTER for STATE
def plot_scatter_state(covid_state_df,state,category_tuple=('deathIncrease','death')):
    daily, cumulative = category_tuple
    
    #daily = category_list[0]
    #cumulative = category_list[1]
    
    state_mask = (covid_state_df['state'] == state)
    covid_state_df[state_mask]

    fig = go.Figure()
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    fig.update_layout(#height=400,
                      title_text=f"{state} Daily and Total Deaths",
                      paper_bgcolor='#D6DBDF',
                      legend=dict(
                          yanchor="top",
                          y=1.10,
                          xanchor="left",
                          x=0.01
                    )
    )
    fig.add_trace(
        go.Bar(x=covid_state_df[state_mask]['date'],
            y=covid_state_df[state_mask][daily], name=daily
        ), secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=covid_state_df[state_mask]['date'],
            y=covid_state_df[state_mask][cumulative], 
            name=cumulative
        ),secondary_y=True
    )
    fig.update_yaxes(title_text=f"{daily}", secondary_y=False)
    fig.update_yaxes(title_text=f"{cumulative}", secondary_y=True)

    return fig

# Choropleth animation
def plot_animation(df, category='death'):
    fig = px.choropleth(data_frame=df,
                locations='state',
                color='death',
                locationmode='USA-states',
                animation_frame='date',
                category_orders=animation_date_dict)
    
    fig.update_geos(center = {"lat": 37.0902, "lon": -95.7129},
                    scope = 'usa')
    return fig