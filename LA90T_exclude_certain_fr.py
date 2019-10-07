#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  6 20:52:13 2019
@author: wg
"""

import datetime
import pandas as pd
import numpy as np
import os
    
def find_measure_startLine(filename):
    with open(filename, 'r') as fin:
        n = 0
        while True:
            line = fin.readline()
            if n<24:        
                print(line)
            n += 1
            if not line:
                break
            else:
                if ('# RTA LOG Results LAeq_dt' in line) :
                    print('Measurmeent starts from ' + str(n) + ' th line')
                    break  # next line starts. break
    return n

def data_2_dataFrame(filename, startLineNumber):
    with open(filename,"r") as fin:
        allData = fin.readlines()
    surveyData = allData[startLineNumber::]
    surveyDataList = [surveyData[n].strip("\n").split("\t") for n in range(len(surveyData))]
    dataSet = []
    for dataLine in surveyDataList:
        dataSet.append([w.strip() for w in dataLine])
    print(dataSet[0:4])
    
    surveyDF = pd.DataFrame(dataSet[2::], columns = dataSet[0])
    print(surveyDF.columns)
    columnsToFloat = ['6.3', '8.0', '10.0', '12.5',
       '16.0', '20.0', '25.0', '31.5', '40.0', '50.0', '63.0', '80.0', '100.0',
       '125.0', '160.0', '200.0', '250.0', '315.0', '400.0', '500.0', '630.0',
       '800.0', '1000.0', '1250.0', '1600.0', '2000.0', '2500.0', '3150.0',
       '4000.0', '5000.0', '6300.0', '8000.0', '10000.0', '12500.0', '16000.0',
       '20000.0']
    for c in columnsToFloat:
        surveyDF[c] = surveyDF[c].astype(float)
    print(surveyDF.head())
    surveyDF2 = surveyDF.drop(columns=['40.0', '50.0', '100.0'])       
    columnsFreq = ['6.3', '8.0', '10.0', '12.5',
       '16.0', '20.0', '25.0', '31.5', '63.0', '80.0', 
       '125.0', '160.0', '200.0', '250.0', '315.0','400.0', '500.0', '630.0',
       '800.0', '1000.0', '1250.0', '1600.0', '2000.0', '2500.0', '3150.0',
       '4000.0', '5000.0', '6300.0', '8000.0', '10000.0', '12500.0', '16000.0',
       '20000.0']
    return [surveyDF2, columnsFreq]

def get_timeObj(dateIn="2019-08-19", timeIn="10:57:59"):
    dv = [int(d) for d in dateIn.split('-')]
    tv = [int(t) for t in timeIn.split(':')]
    timeStamp = datetime.datetime(dv[0], dv[1], dv[2], tv[0], tv[1], tv[2])
    return timeStamp

def calc_Laeq_dt(filename):
    n = find_measure_startLine(filename)
    [surveyDF2, columnsFreq] = data_2_dataFrame(filename,n)
    
    ENG=0
    for c in columnsFreq:
        ENG += 10**(surveyDF2[c]/10) 
    LAeq_dt = 10*np.log10(ENG)
    surveyDF2["LAeq_dt"] = LAeq_dt
    surveyDF2 = surveyDF2[["Date", "Time", "LAeq_dt"]]
    print(surveyDF2.head())
    return surveyDF2

def calc_LAeqT_from_spec(dataTframeInput, columnName="LAeq_dt"):
    return np.log10(np.mean(10.**(dataTframeInput[columnName]/10)))

    
def calc_Lx_T(sDF, duration = 900, resolution=1):
    ''' sDF: survey dataframe
        duration is the equivalent measurement time length T in seconds,
        resolution is the sampling rate, default is 1 measurement per second
    '''
    
    # find the start time stamp of a chunck of measurement duration
    dv = [int(d) for d in sDF["Date"][0].split('-')]
    tv = [int(t) for t in sDF["Time"][0].split(':')] 
    if duration == 900:
        minutes = [0, 15, 30, 45]
    elif duration == 3600:
        minutes = [0]
    else:
        assert False, "not defined !"
    second = 0
    timeObj = [datetime.datetime(dv[0], dv[1], dv[2],tv[0], m, second) for m in minutes] #same hour
    timeObj.append(datetime.datetime(dv[0], dv[1], dv[2],tv[0]+1, 0, 0)) # next hour
    
    start = get_timeObj(sDF["Date"][0], sDF["Time"][0])
    for tj in timeObj:
        difference = tj - start
        if difference.total_seconds() >=0:
            startTime = tj
            break
    
    # add time stamp column
    timeObjectList = [get_timeObj(sDF["Date"][i], sDF["Time"][i]) for i in range(sDF.shape[0])]
    sDF["DateTimeObject"] = timeObjectList
    print(sDF.head())
    sDF2 = sDF[["DateTimeObject", "LAeq_dt"]]
    
    # determine the total steps (chunk) of measurements
    lastTime = sDF2["DateTimeObject"].iloc[-1]
    measureDuration = lastTime - startTime
    steps = int(np.floor(measureDuration.total_seconds()/duration))
    
    # slice the data
    dateT = []
    LA90T = []
    LAeqT = []
    for s in range(steps):
        st = startTime + datetime.timedelta(seconds=duration*s)
        et = startTime + datetime.timedelta(seconds=duration*(s+1))
        tempDF = sDF2[(sDF2["DateTimeObject"]>=st) & (sDF2["DateTimeObject"]<et)]
        print (tempDF.head())
        tempDF2 = tempDF.sort_values("LAeq_dt")
        print (tempDF2.head())
        LA90T.append(tempDF2["LAeq_dt"].iloc[int(0.1*duration/resolution)]) # find LA90
        LAeqT.append(10*np.log10(np.mean(10.**(tempDF["LAeq_dt"]/10)))) # calc the LAeq,T
        dateT.append(st)
    LA90DF = pd.DataFrame.from_dict({"Time":dateT, "LAeqT":LAeqT, "LA90T":LA90T})
    print(LA90DF.head())
    
    # write to CSV
    LA90DF.to_csv("LAeqT-LA90T.csv")
    

def main():
    filename = os.path.join("data", "2019-09-13_SLM_000_RTA_3rd_Log.txt")
    DF2 = calc_Laeq_dt(filename)
    calc_Lx_T(DF2, duration = 900)


if __name__=="__main__":
    if 1:  
        main()    