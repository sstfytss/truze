# visualization.py
# Truze.AI
#
# Created by Shun Sakai and Joseph Fernando on April 15, 2023
# Copyright © 2023 Shun Sakai. All rights reserved.
#
# THE CONTENTS OF THIS PROJECT ARE PROPRIETARY AND CONFIDENTIAL.
# UNAUTHORIZED COPYING, TRANSFERRING OR REPRODUCTION OF THE CONTENTS OF THIS PROJECT, VIA ANY MEDIUM IS STRICTLY PROHIBITED.

from multiprocessing.sharedctypes import Value
from operator import index
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.figure_factory as ff
import math
import dash

nan1 = "NaN" # constant for NaN
nan2 = "nan" # constant for nan
period = "." # period to denote float

def stats(data, selected):
    colNum = list() # empty list to store values in column without nans
    row = data[selected].astype(str).values.tolist() # add values in column selected to list
    anyWords = False
    none = 'None'
 
    # store values in column without nans
    for i in row:
        if nan2 not in i:
            if is_num(i):
                i = float(i)

                if i.is_integer():
                    colNum.append(int(i))
                else:
                    colNum.append(i)
            else:
                colNum.append(i)

    coldf = pd.DataFrame(colNum, columns=['value']) # pandas dataframe for the column
    anyWords = any(isinstance(s, str) for s in colNum if s != none) # check if everything is a string

    # don't calculate stats if everything is a string
    if anyWords:
        notAvailable = 'N/A'
        stats = {
            'mean' : notAvailable,
            'median': notAvailable,
            'mode' : notAvailable,
            'min' : notAvailable,
            'max' : notAvailable,
            'std' : notAvailable,
            'q1' : notAvailable,
            'q2' : notAvailable,
            'q3' : notAvailable,
            'range' : notAvailable
        }
    else:
        stats = {
            'mean' : round(coldf['value'].mean(), 2),
            'median': round(coldf['value'].median(), 2),
            'mode' : round(coldf['value'].mode(), 2),
            'min' : round(coldf['value'].min(), 2),
            'max' : round(coldf['value'].max(), 2),
            'std' : round(coldf['value'].std(), 2),
            'q1' : round(coldf['value'].quantile(0.25), 2),
            'q2' : round(coldf['value'].quantile(0.50), 2),
            'q3' : round(coldf['value'].quantile(0.75), 2),
            'range' : '{b1} - {b2}'.format(b1= coldf['value'].min(), b2=coldf['value'].max())
        }

    return stats

def box(data, selected):
    colNum = list() # empty list to store values in column without nans
    row = data[selected].astype(str).values.tolist() # add values in column selected to list
    anyWords = False # check if the list has strings
    none = 'None' # constant for none
    invalid = 'N/A'

    # store values in column without nans
    for i in row:
        if nan2 not in i:
            if is_num(i):
                i = float(i)
                if i.is_integer():
                    colNum.append(int(i))
                else:
                    colNum.append(i)
            else:
                colNum.append(i)

    anyWords = any(isinstance(s, str) for s in colNum if s != none) # check if everything is a string
    coldf = pd.DataFrame(colNum, columns=['value']) # pandas dataframe for the column

    # if there are strings that aren't none, don't show boxplot
    if anyWords:
        return invalid
    
    else:
        # create histogram and plot
        fig = px.box(coldf, x = 'value')
        fig.update_layout(title= 'Box Plot', xaxis_title= selected)
        fig.update_layout(
            margin=dict(l=20, r=10, t=60, b=30),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig

def hist(data, selected, curve):
    row = [] # empty list to store values in column
    lis = [] # empty list to store non-duplicate values in column
    colNum = [] # empty list to store values in column without nans
    dic = {} # empty dict to store value and count lists
    nanCount = 0 # number of nans
    yesNo = False # check if the list is binary
    anyWords = False # check if the list has strings
    none = 'None' # constant for none
    row = data[selected].astype(str).values.tolist() # add values in column selected to list#returnList(col)

    # create a dictionary with frequency count
    for i in row:
        if nan2 not in i:
            if is_num(i): # the value is a number
                i = float(i)
                if i.is_integer():
                    dic[int(i)] = dic.get(int(i), 0) + 1
                else:
                    dic[float(i)] = dic.get(float(i), 0) + 1
            else: # the value is only a string
                dic[i] = dic.get(i, 0) + 1  
        else:  
            dic[-1] = dic.get(-1, 0) + 1
            nanCount = dic[-1]

    # lis of unique values in column
    valueSet = set(row)

    # add unique values to lis
    for i in valueSet:
        if nan2 not in i:
            if is_num(i):
                i = float(i)
                if i.is_integer():
                    lis.append(int(i))
                else:
                    lis.append(float(i))
            else:
                lis.append(i)

    coldf = pd.DataFrame(dic.items(), columns=['key', 'value']) # pandas dataframe for the column
    anyWords = any(isinstance(s, str) for s in lis if s != none) # check if everything is a string
    if anyWords: lis = map(str, lis) # if any strings are present, map the entire list to a list of strings
    yesNo = True if max(row) == 1 or 'y' in row or len(valueSet) <= 3 or 'False' in valueSet or anyWords == True else False # check if values are yes no
    
    # create histogram and plot
    fig = px.bar(coldf, x = 'key', y = 'value')
    fig.update_xaxes(type='category', categoryorder='array', categoryarray= sorted(lis))
    fig.update_layout(xaxis_title= selected, xaxis=dict(rangeslider=dict(visible=True),
                             type="linear"), yaxis_title='frequency', title= 'Histogram', showlegend= False)
    fig.update_layout(
        margin=dict(l=20, r=10, t=60, b=30),
        paper_bgcolor='rgba(0,0,0,0)',

    )
    
    # choosing the graph to display
    if yesNo:
        graph = fig
    else: # create normal curve for data if possible
        # store values in column without nans
        for i in row:
            if nan2 not in i:
                if is_num(i):
                    i = float(i)
                    if i.is_integer():
                        colNum.append(int(i))
                    else:
                        colNum.append(float(i))
                else:
                    colNum.append(i)

        s= pd.DataFrame(colNum, columns=['value']) # pandas dataframe for the column
        group_labels = [selected] # title of data
        colors = ['#F66095'] # color of plot
        fig2 = ff.create_distplot([s['value']], group_labels, colors = colors, curve_type= curve, show_rug = False)
        fig2.update_layout(title_text='Histogram with Curve', xaxis_title = selected, yaxis_title = 'Probability Density', xaxis=dict(rangeslider=dict(visible=True),
                             type="linear"), showlegend= False)
        fig2.update_layout(
            margin=dict(l=20, r=10, t=60, b=30),
            paper_bgcolor='rgba(0,0,0,0)',
        )
        graph = fig2
        
    return graph

def is_num(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return True


'''
if __name__ == '__main__':
    column = input('Which column number would you like to plot: ')
    curve = input('What kind of curve would you like to display on your histogram? [kde or normal]: ')
    setup()
    hist(column, curve)
    box(column)
    stats(column)
'''