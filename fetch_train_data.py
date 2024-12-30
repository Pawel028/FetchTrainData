import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
# URL of the Indian Railways website with running train statuses
URL = "https://www.railyatri.in/live-train-status"  # Replace with the actual running status page URL

train_list = ['09154', '20907', '05054']
# Function to fetch train running status
def get_train_status(train_num):
    URL = "https://rappid.in/apis/train.php?train_no="+train_num
    response = requests.get(URL)
    return response.text