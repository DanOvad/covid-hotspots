# README

<b>By:</b> Dan Ovadia<br>
<b>Date:</b> September 4, 2020

[Deployed US Covid-19 Dashboard](https://covid-hotspots-ga-dsi-la-11.herokuapp.com/)
(might take time around a minute the first time you connect, Heroku needs to wake up the dyno; upon refresh it should spring to life.)

This repository holds the code for the components to create a dashboard visualizing Coronavirus spread. It is built using Plotly to generate interactive visualizations and Dash to generate the HTML for the website, respectively. The website is hosted on Heroku.

The data are coming from multiple sources, specifically The New York Times covid-19 github repo, The Atlantic's Covid Tracking Project API, and census.gov. The data are pulled, transformed, and uploaded to Google Cloud Storage using a Cloud Function. The code for the function is stored in the `cloud-function` directory.

#### Table of Contents
1. [Modules](#1---Modules)<br>
Explanation of defined functions created to handle the website
  1. [Data Processing](#Data-Processing-Functions)<br>
    Retrieving and processing data
  2. [Plotting](#Plotting-Functions)<br>
    Generating scatter plots and choropleth plots
2. [Notebooks](#2---Notebooks)<br>
  Description of how the topics each notebook covers.
3. [Heroku App](#3---Data-Processing-Functions)<br>
  Description of the components of the Heroku App
4. [GCP Cloud Function](#4---GCP-Cloud-Function)<br>
  Description of the components of the Cloud Function
5. [Conclusion](#5---Conclusion)<br>


## Objective
To visualize current and historical trends of the coronavirus' spread in the United States at a county and state level. To provide updated statistics on new cases, deaths, and hospitalizations (only at a state level).

---
## 1 - Modules
The modules were split into two categories: (1) Data Processing, and (2) Plotting. Data processing handles any functions required to build out the dataframes needed for plotting. This includes but is not limited to: making HTTP requests to pull and clean data.

### Data Processing Functions

### Plotting Functions

---
## 2 - Notebooks

---
## 3 - Heroku App

---
## 4 - Cloud Functions

---
## 5 - Conclusion
