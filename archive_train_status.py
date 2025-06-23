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
from datetime import datetime, timedelta
from time import sleep
import boto3
from botocore.exceptions import NoCredentialsError
dotenv.load_dotenv()
config = read_yaml(Path("config/config.yaml"))
string = os.getenv('mongodb_string')
client = MongoClient(string) 
# print(string)
db = client['train_data']  # Database name
collection = db['train_status_2']  # Collection name
aws_access_key_id_var = os.getenv("aws_access_key_id")
aws_secret_access_key_var = os.getenv("aws_secret_access_key")
# s3 = boto3.client('s3')

client = boto3.client('s3',aws_access_key_id=aws_access_key_id_var,aws_secret_access_key=aws_secret_access_key_var,region_name='ap-south-1')

# Load environment variables (for MongoDB connection string)
def Archive_Train_Status():
    five_hours_ago = datetime.now() - timedelta(hours=3)
    query = {'updated_time': {'$lt': five_hours_ago}}
    result = pd.DataFrame(collection.find(query))
    
    # result = collection.delete_many(query)
    # result=pd.DataFrame(result)
    time_now = datetime.now()
    fname = "DataStored_"+str(time_now.year)+"_"+str(time_now.month).zfill(2)+"_"+str(time_now.day).zfill(2)+"_"+str(time_now.hour).zfill(2)+"_"+str(time_now.minute).zfill(2)+".csv"
    result.to_csv(fname)    
    client.upload_file(fname,'trainprojectpawel', fname)
    os.remove(fname)
    collection.delete_many(query)

if __name__ == "__main__":
    while 1<2:
        Archive_Train_Status()
        sleep(10000)