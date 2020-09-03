# README

<b>By:</b> Dan Ovadia<br>
<b>Date:</b> September 3, 2020
## Google Cloud Platform (GCP) Components

This read me will explain how the Google Cloud Platform components work to support the Heroku App hosting the covid dashboard. 

### 1. Google Cloud Storage (GCS)

A GCS bucket was created to host `covid_counties.csv`, `covid_states.csv`, and `states_population.csv`. The files were compressed using gZip and loaded using the `google-cloud-storage` python library. 

### 2. Google Cloud Function (CGF)

To automate the data processing and loading to the Cloud Storage bucket, a cloud function was created specifically to do the following:

- Retrieve required data from datasources:
    - New York Times github (county data)
    - The Atlantic's Covid Tracking Project (state data)
    - Census.gov (county population data)
- Process the data in pandas to clean and create fields for the dashboard.
- Transform the dataframes to a BytesIO objects, compress using gzip. 
- Load the gziped buffer to Cloud Storage.

### 3. Google Pub/Sub

A Pub/Sub topic was created specifically for the Cloud Function to receive triggers from the Cloud Scheduler. The Cloud Function is subscribed to the Pub/Sub topic as it's trigger. The Cloud Scheduler creates a cron job that writes to the Pub/Sub topic, which subsequently triggers the Cloud Function to in reliable interviews as prescribed.

### 4. Google Cloud Scheduler

A cron job was created to write to the Pub/Sub topic and subsequently run the Cloud Function, which updates our Google Cloud Storage buckets.

---
## Creating the Cloud Function
In order to create the Cloud Function, a couple pieces are required:
1. A python script, likely named `main.py` which runs the processes in the cloud.
2. A `requirements.txt` file which represents the python libraries needed to be imported to support the python script.
3. Any other dependences such as custom modules.

### Script

### Requirements.txt
In order to accurately generate the `requirements.txt` file, it is common practice to create a fresh virtual python environment and import specific dependencies for your scripts. This is easily done using either [venv](https://docs.python.org/3/library/venv.html) or [conda](https://uoa-eresearch.github.io/eresearch-cookbook/recipe/2014/11/20/conda/). 

Test run the code in the virtual environment to make sure that all requirements have been satisfied. This is also a good time to check to make sure that your code does not have any other dependencies such as local data, or other local module references.

Next, we generate the `requirements.txt` file. To export a list of installed packages and respective versions, run the following in terminal while in the project directory: 
<pre><code>pip freeze > requirements.txt</code></pre>
In this code, `pip freeze` generates a list with `package`==`version` for all dependencies in your virtual environment.

#### In Practice
I ran into some trouble while trying to create the requirements.txt file. I am more comfortable using `pip` and `venv` than I am using `conda`. Below are some of the issues I ran into:

1. I had some version differences between installations using pip and installations using conda. For example, `google-cloud-storage` was installed as `v 1.28.0` using conda, while pip installed `v 1.31.0` the most recent version. At the time of this writing `v 1.31.0` had only been out for less than a week, so it's only fair. 

2. I had issues producing a viable `requirements.txt` file. I tried using both pip and conda. 

    <b>Using pip:</b> <pre><code>pip freeze > requirements.txt</code></pre> 

    failed to return version numbers for conda installed packages, specifically returning `package==@file:////[some-path]`. 
    
    <b>Using Conda:</b> <pre><code>conda list --export > requirements.txt</code></pre>
    
    returned a file completely in the wrong format, specifically `package=version=build=channel`, instead of `package==version` as GCF was expecting.


In the end, I created a virtual python environment using `venv` and `pip installed` required packages and the whole process was seemless.  It was a lot more intuitive for me and has always just worked seemlessly.

## Conclusion
In conclusion, this process was actually incredibly easy. During the process I realized that App Engine automatically creates a bucket in Cloud Storage associated to the App. If I had hosted the web application on GCP from the start I likely could have leveraged that functionality, instead of creating a separate GCS bucket dedicated to hosting covid data.

Kudos to Wallace Wong for writing a linkedIn post that helped guide me. 

[Scheduling Python scripts on GCP using Cloud Functions and Scheduler](https://www.linkedin.com/pulse/scheduling-python-scripts-gcp-using-cloud-functions-scheduler-wong/?trackingId=DmoCY%2FbITJygLGkQ0t6EqA%3D%3D) - By Wallace Wong, Nov 19, 2019
