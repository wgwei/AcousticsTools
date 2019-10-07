# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 10:36:52 2019
input CSV file format: 
    first row: type, date, values etc
@author: W.Wei
"""

import pandas as pd
import math

def load_survey(fileName, repeat=2):
    surveyData = pd.read_csv(fileName)
    dataRowNo = surveyData.shape[0]
    steps = math.floor(dataRowNo / repeat)
    t = [n*steps for n in range(repeat)] # [0, steps, steps*2, ..]
    tt = t + [dataRowNo]
    newData = [surveyData.iloc[tt[i]:tt[i+1]] for i in range(len(t))] # this is list of DataFrame
    
    outData = []
    for nd in newData:
        outData.append(nd.reset_index())
        print("\n xxxxx \n")
        print(nd.head())
        print(nd.index)
        
    newCSV = pd.concat(outData, axis=1, sort=False)
    newCSV.to_csv("reshaped.csv",index=False)

if __name__ =="__main__":
    load_survey(r"data\survey-example.csv", 2)
