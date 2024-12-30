from datetime import datetime, timedelta, time
from pymongo import MongoClient
import pandas as pd
import os
import dotenv
from src.FetchTrainData.utils.common import read_yaml, create_directories,save_json
from src.FetchTrainData.components import RailData, GetTrainList
from pathlib import Path
import asyncio
import time

async def store_data(train_no,string):
    train1 = str(train_no).rjust(5, "0")
    dict = RailData(train_num=train1)
    dict1 = dict.get_data_obj.get_reponse()
    # print("train num is: "+train1+dict["message"])
    # print("Train_Number is:"+train1+" and message is: "+dict['message'])
    if dict1['message']!="":
        # dict = RailData(train_num=train1).ReFormatData()

        dict2 = dict.ReFormatData()


        # print(dict)
        # MongoDB connection
        client = MongoClient(string)  # Use your MongoDB connection string
        db = client['train_data']  # Database name
        collection = db['train_status']
        collection.insert_one(dict2)
        print("Train_Number is:"+train1+" and message is: "+dict2['message'] + " and data uploaded to Mongodb")
        # type(dict)
        
async def loop_run():
    config = read_yaml(Path("config/config.yaml"))
    train_list_obj = GetTrainList(config.Train_list.Train_list_file)
    # print(train_list["Train_num"])
    train_list_obj.get_train_list()
    string = train_list_obj.mongo_string
    task = [store_data(train,string) for train in train_list_obj.train_list]  


    results = await asyncio.gather(*task)



if __name__ == "__main__":
    try:
        start_time = time.time()
        asyncio.run(loop_run())
    except:
        pass

    print(time.time()-start_time)



            


        



            


    
    
