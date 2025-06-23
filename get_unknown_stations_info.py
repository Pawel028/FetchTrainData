import os
import difflib
import re
n=1
from geopy.geocoders import GoogleV3
from bs4 import BeautifulSoup
import requests
import re
# import dash
# from dash import dcc, html
# from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
# from components import RailData, GetTrainList
import os
from pymongo import MongoClient
from datetime import datetime,timedelta,time
import pytz
import dotenv
import json
import asyncio
from time import sleep
dotenv.load_dotenv()






# Replace these with your Google API key and CSE ID


def google_search(query, api_key, cse_id, num_results=5):
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': query,
        'num': num_results
    }
    
    response = requests.get(url, params=params)
    return response.json()

def extract_station_code(snippet):
    # Regular expression to match typical Indian station code patterns (usually 2-5 letters, all uppercase)
    station_code_pattern = r'\b[A-Z]{2,5}\b'
    match = re.search(station_code_pattern, snippet)
    
    if match:
        return match.group(0)
    return None



def get_zone_state_from_station_code(station,Station_Code):
    station1 = ''.join([char for char in station if char.isalpha() or char == ' ' or char == "-"]).lower()
    st_code = station1+"-"+Station_Code.lower()
    url = f'https://www.railyatri.in/stations/{st_code}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        Zone = str(soup.renderContents()).split("Zone")[1].split(">")[2].split("</td")[0].strip()
        state_new = str(soup.renderContents()).split("in District:")[1].split("\n")[0].split("(")[1].split(")")[0]
        return Zone,state_new
    except:
        return None

def get_Long_Lat_from_station_State(station,state):
    station = station+" "+state
    geolocator = GoogleV3(api_key='AIzaSyA-2pIn5Q8lWfxj6Sx5ZQ2CnmUjZ5tIbLQ')
    location = geolocator.geocode(f"{station}, India")
    if len(location[0].split(","))==1:
        station1 = station.split(" ")[0]
        location = geolocator.geocode(f"{station1}, India")
    
    if len(location[0].split(","))==1:
        station2 = station+" "+state
        location = geolocator.geocode(f"{station2}, India")
    
    return station, state, location[0], location.longitude, location.latitude



def find_station_match_curr_data(station,data):
    pattern = re.compile(station.replace("Jn","Junction"), re.IGNORECASE)
    matches = [option for option in data["station"] if pattern.search(option)]
    if len(matches)==0:
        pattern = re.compile(station.split(" ")[0], re.IGNORECASE)
        matches = [option for option in data["station"] if pattern.search(option)]
    if len(matches)==1:
        return data[data["station"]==matches[0]]
    else:
        pass
        

def find_station_match_online_api(station,data):
    station_code = get_station_code(station)
    # print(station_code)
    Zone,State = get_zone_state_from_station_code(station,station_code)
    station, State, Name, Longitude, Latitude = get_Long_Lat_from_station_State(station,State)
    Region = Zone
    dist = 9999999
    ind=0
    for i in range(len(data)):
        dist_new = (Longitude-data.iloc[i]['Longitude'])**2+(Latitude-data.iloc[i]['Latitude'])**2 
        if dist_new<dist:
            ind = i
            dist = dist_new
            Closest_station = data.iloc[ind]['station']
            Closest_Longitude = data.iloc[ind]['Longitude']
            Closest_Latitude = data.iloc[ind]['Latitude']
            Closest_Station_Code = data.iloc[ind]['Station_Code']
            Closest_State = data.iloc[ind]['State']
            Closest_Region = data.iloc[ind]['Region']
    df = pd.DataFrame({"station":station,"Name":Name,"Longitude":Longitude,"Latitude":Latitude,"Station_Code":station_code,"State":State,"Region":Zone,
        "Closest_station":Closest_station,"Closest_Longitude":Closest_Longitude,"Closest_Latitude":Closest_Latitude,
        "Closest_Station_Code":Closest_Station_Code,"Closest_State":Closest_State,"Closest_Region":Closest_Region,"Final State":State,
        "Final_State":State,"Final_Region":Zone},index = range(1))
    return df

def get_station_code(station_name):
    # Create a query to search for the station code
    search_query = f"{station_name} station code"
    results = google_search(search_query, api_key, cse_id)
    
    station_code = None
    for item in results.get('items', []):
        snippet = item['snippet']
        # print(f"Checking snippet: {snippet}")
        station_code = extract_station_code(snippet)
        
        if station_code:
            print(f"Station Code found: {station_code}")
            break
    
    if not station_code:
        print("No station code found in search results.")
    
    return station_code

def get_reponse(train_num)->dict:
    if type(train_num)==str:
        URL = "https://rappid.in/apis/train.php?train_no="+train_num  # Replace with the actual running status page URL
    else:
        URL = "https://rappid.in/apis/train.php?train_no="+str(train_num)  # Replace with the actual running status page URL
    response = requests.get(URL)
    # print(train_num)
    if len(response.text)!=0:
        response_dict = json.loads(response.text)
        # print(response_dict)
        return response_dict
    else:
        return None

async def loop_get_response():
    train_data = pd.read_csv("Train_list.csv")
    train_list = list(train_data["Train_num"])
    tasks = [get_reponse(train_number) for train_number in train_list]
    results = await asyncio.gather(*tasks)
    return results


def store_new_station_info(station,data,collection):
    try:
        a=find_station_match_online_api(station,data)
        
        b={'station': a['station'].values[0],
            'Name': a[ 'Name'].values[0],
            'Longitude': a[ 'Longitude'].values[0],
            'Latitude': a[ 'Latitude'].values[0],
            'Station_Code': a[ 'Station_Code'].values[0],
            'State': a[ 'State'].values[0],
            'Region': a[ 'Region'].values[0],
            'Closest_station': a[ 'Closest_station'].values[0],
            'Closest_Longitude': a[ 'Closest_Longitude'].values[0],
            'Closest_Latitude': a[ 'Closest_Latitude'].values[0],
            'Closest_Station_Code': a[ 'Closest_Station_Code'].values[0],
            'Closest_State': a[ 'Closest_State'].values[0],
            'Closest_Region': a[ 'Closest_Region'].values[0],
            'Final State': a[ 'Final State'].values[0],
            'Final_State': a[ 'Final_State'].values[0],
            'Final_Region': a[ 'Final_Region'].values[0],
            }
        existing_document = collection.find_one(b)

        if not existing_document:
            # If the document doesn't exist, insert the new document
            collection.insert_one(b)
            return 1
            # print("New document inserted.")
        else:
            return 1
    except:
        return 0
class GetData:
    def __init__(self,train_num):
        self.train_num = train_num

    def get_reponse(self)->dict:
        if type(self.train_num)==str:
            URL = "https://rappid.in/apis/train.php?train_no="+self.train_num  # Replace with the actual running status page URL
        else:
            URL = "https://rappid.in/apis/train.php?train_no="+str(self.train_num)  # Replace with the actual running status page URL
        response = requests.get(URL)
        if len(response.text)!=0:
            response_dict = json.loads(response.text)
            # print(response_dict)
            return response_dict
        else:
            return None


if __name__=="__main__":
    while 1<2:
        string = os.getenv("mongodb_string")
        client = MongoClient(string)  # Use your MongoDB connection string
        db = client['train_data']  # Database name
        collection_station = db['Station_Info_20250228']
        collection_train_status = db["train_status"]
        collection_unknown_stations = db["Unknown_Stations"]
        collection_unknown_stations_manual = db["Unknown_Stations_Manual"]
        # unknown_stations = list(collection_unknown_stations.find())
        # station_info = pd.DataFrame(list(collection_station.find()))


        api_key = "AIzaSyA-2pIn5Q8lWfxj6Sx5ZQ2CnmUjZ5tIbLQ"
        cse_id = "350c8578551264f73"
        # Replace with your API key
        geolocator = GoogleV3(api_key=api_key)

        # Geocode an address (address to coordinates)
        location = geolocator.geocode("Trivandrum Kerala, India")
        unknown_stations_list = list(collection_unknown_stations.find())
        unknown_stations = []

        # Add each val to the new list if it doesn't already exist
        for val in unknown_stations_list:
            if val not in unknown_stations:
                unknown_stations.append(val)


        unknown_stations = pd.DataFrame(unknown_stations)        
        data = pd.DataFrame()
        for i, station in enumerate(unknown_stations["Station Name"]):
            # station = station_list[1]
            print(i)
            try:
                station_code = get_station_code(station)
                Zone,State = get_zone_state_from_station_code(station,station_code)
                station1, State, Name, Longitude, Latitude = get_Long_Lat_from_station_State(station,State)
                data1 = pd.DataFrame({"station_code":[station_code],"station_actual":station,"station_new":[station1], "Zone":[Zone],"State":[State], "Name":[Name], "Longitude":[Longitude], "Latitude":[Latitude]})
                data = pd.concat([data,data1])
                collection_unknown_stations.delete_one({"Station Name":station})
            except:
                existing_document = collection_unknown_stations_manual.find_one({"Station Name":station})
                if not existing_document:
                    collection_unknown_stations_manual.insert_one({"Station Name":station})

        data.columns = ["Station_Code","station_old","station","Region","State","Name","Longitude","Latitude"]
        data_fin = data[["station","Station_Code","State","Region","Longitude","Latitude"]]

        collection_station.insert_many(data_fin.to_dict('records'))
        sleep(10)