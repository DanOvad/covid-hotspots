import pandas as pd
import numpy as np
import geopandas as gpd


import requests
import json
from urllib.request import urlopen
import time
import datetime

from os import path



# Get map of US Counties. Here we need FIPS codes and polygons

def load_county_geojson():
    # Check if geojson file exists
    if path.exists('data/county_geojson.json'):
        # Load from file
        with open('data/county_geojson.json','r') as fout:
            county_geojson = json.load(fout)
    else:
        # Download from plotly
        county_geojson_url = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
        
        with urlopen(county_geojson_url) as response:
            county_geojson = json.load(response)
        
        #Write to file
        with open('data/county_geojson.json','w') as fout:
            json.dump(county_geojson, fout)
    return county_geojson

    
def get_covid_county_data():
    '''Function to return covid county data from nytimes github\n
    https://raw.githubusercontent.com/nytimes/covid-19-data'''
    
    print("Retrieving Covid County data")
    # Set NYT github covid-19 data url
    
    today = time.strftime('%Y%m%d')
    filepath = f'data/covid_counties_{today}.csv'
    if path.exists(filepath):
        print("Pulling from file.")
        df = pd.read_csv(filepath)
    else:
        print("Pulling from github.")
        url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
        df = pd.read_csv(url)
        df.to_csv(filepath)
    
    # Reassign our fips to be a string of length 5
    df['fipsnum'] = df['fips']
    df['fips'] = df['fipsnum'].astype(str).apply(lambda x: '0'+x[:4] if len(x) == 6 else x[:5])
    # Set date format
    df['date'] = pd.to_datetime(df['date'], format = '%Y-%m-%d')
    # Create log_deaths column
    df['log_deaths'] = np.log(df['deaths'] + 1)
    return df


def get_covid_state_data():
    # Coronavirus data by state from covidtracking API
    states_url = "https://covidtracking.com/api/states/daily"
    # Create requests object
    r = requests.get(states_url)
    
    
    # Cleaning
    # Set date as dateTime format
    states_df['date'] = pd.to_datetime(states_df.date, format="%Y%m%d")

    #Extract values for date, state, and death
    states_df = states_df[['date', 'state', 'death', 'total']].sort_values('date')

    deaths = states_df.reset_index()
    return states_df

def generate_slider_dates(df):
    # Hardcode a start date
    start_date = '2020-03-01'
    start_date_int = int(time.mktime(datetime.datetime.strptime(start_date, '%Y-%m-%d').timetuple()))

    # Get max date from df
    max_date_int = int(time.mktime(df['date'].max().timetuple()))

    # Create a list of dates from max to min, going back 2 weeks each time
    date_list = range(max_date_int, start_date_int, -(14*24*60*60))
    date_dict = {day:{'label':time.strftime('%Y-%m-%d',time.localtime(day)),'style':{'writing-mode': 'vertical-rl','text-orientation': 'sideways', 'height':'80px'}}  for day in date_list}
    return date_dict