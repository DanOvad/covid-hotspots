import os
import sys
import pandas as pd
from google.cloud import storage
import time

# Custom files and modules
from config import config
from modules import data_processing


if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
    print("You need to set your environment variable.")
    sys.exit()
else:
    print(f"Credentials are in environment: {'GOOGLE_APPLICATION_CREDENTIALS' in os.environ}")
    
    
def write_blob_to_gcs(bucket_name, blob_name, filepath):
    # Client to bundle configuration needed for API requests.
    client = storage.Client()

    # Extract the bucket object from the client bundle
    bucket = client.get_bucket(bucket_name)

    # Instantiate or extract the blob object from the bucket
    blob = storage.blob.Blob(blob_name,bucket)

    # Upload the file to the specific blob
    blob.upload_from_filename(filepath)
    
    return [blob_item.name for blob_item in bucket.list_blobs()]

def main():
    # State Data - Setting Variables
    t0 = time.time()
    BUCKET_NAME = 'us_covid_hotspot-bucket'
    BLOB_NAME = 'covid_states.csv.gz'
    FILEPATH = f"data/{BLOB_NAME}"
    
    # Read in new county data from Covid Tracking Project
    COVID_STATES_DF = data_processing.get_covid_state_data(cache_mode = 0)

    print(f"Writing state DF to {BLOB_NAME}")
    # Write DF to csv.gz
    COVID_STATES_DF.to_csv(FILEPATH, 
                           index = False,
                           compression = 'gzip')
    
    # Write file to GCS
    print(f"Writing {BLOB_NAME} to GCS {BUCKET_NAME}")
    write_blob_to_gcs(BUCKET_NAME, BLOB_NAME, FILEPATH)

    # County Data - Setting Variables
    BUCKET_NAME = 'us_covid_hotspot-bucket'
    BLOB_NAME = 'covid_counties.csv.gz'
    FILEPATH = f"data/{BLOB_NAME}"

    # Getting Data
    COVID_COUNTIES_DF = data_processing.get_covid_county_data(cache_mode=0)
    
    print(f"Writing county DF to {BLOB_NAME}")
    # Writing DF to csv.gz
    COVID_COUNTIES_DF.to_csv(FILEPATH, 
                           index = False,
                           compression = 'gzip')
    
    
    # Write file to GCS
    print(f"Writing {BLOB_NAME} to GCS {BUCKET_NAME}")
    write_blob_to_gcs(BUCKET_NAME, BLOB_NAME, FILEPATH)
    print(f"This process took {time.time()-t0} seconds")
main()
