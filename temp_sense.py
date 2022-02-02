import glob
import time
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import base64
import http.client, urllib
import daysummary
import json
import dht11mon
import numpy as np
from scipy import signal

class Message:
    def __init__(self,deviceID,k, m,t,i,s,v,a0='',a='0',p='', pr='-2'):
        self.k=k
        self.m=m
        self.t=t
        self.i=i
        self.s=s
        self.v=v
        self.p=p
        self.a=a
        self.a0=a0
        self.pr=pr
        self.conn = http.client.HTTPSConnection("pushsafer.com:443")
        self.deviceID=deviceID
    def send(self):    
        self.conn.request("POST", "/api",
          urllib.parse.urlencode({
            "k": self.k,                # <Your Private> or Alias Key
            "m": self.m,                   # Message Text
            "t": self.t,                     # Title of message
            "i": self.i,                      # Icon number 1-98
            "s": self.s,                     # Sound number 0-28
            "v": self.v,                 # Vibration number 0-3
            "p": self.p,                   # Picture Data URL with Base64-encoded string
            "a": self.a,                  #Answer possible
            "a0":self.a0,                 #Answer options
          }), { "Content-type": "application/x-www-form-urlencoded" })
        self.response = self.conn.getresponse()

        print(self.response.status, self.response.reason)
        data = self.response.read()
        
        data1=json.loads(data)
        print(data1)
        noleft=data1['available']
        print('There are ',noleft,'messages left')
    def read(self):
        try:
            self.conn.request("GET","/api-m?k="+ self.k+"&d="+self.deviceID)
            self.responser = self.conn.getresponse()
            data = self.responser.read()
            answer=json.loads(data)
            df = pd.DataFrame(answer)
            length=(len(df))
            lastdat=df.iloc[length-1,1]
            answer=lastdat['answer']
            return answer
        except:
            print('Read answer error')
            blank=''
            return blank

class DS18B20:
    """Read the temperature from the DS18B20"""
    def __init__(self):
        self.device_file = glob.glob("/sys/bus/w1/devices/28*")[0] + "/w1_slave"
        print (self.device_file)

    def read_temp_raw(self):
        try:
            self.device_file = glob.glob("/sys/bus/w1/devices/28*")[0] + "/w1_slave"
            f = open(self.device_file, "r")
            lines = f.readlines()
            f.close()
            return lines
        except:
            print('Error opening device')
            return []

    def crc_check(self, lines):
        try:
            chek=lines[0].strip()[-3:] == "YES"
            return chek
        except:
            print('Device Read error')
            return False
    
    def read_temp(self):
        temp_c = -255
        attempts = 0

        lines = self.read_temp_raw()
        success = self.crc_check(lines)

        while not success and attempts < 5:
            time.sleep(.2)
            lines = self.read_temp_raw()
            success = self.crc_check(lines)
            attempts += 1

        if success:
            temp_line = lines[1]
            equal_pos = temp_line.find("t=")
            if equal_pos != -1:
                temp_string = temp_line[equal_pos+2:]
                temp_c = float(temp_string)/1000.0

        return temp_c

class Monitor:
    """ Monitor the temperature"""
    def __init__(self, morning=7, evening=22, mint=59, waittime=3, threshold=50, interval_time=58, agawait_off=300, error_sleep=300, summarytime=10):
        self.waittime=waittime
        self.morning=morning
        self.mint=mint
        self.evening=evening
        self.threshold=threshold
        self.interval_time=interval_time
        self.agawait_off=agawait_off
        self.errorsleep=error_sleep
        self.summarytime=summarytime
        self.temp_list=[]
        self.time_list=[]
        self.humidity_list=[]
        self.ambient_list=[]
        self.improving=False
        self.d_h=dht11mon.Temphum()
        self.sensor=DS18B20()
        
    def aga_off(self):
        message_on=True
        while self.T<self.threshold and self.improving==False:
            if message_on:
                messaltert=Message(k="<Your Private>",deviceID='<ID>',m='Aga Temp is '+str(self.T)[:4]+'change the threshold by answering with an integer or stop or start',t='Aga out?', i='2',s='20',v='3',p='', pr='2',a='1')
                messaltert.send()
            time.sleep(self.agawait_off)
            answer=messaltert.read()
            if answer.isnumeric():
                self.threshold=int(answer)
            if answer=='stop':
                message_on=False
            if answer=='start':
                message_on=True
                
            self.T=self.sensor.read_temp()
            self.ambient, self.humidity=self.d_h.read()
            self.timenow=datetime.datetime.now()
            if len(self.temp_list)>1:
                if self.T>=self.temp_list[-1] and message_on:
                    messaltert=Message(k="<Your Private>",deviceID='<ID>',m='Aga Temp is '+str(self.T)[:4],t='Warming up', i='1',s='0',v='0',p='', pr='2',a='1')
                    messaltert.send()
                    self.improving=True 
                else:
                    self.improving=False
            self.temp_list.append(self.T)
            self.time_list.append(self.timenow.hour*60+self.timenow.minute)
            
            self.humidity_list.append(self.humidity)
            self.ambient_list.append(self.ambient)
            print(self.T, ' aga out?')
            
    def createdataplot(self):
        meanT=sum(self.temp_list)/len(self.temp_list)
        humdata=np.array(self.humidity_list)
        humiditysm=signal.savgol_filter(humdata, 8, 3)
        mean_humidity=humiditysm.mean()
        self.humidity_list=humiditysm.tolist()
        data={'time':self.time_list,'temp':self.temp_list, 'humidity':self.humidity_list, 'ambient':self.ambient_list}
        df=pd.DataFrame(data=data)
        filename=str(self.dtime)
        file=filename.replace('/','-')
        df.to_csv('Temp_log/temp-'+file[:-7]+'.csv')
        fig, ax1=plt.subplots()
        color = 'tab:red'
        ax1.plot(df['time'],df['temp'], color=color)
        ax1.set_xlabel('time (min)')
        ax1.set_ylabel('Aga Temp', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        ax2 = ax1.twinx()
        color = 'tab:blue'
        ax2.plot(df['time'],df['humidity'], color=color)
        ax2.set_ylabel('Humidity %', color=color)
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim(20,80)
        fig.tight_layout()
        fig.savefig("Temp_log/plot.png")
        plt.close()
        time.sleep(2)
        del df
        
        if self.dtime.hour>self.morning and self.dtime.hour<self.evening:
            file1="Temp_log/plot.png"
            self.pic_string=self.image_encode(file1)
            mess=Message(k="<Your Private>",deviceID='<ID>',m='Update',t='The mean temperature is '+str(meanT)[:4]+' and the mean humidity is '+str(mean_humidity)[:2], i='1',s='0',v='0',p=self.pic_string, a='1')
            mess.send()
            self.time_list=[]
            self.temp_list=[]
            self.humidity_list=[]
            self.ambient_list=[]
    
    def image_encode(self,file):
        self.encoded = base64.b64encode(open(file, "rb").read())
        pic_string= "data:image/png;base64,"+str(self.encoded)[2:]
        return pic_string
    
    def summary_day(self):
        sot=daysummary.Summerisetemp()
        sot.plotday()
        time.sleep(1)
        file2="Temp_log/summaryplot.png"
        self.pic_string=self.image_encode(file2)
        mess1=Message(k="<Your Private>",deviceID='<ID>',m='Summary',t="Yesterday's Aga Temperature Summary", i='1',s='0',v='0',p=self.pic_string)
        mess1.send()
            
    def measure(self):
        self.dtime=datetime.datetime.now()
        hour=int(self.dtime.hour)+1
        if  self.dtime.minute==self.mint and hour%self.waittime==0 and len(self.temp_list)>0:
            print('send message')
            self.createdataplot()
        if self.dtime.minute==self.mint and  self.dtime.hour==self.summarytime-1:
            self.summary_day() 
        self.T=self.sensor.read_temp()
        self.temp_list.append(self.T)
        self.time_list.append(self.dtime.hour*60+self.dtime.minute)
        self.ambient, self.humidity=self.d_h.read()
        self.humidity_list.append(self.humidity)
        self.ambient_list.append(self.ambient)
        if len(self.temp_list)>2:
            if self.T<=self.temp_list[-3]:
                self.improving=False
            else:
                self.improving=True
        else:
            self.improving=True
        if self.T<self.threshold and self.improving==False:
            self.aga_off()
        print('T= ',self.T)
        time.sleep(self.interval_time)
                
    
if __name__ == "__main__":
    inmess=Message(k="<Your Private>",deviceID='<ID>',m='The code started',t='Test', i='1',s='0',v='0', a='1')
    inmess.send()
    
    mon_temp=Monitor(waittime=3,summarytime=8)
    while True:
        mon_temp.measure()
        minute=int(mon_temp.dtime.minute)
        if minute%15==0:
            answer=inmess.read()
            if answer.isnumeric():
                mon_temp.threshold=int(answer)
