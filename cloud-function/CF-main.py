import base64
import os
import sys
import time

import pandas as pd
import requests
import gzip
from io import BytesIO, TextIOWrapper

from google.cloud import storage

def hello_pubsub(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    main()
    #pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(pubsub_message)


# Get state covid data from Covid Tracking Project's API
def generate_covid_state_data():
    ''' This function is specific to gathering data from github with no caching. And loading that data to GCS.'''
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
    #state_pop = pd.read_csv('data/tbl_states.csv')
        
    bucket_name = 'us_covid_hotspot-bucket'
    blob_name = "states_populuations.csv"
    blob_uri = f"gs://{bucket_name}/{blob_name}"
        
    # Get the client object to make the request
    client = storage.Client()
    state_pop = pd.read_csv(blob_uri)
        
        
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
            
    return covid_states_df


## County Data, starting with Census Data

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


# Get covid data at a county level.
def generate_covid_county_data():
    '''Function to return covid county data from nytimes github\n
    https://raw.githubusercontent.com/nytimes/covid-19-data
    This function is exclusive to our cloud function deployment.
    '''
    
    print("Pulling covid county data from github.")
    # NYT covid-19 github url
    url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    
    # Read in data from github
    df = pd.read_csv(url)
    
    # Reassign our fips to be a string of length 5
    df['fips'] = df['fips'].astype(str).apply(lambda x: '0'+x[:4] if len(x) == 6 else x[:5])
    # Set date format
    df['date'] = pd.to_datetime(df['date'], format = '%Y-%m-%d')

    # Get Census data and Merge dataframes on fips
    df = df.merge(get_census_county_data(),
                    how='left',
                    left_on='fips',
                    right_on='FIPS')
     
    # Cases Per Million
    df['casesPerMillion']=df['cases']/df['POPESTIMATE2019']*1000000
    # Deaths Per Million
    df['deathsPerMillion']=df['deaths']/df['POPESTIMATE2019']*1000000
    
     
    df['case_diff'] = df.groupby(
            by = ['fips','county','state'])['cases'].diff()
    #df['case_pm_diff'] = df.sort_values(by=['fips','state','county','date'])['casesPerMillion'].diff()
    
    # New Deaths by day
    df['death_diff'] = df.groupby(
            by = ['fips','county','state'])['deaths'].diff()
    
     
    df["cases_14MA"] = df.groupby(
        by=['fips','county','state'], 
        as_index=False)['case_diff'].rolling(14).mean().reset_index(level=[0,1,2], drop=True)
    df["deaths_14MA"] = df.groupby(
        by=['fips','county','state'], 
        as_index=False)['death_diff'].rolling(14).mean().reset_index(level=[0,1,2], drop=True)

    return df

def write_df_to_GCS(df, blob_name):
    bucket_name = 'us_covid_hotspot-bucket'
    blob_uri = f"gs://{bucket_name}/{blob_name}"
    
    # Instantiate BytesIO Buffer
    gz_buffer = BytesIO()
    
    # Instantiate a GzipFile Object using the BytesIO object, 
      # write to it using a text wrapper.
    print(f"Writing {blob_name} to gzip")
    t0 = time.time()
    with gzip.GzipFile(mode='w', fileobj=gz_buffer) as gz_file:
        df.to_csv(TextIOWrapper(gz_file,'utf8'),
                 index=False)
    print(f"Zipping took {time.time()-t0} seconds")
    gz_buffer.seek(0)
    print(f"Opening GCS")
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = storage.blob.Blob(blob_name, bucket)
    t0 = time.time()
    blob.upload_from_file(file_obj=gz_buffer, content_type='text/csv', timeout=240)
    print(time.time()-t0)
    #return [blob_item.name for blob_item in bucket.list_blobs()]



def main():
    #####
    # State Data - Setting Variables
    
    BUCKET_NAME = 'us_covid_hotspot-bucket'
    BLOB_NAME = 'covid_states.csv.gz'
    
    # Read in new county data from Covid Tracking Project
    t0 = time.time()
    DF = generate_covid_state_data()
    print(f"Getting covid_states_df took: {round(time.time() - t0,2)} seconds")
    # Write df to GCS
    
    print(f"Writing {BLOB_NAME} to GCS {BUCKET_NAME}")
    t0=time.time()
    # Write to Bucket - state
    write_df_to_GCS(COVID_STATES_DF, BLOB_NAME)
    print(f"Writing {BLOB_NAME} took: {round(time.time()-t0,2)} seconds")
    
    ######
    # County Data - Setting Variables
    BLOB_NAME = 'covid_counties.csv.gz'

    # Getting Data
    t0 = time.time()
    DF = generate_covid_county_data()
    print(f"Getting covid_county_df took: {round(time.time() - t0,2)} seconds")
    
    # Write file to GCS
    print(f"Writing {BLOB_NAME} to GCS {BUCKET_NAME}")
    write_df_to_GCS(COVID_COUNTIES_DF, BLOB_NAME)
    print(f"This process took {time.time()-t0} seconds")
    
    
    
def main():
    # State Data - Setting Variables
    BUCKET_NAME = 'us_covid_hotspot-bucket'
    BLOB_NAME = 'covid_states.csv.gz'
    
    # Read and transform in state data from Covid Tracking Project
    DF = generate_covid_state_data()
    
    # Write to Bucket - state
    print(f"Writing {BLOB_NAME} to GCS {BUCKET_NAME}")
    write_df_to_GCS(COVID_STATES_DF, BLOB_NAME)
    
    
    # County Data - Setting Variables
    BLOB_NAME = 'covid_counties.csv.gz'

    # Read and transform county data from New York Times
    DF = generate_covid_county_data()
    
    # Write file to GCS
    print(f"Writing {BLOB_NAME} to GCS {BUCKET_NAME}")
    write_df_to_GCS(COVID_COUNTIES_DF, BLOB_NAME)