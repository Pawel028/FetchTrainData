from datetime import datetime, timedelta, time
import aioboto3.session
from pymongo import MongoClient
import pandas as pd
import os
import dotenv
from src.FetchTrainData.utils.common import read_yaml, create_directories,save_json
from src.FetchTrainData.components import RailData, GetTrainList
from pathlib import Path
import asyncio
import time
import boto3
import json
dotenv.load_dotenv()
from time import sleep
from json import dumps
from kafka import KafkaProducer
import aioboto3

topic_name='hello_world'
producer = KafkaProducer(bootstrap_servers=['localhost:9092'],value_serializer=lambda x: json.dumps(x).encode('utf-8'))

# Initialize a session using Amazon Lambda
aws_access_key_id_var = os.getenv("aws_access_key_id")
aws_secret_access_key_var = os.getenv("aws_secret_access_key")



# async def invoke_lambda(payload):
#     session = aioboto3.Session()
#     async with session.client('lambda', 
#                                aws_access_key_id=aws_access_key_id_var,
#                                aws_secret_access_key=aws_secret_access_key_var,
#                                region_name='ap-south-1') as client:
#         try:
#             # Invoke Lambda asynchronously
#             response = await client.invoke(
#                 FunctionName='ReformatData',  # Name of your Lambda function
#                 InvocationType='RequestResponse',  # Synchronous invocation
#                 Payload=json.dumps(payload)  # Convert Python dict to JSON
#             )
#             async with response['Payload'] as stream:
#                 response_payload = await stream.read()
#             # Read and process the Lambda response
#             response_payload = json.loads(response_payload)

#             return response_payload

#         except Exception as e:
#             print(f"Error invoking Lambda function: {e}")
#             return None


def invoke_lambda(payload):
    # Ensure the payload is a dictionary; convert if necessary
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary.")
    
    try:
        # Initialize boto3 Lambda client
        client = boto3.client('lambda', 
                              aws_access_key_id=aws_access_key_id_var,
                              aws_secret_access_key=aws_secret_access_key_var,
                              region_name='ap-south-1')
        
        # Invoke Lambda synchronously
        response = client.invoke(
            FunctionName='ReformatData',  # Name of your Lambda function
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps(payload)  # Convert Python dict to JSON
        )
        
        # Read and process the Lambda response
        response_payload = response['Payload'].read()

        # Check if response_payload is empty or valid JSON
        if response_payload:
            try:
                response_payload = json.loads(response_payload)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response: {e}")
                return None
        else:
            print("Empty response from Lambda.")
            return None

        return response_payload

    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None


async def store_data(train_no, collection):
    start_time1 = time.time()
    train1 = str(train_no).rjust(5, "0")
    dict = RailData(train_num=train1)
    dict1 = dict.get_data_obj.get_reponse()

    time_for_rail_api = time.time() - start_time1

    # print("train num is: " + train1 + dict["message"])
    try:
        if dict1 is not None and dict1['message'] != "":
            # Call invoke_lambda asynchronously
            # dict2 = await invoke_lambda(dict1)
            dict2 = invoke_lambda(dict1)
            try:
                producer.send(topic_name, value=dict2)
                producer.flush()  # Ensure the message is sent immediately
                print(f"Data sent to Kafka for train: {train_no}")
            except Exception as e:
                print(f"Failed to send message to Kafka: {e}")

            # Optional: Store data in MongoDB
            # try:
            #     collection.insert_one(dict2)
            #     print(f"Data inserted to MongoDB for train: {train_no}")
            # except Exception as e:
            #     print(f"Failed to insert data into MongoDB: {e}")
    except:
        pass

        
async def loop_run():
    config = read_yaml(Path("config/config.yaml"))
    train_list_obj = GetTrainList(config.Train_list.Train_list_file)
    # print(train_list["Train_num"])
    train_list_obj.get_train_list()
    string = train_list_obj.mongo_string
    
    client = MongoClient(string)  # Use your MongoDB connection string
    db = client['train_data']  # Database name
    collection = db['train_status_1']    
    task = (store_data(train,collection) for train in train_list_obj.train_list[2000:3000])
    results = await asyncio.gather(*task)



if __name__ == "__main__":
    while 1<2:
    
        start_time = time.time()
        # asyncio.run(loop_run())
        try:        
            asyncio.run(loop_run())
        except:
            pass
        print(time.time()-start_time)
        # sleep(5)




            


        



            


    
    
