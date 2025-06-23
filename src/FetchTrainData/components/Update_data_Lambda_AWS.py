import time
from datetime import datetime, timedelta, time

class UpdateData:
    def __init__(self,resp_dict: dict):
        self.success:bool = resp_dict["success"]
        self.train_name:str = resp_dict["train_name"].split("Running Status")[0]
        self.message:str = resp_dict["message"]
        self.updated_time:str = resp_dict["updated_time"]
        self.data:str = resp_dict["data"]

    def extract_train_num(self):
        return self.train_name[0:4]
    
    def abs_update_time(self):
        if self.updated_time != "Updated few seconds ago":
            updated_time = self.updated_time
            update_hr_ago = 0
            if len(updated_time.split("hr"))==1:
                update_min_ago = update_hr_ago + int(updated_time.split("min")[0].split(" ")[1])
            else:
                update_hr_ago = int(updated_time.split("hr")[0].split(" ")[1])
                update_min_ago = int(updated_time.split("hr")[1].split("min")[0])            
            current_time = datetime.now()
            time_difference = timedelta(hours=update_hr_ago, minutes=update_min_ago)
            new_time = current_time - time_difference
            self.updated_time = new_time

    def train_visit_status(self):
        if self.message == "":
            for station in self.data:
                station["Crossed Station"] = "No"
        else:
            ind = 0
            for station in reversed(self.data):
                if(self.message.find(station["station_name"]))>=0:
                    ind=1
                if ind==0:
                    station["Crossed Station"] = "No"
                elif ind==1:
                    station["Crossed Station"] = "Yes"
    
    def train_visit_datetime(self):
        current_time = datetime.now().time()
        current_date = datetime(year=datetime.now().year,month=datetime.now().month,day=datetime.now().day)
        ind=0
        for station in range(len(self.data)-1):
            try:
                time_str = self.data[station]["timing"][0:5]
                k = time(int(time_str.split(":")[0]), int(time_str.split(":")[1]))
                self.data[station]["leaving_time"] = k
                # print(leaving_time)
            except:
                self.data[station]["leaving_time"] = k+timedelta(hours=0, minutes=40)
                pass

            if self.data[station]["Crossed Station"]=="Yes":
                ind=ind+1

        for i in reversed(range(ind)):
            if current_time>=self.data[i]["leaving_time"]:
                self.data[i]["date"] = current_date
                current_time = self.data[i]["leaving_time"]
                current_date = self.data[i]["date"]
            else:
                self.data[i]["date"] = current_date-timedelta(days=1)
                current_time = self.data[i]["leaving_time"]
                current_date = self.data[i]["date"]

        current_time = datetime.now().time()
        current_date = datetime(year=datetime.now().year,month=datetime.now().month,day=datetime.now().day)

        for i in range(ind,len(self.data)-1):
            if current_time<self.data[i]["leaving_time"]:
                self.data[i]["date"] = current_date
                current_time = self.data[i]["leaving_time"]
                current_date = self.data[i]["date"]
            else:
                self.data[i]["date"] = current_date+timedelta(days=1)
                current_time = self.data[i]["leaving_time"]
                current_date = self.data[i]["date"]

        # Data.data[-2]
        dist = int(self.data[-2]["distance"].split(" ")[0])
        dist_fin = int(self.data[-1]["distance"].split(" ")[0])
        dt1=self.data[-2]["date"]
        dt2=self.data[0]["date"]
        tim1 = self.data[-2]["leaving_time"]
        tim2 = self.data[0]["leaving_time"]
        duration = datetime.combine(dt1, tim1) - datetime.combine(dt2, tim2)
        speed = dist/duration.seconds
        delta = timedelta(seconds=(dist_fin-dist)/speed)
        self.data[-1]["leaving_time"] = time(hour=(datetime.combine(dt1, tim1)+delta).hour, minute=(datetime.combine(dt1, tim1)+delta).minute)
        if self.data[-1]["leaving_time"]>self.data[-2]["leaving_time"]:
            self.data[-1]["date"] = self.data[-2]["date"]
            # Data.data[-1]["date"] = datetime.combine(dt1, time=time(hour=0,second=0))+delta
        else:
            delta = timedelta(day=1)
            self.data[-1]["date"] = datetime.combine(dt1, time=time(hour=0,second=0))+delta
        # Data.data[-1]["leaving_time"] = Data.data[-1]["date"]+delta
        for station in self.data:
            station["leaving_time"] = str(station["leaving_time"])
            station["date"] = str(station["date"])

    def train_running_status(self):
        ind=0
        for station in self.data:
            if station["Crossed Station"]=="Yes":
                ind=1

        if ind==1:
            self.running_status = "Yes"
        else:
            self.running_status = "No"

    def train_running_zone_flags(self):
        self.South_Eastern_Railway = 0
        self.Eastern_Railway = 0
        self.North_Frontier_Railway = 0
        self.Northern_Railway = 0
        self.North_Western_Railway = 0
        self.Southern_Railway = 0
        self.Central_Railway = 0
        self.North_Central_Railway = 0
        self.Western_Railway = 0
        self.South_Central_Railway = 0
        self.North_Eastern_Railway = 0
        self.South_East_Central_Railway = 0
        self.South_Western_Railway = 0
        self.West_Central_Railway = 0
        self.East_Coast_Railway = 0
        self.Konkan_Railway = 0
        self.East_Central_Railway = 0
        for station in self.data:
            # print(self.find_station_match_curr_data(station['station_name'])['Final_Region'].values[0])
            try:
                val = self.find_station_match_curr_data(station['station_name'])['Final_Region'].values[0]

                if val == 'South Eastern Railway': self.South_Eastern_Railway=1
                if val == 'Eastern Railway': self.Eastern_Railway=1
                if val == 'North Frontier Railway': self.North_Frontier_Railway=1
                if val == 'Northern Railway': self.Northern_Railway=1
                if val == 'North Western Railway': self.North_Western_Railway=1
                if val == 'Southern Railway': self.Southern_Railway=1
                if val == 'Central Railway': self.Central_Railway=1
                if val == 'North Central Railway': self.North_Central_Railway=1
                if val == 'Western Railway': self.Western_Railway=1
                if val == 'South Central Railway': self.South_Central_Railway=1
                if val == 'North Eastern Railway': self.North_Eastern_Railway=1
                if val == 'South East Central Railway': self.South_East_Central_Railway=1
                if val == 'South Western Railway': self.South_Western_Railway=1
                if val == 'West Central Railway': self.West_Central_Railway=1
                if val == 'East Coast Railway': self.East_Coast_Railway=1
                if val == 'Konkan Railway': self.Konkan_Railway=1
                if val == 'East Central Railway': self.East_Central_Railway=1

            except:
                pass

