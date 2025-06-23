from kafka import KafkaConsumer
from pymongo import MongoClient
from json import loads, JSONDecodeError
import os
import dotenv
from src.FetchTrainData.utils.common import read_yaml, create_directories,save_json
from src.FetchTrainData.components import RailData, GetTrainList
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
import json
# Load environment variables (for MongoDB connection string)
dotenv.load_dotenv()
config = read_yaml(Path("config/config.yaml"))
train_list_obj = GetTrainList(config.Train_list.Train_list_file)
# print(train_list["Train_num"])
train_list_obj.get_train_list()
string = train_list_obj.mongo_string

client = MongoClient(string) 

db = client['train_data']  # Database name
collection = db['train_status_2']  # Collection name
collection_station_info = db['Station_Info']
station_info = pd.DataFrame(list(collection_station_info.find()))

def find_station_match_curr_data(station):
    pattern = re.compile(station.replace("Jn","Junction"), re.IGNORECASE)
    matches = [option for option in station_info["station"] if pattern.search(option)]
    if len(matches)==0:
        pattern = re.compile(station.split(" ")[0], re.IGNORECASE)
        matches = [option for option in station_info["station"] if pattern.search(option)]
    if len(matches)>=1:
        return station_info[station_info["station"]==matches[0]]
    else:
        pass


# Kafka Consumer Setup
consumer = KafkaConsumer(
    'hello_world',  # Your Kafka topic name
    bootstrap_servers=['localhost:9092'],  # Kafka server address
    auto_offset_reset='latest',  # Start reading at earliest available message
    enable_auto_commit=True,  # Auto-commit offsets
    group_id='train_data_group',  # Consumer group ID
    value_deserializer=lambda x: loads(x.decode('utf-8'))  # Deserialize JSON message
)

# Batch size for insert_many
BATCH_SIZE = 100  # Adjust the batch size based on your needs
buffer = []

# Helper function to insert a batch of data into MongoDB using insert_many
def insert_many_to_mongodb(data_batch):
    try:
        if data_batch:
            # Insert the batch of data into MongoDB
            collection.insert_many(data_batch)
            print(f"Inserted {len(data_batch)} records into MongoDB")
    except Exception as e:
        print(f"Failed to insert data into MongoDB: {e}")

# Consume messages from Kafka in a batch and insert into MongoDB
for message in consumer:
    try:
        raw_message = message.value  # Get raw message value

        if raw_message['updated_time'] == "Updated few seconds ago":
            raw_message['updated_time'] = datetime.now()
        else:
            raw_message['updated_time'] = datetime.strptime(raw_message['updated_time'], "%Y-%m-%d %H:%M:%S.%f")
        # print(type(raw_message['updated_time']),raw_message['updated_time'])
        
        
        # Convert single quotes to double quotes to make it a valid JSON
        data_string = raw_message['data'].replace("'", '"')
        data_string = re.sub(r'\bFalse\b', 'false', data_string)
        data_string = re.sub(r'\bTrue\b', 'true', data_string)

        # print(data_string)
        # Parse the string into a list of dictionaries
        data_list = json.loads(data_string)       
        
        # print(data_list[0])

        for i in range(len(data_list)):
            try:
                val = find_station_match_curr_data(data_list[i]['station_name'])['Final_Region'].values[0]

                if val == 'South Eastern Railway': raw_message['South_Eastern_Railway']=1
                if val == 'Eastern Railway': raw_message['Eastern_Railway']=1
                if val == 'North Frontier Railway': raw_message['North_Frontier_Railway']=1
                if val == 'Northern Railway': raw_message['Northern_Railway']=1
                if val == 'North Western Railway': raw_message['North_Western_Railway']=1
                if val == 'Southern Railway': raw_message['Southern_Railway']=1
                if val == 'Central Railway': raw_message['Central_Railway']=1
                if val == 'North Central Railway': raw_message['North_Central_Railway']=1
                if val == 'Western Railway': raw_message['Western_Railway']=1
                if val == 'South Central Railway': raw_message['South_Central_Railway']=1
                if val == 'North Eastern Railway': raw_message['North_Eastern_Railway']=1
                if val == 'South East Central Railway': raw_message['South_East_Central_Railway']=1
                if val == 'South Western Railway': raw_message['South_Western_Railway']=1
                if val == 'West Central Railway': raw_message['West_Central_Railway']=1
                if val == 'East Coast Railway': raw_message['East_Coast_Railway']=1
                if val == 'Konkan Railway': raw_message['Konkan_Railway']=1
                if val == 'East Central Railway': raw_message['East_Central_Railway']=1
            except:
                pass

        # print(f"Received raw message: {raw_message}")
        
        # Try to deserialize the JSON message
        # message_data = loads(raw_message)
        # print(f"Deserialized message from Kafka: {message_data}")
        # print(f"Deserialized message from Kafka: {raw_message}")
        
        # Add the message to the buffer
        # buffer.append(message_data)
        buffer.append(raw_message)
        print(len(buffer))
        # If the buffer reaches the batch size, insert the batch into MongoDB
        if len(buffer) >= BATCH_SIZE:
            insert_many_to_mongodb(buffer)
            buffer.clear()  # Clear the buffer after inserting
        
    except JSONDecodeError as e:
        # Log and handle invalid JSON message
        print(f"JSON decoding failed for message: {raw_message}. Error: {e}")
    
    except Exception as e:
        # Log any other exceptions that may occur
        print(f"An error occurred: {e}")

# After consuming all messages, insert any remaining data in the buffer
if buffer:
    insert_many_to_mongodb(buffer)
