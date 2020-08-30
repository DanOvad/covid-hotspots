import pandas as pd
import numpy as np
import geopandas as gpd


import requests
import json
from urllib.request import urlopen
import time
import datetime

from os import path




################################################################################
# Geojson Data

# Get map of US Counties. Here we need FIPS codes and polygons.

def load_county_geojson():
    # Check if geojson file exists
    if path.exists('data/county_geojson.json'):
        # Load from file
        print("Pulling geojson from file.")
        with open('data/county_geojson.json','r') as fout:
            county_geojson = json.load(fout)
    else:
        # Download from plotly
        print("Pulling geojson from Plotly.")
        county_geojson_url = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
        
        with urlopen(county_geojson_url) as response:
            county_geojson = json.load(response)
        
        #Write to file
        with open('data/county_geojson.json','w') as fout:
            json.dump(county_geojson, fout)
    return county_geojson

################################################################################
# Census Data

# Function to generate fips from a state int and county int.
def generate_fips(state_fips, county_fips):
    state_str, county_str = str(state_fips), str(county_fips)
    
    # Check length of state code and append 0's if necessary.
    if len(state_str) == 1:
        state_str = "0"+state_str
        
    # Check length of county code and append 0's if necessary.
    if len(county_str) == 1:
        county_str = "00"+county_str
    elif len(county_str) == 2:
        county_str = "0"+county_str
        
    return state_str+county_str

def get_census_county_data():
    # URL coming from census.gov as ISO encoded csv
    url = 'https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/co-est2019-alldata.csv'
    
    # Read in the data to dataframe
    census_df = pd.read_csv(url, encoding = "ISO-8859-1")
    
    # Define features
    features = ['SUMLEV',
                'REGION',
                'DIVISION',
                'STATE',
                'COUNTY',
                'STNAME',
                'CTYNAME',
                'POPESTIMATE2019',
                'CENSUS2010POP']
    # Use apply across rows to generate fips codes.
    census_df['FIPS'] = census_df[['STATE','COUNTY']].apply(
        lambda x:generate_fips(
            x['STATE'],
            x['COUNTY']
        ), axis = 1
    )

    # Add the new column to our features.
    if 'FIPS' not in features:
        features.append('FIPS')
    
    return census_df[features]

################################################################################
# County Covid Data

# Get covid data at a county level.
def get_covid_county_data():
    '''Function to return covid county data from nytimes github\n
    https://raw.githubusercontent.com/nytimes/covid-19-data'''
    
    print("Retrieving Covid County data")
    # Set NYT github covid-19 data url
    
    today = time.strftime('%Y%m%d')
    filepath = f'data/covid_counties_{today}.csv'
    if path.exists(filepath):
        print("Pulling county data from file.")
        df = pd.read_csv(filepath)
    else:
        print("Pulling county data from github.")
        url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
        df = pd.read_csv(url)
        df.to_csv(filepath, index=False)
    
    # Reassign our fips to be a string of length 5
    #df['fipsnum'] = df['fips']
    df['fips'] = df['fips'].astype(str).apply(lambda x: '0'+x[:4] if len(x) == 6 else x[:5])
    # Set date format
    df['date'] = pd.to_datetime(df['date'], format = '%Y-%m-%d')
    # Create log_deaths column
    df['log_deaths'] = np.log(df['deaths'] + 1)
    return df

################################################################################
# State Covid Data

# Get state covid data from Covid Tracking Project's API
def get_covid_state_data():
    today = time.strftime('%Y%m%d')
    filepath = f'data/covid_states_{today}.csv'
    if path.exists(filepath):
        print("Pulling state data from file.")
        covid_states_df = pd.read_csv(filepath)
    else:
        print("Pulling state data from Covid Tracking API")
        
        # Coronavirus data by state from covidtracking API
        states_url = "https://covidtracking.com/api/states/daily"
        with requests.get(states_url) as response:
            covid_states_df = pd.DataFrame(response.json())
        
        # Set date as datetime format
        covid_states_df['datetime'] = pd.to_datetime(covid_states_df['date'], format="%Y%m%d")
        covid_states_df['date'] = covid_states_df['datetime'].map(lambda x:x.strftime('%Y-%m-%d'))
        # set date to index
        #covid_states_df.set_index(keys='date',inplace=True)
        covid_states_df.to_csv(filepath, index=False)
            
    return covid_states_df

def generate_slider_dates(df):
    # Hardcode a start date
    start_date = '2020-03-01'
    start_date_int = int(time.mktime(datetime.datetime.strptime(start_date, '%Y-%m-%d').timetuple()))

    # Get max date from df
    max_date_int = int(time.mktime(df['date'].max().timetuple()))

    # Create a list of dates from max to min, going back 2 weeks each time
    date_list = range(max_date_int, start_date_int, -(14*24*60*60))
    date_dict = {day:{
        'label':time.strftime('%Y-%m-%d',time.localtime(day)),
        'style':{
            'writing-mode': 'vertical-lr',
            #'text-orientation': 'sideways', 
            'height':'70px',
            'font-size':12,
            'color':'#000000'}}  for day in date_list}
    return date_dict


################################################################################
# National Aggregates

# Get aggregate statistics from state covid data
def generate_state_aggregate_stat(covid_states_df, date, category):
    date_mask = (covid_states_df['date'] == date)
    stat = int(covid_states_df[date_mask][category].sum())
    return f"{stat:,d}"


################################################################################
# Other


def generate_animation_dates(df):
    
    # Hardcode a start date
    start_date = '2020-03-01'
    max_date = df['date'].max()
    

    # Create a list of dates from max to min, going back 2 weeks each time
    date_list = range(max_date_int, start_date_int, -(14*24*60*60))
    date_dict = {day:{'label':time.strftime('%Y-%m-%d',time.localtime(day)),'style':{'writing-mode': 'vertical-rl','text-orientation': 'sideways', 'height':'70px'}}  for day in date_list}
    return date_dict

