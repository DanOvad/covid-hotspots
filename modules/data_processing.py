import pandas as pd
import numpy as np
import geopandas as gpd


import requests
import json
from urllib.request import urlopen
import time
import datetime

from os import path

from google.cloud import storage


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
    

    # Use apply across rows to generate fips codes.
    census_df['FIPS'] = census_df[['STATE','COUNTY']].apply(
        lambda x:generate_fips(
            x['STATE'],
            x['COUNTY']
        ), axis=1
    )
    # Define features
    features = ['FIPS',
                'STATE',
                'COUNTY',
                'POPESTIMATE2019',
                'CENSUS2010POP']
    
    return census_df[features]

################################################################################
# County Covid Data

# Get covid data at a county level.
def get_covid_county_data(cache_mode = 1):
    '''Function to return covid county data from nytimes github\n
    https://raw.githubusercontent.com/nytimes/covid-19-data
    
    cache_mode: {0: No caching, 1: Read only caching, 2: Read/write caching}'''
    
    print("Retrieving Covid County data")
    # Set NYT github covid-19 data url
    
    today = time.strftime('%Y%m%d')
    filepath = f'data/covid_counties_{today}.csv.gz'
    
    if cache_mode == 3:    
        
        bucket_name = 'us_covid_hotspot-bucket'
        blob_name = "covid_counties_20200901.csv.gz"
        blob_uri = f"gs://{bucket_name}/{blob_name}"
        print(f"Pulling county data from GCS [{blob_uri}]")
        
        # Get the client object to make the request
        client = storage.Client()
    
        df = pd.read_csv(blob_uri, compression = 'gzip')
        
        # Set date format
        df['date'] = pd.to_datetime(df['date'], format = '%Y-%m-%d')
        
        # Reassign our fips to be a string of length 5
        df['fips'] = df['fips'].astype(str).apply(lambda x: '0'+x[:4] if len(x) == 6 else x[:5])
        
    elif (path.exists(filepath) and cache_mode in (1,2)):
        
        print("Pulling county data from file.")
        
        # Read in data from file
        df = pd.read_csv(filepath, compression = 'gzip')
        
        # Set date format
        df['date'] = pd.to_datetime(df['date'], format = '%Y-%m-%d')
        
        # Reassign our fips to be a string of length 5
        df['fips'] = df['fips'].astype(str).apply(lambda x: '0'+x[:4] if len(x) == 6 else x[:5])
        
        
    else:
        print("Pulling county data from github.")
        # NYT covid-19 github url
        url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
        
        # Read in data from github
        df = pd.read_csv(url)
        
        # Reassign our fips to be a string of length 5
        df['fips'] = df['fips'].astype(str).apply(lambda x: '0'+x[:4] if len(x) == 6 else x[:5])

        # Set date format
        df['date'] = pd.to_datetime(df['date'], format = '%Y-%m-%d')

        # Create log_deaths column
        #df['log_deaths'] = np.log(df['deaths'] + 1)

        # Create log_cases column
        #df['log_cases'] = np.log(df['cases'] + 1)

         
        # Get Census data and Merge dataframes on fips
        df = df.merge(get_census_county_data(),
                        how='left',
                        left_on='fips',
                        right_on='FIPS')
         
        # Cases Per Million
        df['casesPerMillion']=df['cases']/df['POPESTIMATE2019']*1000000
        #df['log_casesPerMillion']= np.log(df['casesPerMillion']+1)

        # Deaths Per Million
        df['deathsPerMillion']=df['deaths']/df['POPESTIMATE2019']*1000000
        #df['log_deathsPerMillion']= np.log(df['deathsPerMillion']+1)
        
        # New Cases by day
        #df['case_diff'] = df.sort_values(by=['fips','state','county','date'])['cases'].diff()
        
         
        df['case_diff'] = df.groupby(
                by = ['fips','county','state'])['cases'].diff()

        #df['case_pm_diff'] = df.sort_values(by=['fips','state','county','date'])['casesPerMillion'].diff()
        
        # New Deaths by day
        df['death_diff'] = df.groupby(
                by = ['fips','county','state'])['deaths'].diff()
        
         
        df["cases_14MA"] = df.groupby(
            by=['fips','county','state'], 
            as_index=False)['case_diff'].rolling(14).mean().reset_index(level=0, drop=True)

        df["deaths_14MA"] = df.groupby(
            by=['fips','county','state'], 
            as_index=False)['death_diff'].rolling(14).mean().reset_index(level=0, drop=True)
        if cache_mode == 2:
            # Write to file
            df.to_csv(filepath, index=False, compression='gzip')
    
    return df

################################################################################
# State Covid Data

# Get state covid data from Covid Tracking Project's API
def get_covid_state_data(cache_mode = 1):
    # Cache mode 
    # 0 = No cache, 
    # 1 = Read only cache
    # 2 = Read/Write cache,
    # 3 = Read from GCS bucket
    
    today = time.strftime('%Y%m%d')
    filepath = f'data/covid_states_{today}.csv.gz'
    
    if cache_mode == 3:
        print("Pulling state data from Cloud Storage")
        bucket_name = 'us_covid_hotspot-bucket'
        blob_name = "covid_states_20200901.csv.gz"
        blob_uri = f"gs://{bucket_name}/{blob_name}"
        print(blob_uri)
        
        # Get the client object to make the request
        client = storage.Client()
    
        covid_states_df = pd.read_csv(blob_uri, compression = 'gzip')
        
    elif (path.exists(filepath) and cache_mode in (1,2)):
        print("Pulling state data from file.")
        covid_states_df = pd.read_csv(filepath, compression = 'gzip')
        
        # Data Cleaning
        covid_states_df['date'] = pd.to_datetime(covid_states_df['date'], format="%Y-%m-%d")
        
    else:
        print("Pulling state data from Covid Tracking API")
        
        # Coronavirus data by state from covidtracking API
        states_url = "https://covidtracking.com/api/states/daily"
        
        with requests.get(states_url) as response:
            covid_states_df = pd.DataFrame.from_records(
                response.json(),
                index = range(len(response.json()))
            )

        # Set date as datetime format
        covid_states_df['date'] = pd.to_datetime(covid_states_df['date'], format="%Y%m%d")
        
        # Pull in state population data
        state_pop = pd.read_csv('data/tbl_states.csv')
        
        # Merge data with state data
        covid_states_df = covid_states_df.merge(state_pop, 
                              how='left',
                              left_on='state',
                              right_on='state')
        
        # Per Capita
        covid_states_df['case_pm'] = covid_states_df['positive']/covid_states_df['Pop']*1000000
        covid_states_df['death_pm'] = covid_states_df['death']/covid_states_df['Pop']*1000000
        
        # Daily Increase Moving Averages
        covid_states_df["deaths_14MA"] = covid_states_df.groupby(
            by=['state'], 
            as_index=False
        )['deathIncrease'].rolling(14).mean().reset_index(level=0, drop=True)
        
        covid_states_df["cases_14MA"] = covid_states_df.groupby(
            by=['state'], 
            as_index=False
        )['positiveIncrease'].rolling(14).mean().reset_index(level=0, drop=True)
        
        
        
        if cache_mode == 2:
            covid_states_df.to_csv(filepath, index=False, compression='gzip')
            
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


