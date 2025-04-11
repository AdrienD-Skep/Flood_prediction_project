import geopandas as gpd
import pandas as pd
import numpy as np

import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta
import time

import joblib
import json

from huggingface_hub import HfApi

import os

# Access the Hugging Face token from the environment variable
hf_token = os.getenv("HF_TOKEN")

delta_37_days = timedelta(days=37)
delta_30_days = timedelta(days=30)
delta_7_days = timedelta(days=7)
delta_1_day = timedelta(days=1)
def Create_df(data, start_date, end_date, day_time=24):
    result_df = pd.DataFrame()
    day = start_date
    i = 0
    while day <= end_date :
        # Define offsets in hours
        start_30 = i * day_time
        end = start_30 + 31 * day_time # 31 because open meteo end date is inclusive
        start_5 = end - 5 * day_time  # Last 5 days of the 30-day window
        start_1 = end - 1 * day_time  # Last 1 day of the 30-day window
        
        slice_30 = slice(start_30, end)
        slice_5 = slice(start_5, end)
        slice_1 = slice(start_1, end)

        new_row = {
            f"median_{key}_30": np.nanmedian(value[slice_30])
            for key, value in data.items()
        } | {
            f"mean_{key}_{suffix}": np.nanmean(value[slice_])
            for suffix, slice_ in [
                ("30", slice_30),
                ("5", slice_5),
                ("1", slice_1)
            ]
            for key, value in data.items()
        } | {
            f"max_{key}_1": np.nanmax(value[slice_1])
            for key, value in data.items()
        } 
        new_row["date"]= day
        new_row["date_id"]= i
        if len(result_df) == 0 :
            result_df = pd.DataFrame([new_row])
        else :
            result_df.loc[len(result_df)] = new_row
        day = day + delta_1_day
        i += 1
    return result_df


def Get_previous_month_weather(lat, lon, end_date) :

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    start_date = end_date - delta_37_days
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly":  ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "precipitation", "et0_fao_evapotranspiration", "vapour_pressure_deficit", "wind_speed_10m", "wind_gusts_10m"],
        "timezone": "GMT",
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
    }

    responses = openmeteo.weather_api(url, params=params, method="POST")
    complete_result = []
    for j in range(len(responses)) :
        response = responses[j]
        elevation = response.Elevation()

        # Process daily data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
        hourly_dew_point_2m = hourly.Variables(2).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(3).ValuesAsNumpy()
        hourly_et0_fao_evapotranspiration = hourly.Variables(4).ValuesAsNumpy()
        hourly_vapour_pressure_deficit = hourly.Variables(5).ValuesAsNumpy()
        hourly_wind_speed_10m = hourly.Variables(6).ValuesAsNumpy()
        hourly_wind_gusts_10m = hourly.Variables(7).ValuesAsNumpy()

        weather_data = {}
        weather_data["temperature_2m"] = hourly_temperature_2m
        weather_data["relative_humidity_2m"] = hourly_relative_humidity_2m
        weather_data["dew_point_2m"] = hourly_dew_point_2m
        weather_data["precipitation"] = hourly_precipitation
        weather_data["et0_fao_evapotranspiration"] = hourly_et0_fao_evapotranspiration
        weather_data["vapour_pressure_deficit"] = hourly_vapour_pressure_deficit
        weather_data["wind_speed_10m"] = hourly_wind_speed_10m
        weather_data["wind_gusts_10m"] = hourly_wind_gusts_10m

        result_df = Create_df(weather_data, start_date + delta_30_days,end_date)

        result_df["elevation"] = elevation    
        result_df["lat"] = lat[j]
        result_df["lon"] = lon[j]
        
        complete_result.append(result_df)
    return complete_result

def Get_soil_moisture(lat, lon, end_date) :

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    start_date = end_date - delta_37_days
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["soil_moisture_0_to_7cm", "soil_moisture_7_to_28cm", "soil_moisture_28_to_100cm", "soil_moisture_100_to_255cm"],
        "models": "ecmwf_ifs025",
        "timezone": "GMT",
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
    }
    responses = openmeteo.weather_api(url, params=params, method="POST")
    complete_result = []
    for j in range(len(responses)) :
        response = responses[j]

        # Process daily data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_soil_moisture_0_to_7cm = hourly.Variables(0).ValuesAsNumpy()
        hourly_soil_moisture_7_to_28cm = hourly.Variables(1).ValuesAsNumpy()
        hourly_soil_moisture_28_to_100cm = hourly.Variables(2).ValuesAsNumpy()
        hourly_soil_moisture_100_to_255cm = hourly.Variables(3).ValuesAsNumpy()


        weather_data = {}

        weather_data["soil_moisture_0_to_7cm"] = hourly_soil_moisture_0_to_7cm
        weather_data["soil_moisture_7_to_28cm"] = hourly_soil_moisture_7_to_28cm
        weather_data["soil_moisture_28_to_100cm"] = hourly_soil_moisture_28_to_100cm
        weather_data["soil_moisture_100_to_255cm"] = hourly_soil_moisture_100_to_255cm
        
        result_df = Create_df(weather_data, start_date + delta_30_days,end_date)
        result_df["lat"] = lat[j]
        result_df["lon"] = lon[j]
        complete_result.append(result_df)
    return complete_result

def get_river_discharge(lat,lon, end_date):
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    start_date = end_date - delta_37_days
    url = "https://flood-api.open-meteo.com/v1/flood"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "river_discharge",
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "models": "seamless_v4",
        "timezone": "GMT"
    }
    responses = openmeteo.weather_api(url, params=params, method="POST")
    complete_result = []
    for j in range(len(responses)) :
        response = responses[j]
        # Process daily data. The order of variables needs to be the same as requested.
        daily = response.Daily()
        daily_river_discharge = daily.Variables(0).ValuesAsNumpy()
        daily_data = {}
        
        daily_data["river_discharge"] = daily_river_discharge
        result_df = Create_df(daily_data, start_date + delta_30_days,end_date,1)
        result_df["lat"] = lat[j]
        result_df["lon"] = lon[j]
        complete_result.append(result_df)
    return complete_result


def Get_marine_weather(lat, lon, sea_lat, sea_lon, sea_distance, end_date):
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=2, backoff_factor=0.1)  
    openmeteo = openmeteo_requests.Client(session=retry_session)
    start_date = end_date - delta_37_days
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
                "latitude": sea_lat,
                "longitude": sea_lon,
                "hourly": ["wave_height", "sea_level_height_msl"],
                "timezone": "GMT",
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
            }
    responses = openmeteo.weather_api(url, params=params, method="POST")
    complete_result = []
    
    for j in range(len(responses)) :
        response = responses[j]
        # Process daily data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_wave_height = hourly.Variables(0).ValuesAsNumpy()
        hourly_sea_level_height_msl = hourly.Variables(1).ValuesAsNumpy()


        hourly_data  = {}
        hourly_data["wave_height"] = hourly_wave_height
        hourly_data["sea_level_height_msl"] = hourly_sea_level_height_msl
        result_df = Create_df(hourly_data, start_date + delta_30_days,end_date)
        result_df["lat"] = lat[j]
        result_df["lon"] = lon[j]
        result_df["Sea distance"] = sea_distance[j]
        complete_result.append(result_df)
    return complete_result

def update_gdf(row , df):
    df_location = df[(df["lat"] == row["representative_point_lat"]) & (df["lon"] == row["representative_point_lon"])]
    date_ids = df_location["date_id"].unique()

    row["mode_flood_type"] = df_location[f"flood_type"].mode().iloc[0]
    for date_id in date_ids :
        row[f"flood_type_{date_id}"] = df_location[(df_location["date_id"] == date_id)]["flood_type"].iloc[0]

    row["max_flood_proba"] = df_location[f"flood_proba"].max()
    row["mean_flood_proba"] = df_location[f"flood_proba"].mean()
    row["median_flood_proba"] = df_location[f"flood_proba"].median()
    for date_id in date_ids :
        row[f"flood_proba_{date_id}"] = df_location[(df_location["date_id"] == date_id)]["flood_proba"].iloc[0]
    return row

def update_geo_data(gdf):
    CHUNK_SIZE = 100
    TOTAL_ROWS = len(gdf)

    predict_flood_model = joblib.load("model_XGBC_predict_flood.pkl")
    predict_type_model = joblib.load("model_XGBC_flood_type.pkl")
    for start_idx in range(0, TOTAL_ROWS, CHUNK_SIZE):
        end_idx = min(start_idx + CHUNK_SIZE, TOTAL_ROWS)
        chunk = gdf.iloc[start_idx:end_idx].copy()
        
        # Get current time once per chunk to ensure consistency
        now = datetime.now()
        end_date = now + delta_7_days
        one_min_ago = now - timedelta(minutes=1)
        
        # Check conditions
        date_condition = (chunk['last_update'].dt.date != now.date()).any()
        time_condition = (gdf['last_update'] < one_min_ago).all()
        while not time_condition :
            time.sleep(65)
            now = datetime.now()
            one_min_ago = now - timedelta(minutes=1)
            time_condition = (gdf['last_update'] < one_min_ago).all()
            


        if date_condition:
            try:
                lat = chunk["representative_point_lat"].tolist()
                lon = chunk["representative_point_lon"].tolist()
                sea_lat = chunk["Sea latitude"].tolist()
                sea_lon = chunk["Sea longitude"].tolist()
                sea_distance = chunk["Sea distance"].tolist()

                weather_data = Get_previous_month_weather(lat,lon, end_date)
                soil_moisture_data = Get_soil_moisture(lat, lon, end_date)
                river_data = get_river_discharge(lat, lon, end_date)
                marine_weather_data = Get_marine_weather(lat, lon, sea_lat, sea_lon, sea_distance, end_date)
                weather_df = pd.concat(weather_data)
                soil_moisture_df = pd.concat(soil_moisture_data)
                river_df = pd.concat(river_data)
                marine_df = pd.concat(marine_weather_data)
                complete_df = pd.merge(weather_df, soil_moisture_df,on=["date", "lat", "lon", "date_id"])
                complete_df = pd.merge(complete_df, river_df,on=["date", "lat", "lon", "date_id"])
                complete_df = pd.merge(complete_df, marine_df,on=["date", "lat", "lon", "date_id"])
                complete_df["month"] = complete_df['date'].dt.month

                ordered_features = predict_flood_model.feature_names_in_
                X = complete_df[ordered_features]
                predicted_flood_proba = predict_flood_model.predict_proba(X)
                predicted_type = predict_type_model.predict(X)

                complete_df["flood_proba"] = np.round(predicted_flood_proba[:,1] * 100)
                complete_df["flood_type"] = predicted_type

                gdf.loc[chunk.index,:] = gdf.loc[chunk.index,:].apply(lambda x : update_gdf(x,complete_df), axis=1)
                gdf.loc[chunk.index, 'last_update'] = now
                
                print(f"Processed rows {start_idx}-{end_idx-1} at {now}")

                gdf.to_file("europe_admin.geojson", driver="GeoJSON")
                api = HfApi(token=hf_token)
                api.upload_file(
                    path_or_fileobj="europe_admin.geojson",  # Path to the local file
                    path_in_repo="europe_admin.geojson",     # Path in the repository
                    repo_id="AdrienD-Skep/geo_flood_data",       # Repository name
                    repo_type="dataset",                     # Type of repository
                )
                
            except Exception as e:
                print(f"Error processing chunk {start_idx}-{end_idx-1}: {str(e)}")
                time.sleep(65)
        else:
            print(f"Skipping chunk {start_idx}-{end_idx-1} - already up to date")
    
    return json.loads(gdf.to_json())