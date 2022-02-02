#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 15:55:07 2022

@author: phykc
"""
import pandas as pd
import glob
import os
import datetime
import matplotlib.pyplot as plt
import numpy as np

class Summerisetemp:
    def __init__(self):
        self.filelist=[]
        self.timenow=datetime.datetime.now()
        self.yesterday=self.timenow-datetime.timedelta(days=1)
        self.cwd=os.getcwd()
        self.dflist=[]
        self.finddayfiles()
        
    def finddayfiles(self):
        self.path='/home/pi/Temp_log/'
        csv_files = glob.glob(self.path+'*.csv')
        if len(csv_files)>0:
            for file in csv_files:
                name=str(self.yesterday)
                alldayname=name.replace('/','-')
                dayname=alldayname[:10]
                if dayname in file:
                    self.filelist.append(file)
           
    def collectdayfile(self):
        for file in self.filelist:
            self.dflist.append(pd.read_csv(file))
            self.daydf=pd.concat(self.dflist)
            
    def plotday(self):
        if len(self.filelist)>0:
            self.collectdayfile()
            self.daydf['hours']=self.daydf['time']/60
            fig, ax1=plt.subplots(2)
            color = 'tab:red'
            ax1[0].set_xlim(0,24)
            ax1[0].scatter(self.daydf['hours'],self.daydf['temp'], color=color,marker='.')
            ax1[0].set_xlabel('time')
            ax1[0].set_ylabel('Aga Temp C', color=color)
            ax1[0].tick_params(axis='y', labelcolor=color)
            ax2 = ax1[0].twinx()
            color = 'tab:blue'
            ax2.scatter(self.daydf['hours'],self.daydf['humidity'], color=color,marker='.')
            ax2.set_ylabel('Humidity %', color=color)
            ax2.set_ylim(20,80)
            ax2.tick_params(axis='y', labelcolor=color)
            ax1[1].set_xlim(0,24)
            ax1[1].set_ylabel('Ambient Temp C', color=color)
            ax1[1].set_xlabel('Time')
            ax1[1].scatter(self.daydf['hours'],self.daydf['ambient'], color=color,marker='.')
            
            fig.tight_layout()
            fig.savefig('/home/pi/Temp_log/summaryplot.png')
            plt.close()
            
     
    
if __name__=='__main__':
    s=Summerisetemp()
    s.finddayfiles()
    s.plotday()
    
            
        
                
            
            
    
    

