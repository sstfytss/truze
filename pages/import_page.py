# import_page.py
# Truze.AI
#
# Created by Shun Sakai and Joseph Fernando on May 16, 2023
# Copyright © 2023 Shun Sakai. All rights reserved.
#
# THE CONTENTS OF THIS PROJECT ARE PROPRIETARY AND CONFIDENTIAL.
# UNAUTHORIZED COPYING, TRANSFERRING OR REPRODUCTION OF THE CONTENTS OF THIS PROJECT, VIA ANY MEDIUM IS STRICTLY PROHIBITED.

import base64
from http.client import NOT_IMPLEMENTED
import io
from operator import ge
import os
import random as rand

import zipfile
import tempfile

from dash import html, dcc, dash_table, no_update, ctx
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import pandas as pd
import numpy as np
import psycopg2
import hashlib

from app import app
from pages import configdb
from database.Table_Populator import populateTable
from database.Table_Creator import defineColumns
from database.SQLTest import editTable, findAndReplace, pushChanges, revertAllEdits, pullChanges, undoButton, revertColEdits, getIDTable, type_check, prev_check
from visualization import is_num

deleted_columns = []
deleted_rows = []
selected = ''

layout = html.Div([
    html.Div(children=[
        html.Div(id='top-right', children=[
            dbc.Button('Upload New Datset', href = '/new', id='new', style={'marginLeft': '8px', 'borderRadius': '25px', 'backgroundColor':'#0A2463', 'display' : 'none'}),
            dcc.Download(id='download1')
        ], style={'height': '100%', 'float': 'right', 'marginRight': '15px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

        # LOGO
        dcc.Link(children=[
            html.H1(id='logo', children="truze.ai", style={'width' : '100%', 'marginLeft': '15px', 'fontFamily': 'Avenir Next','fontWeight':'bold','color':'white', 'transform': 'translateY(45%)'}),
        ], href="/", style={'display' : 'block', 'textDecoration': 'none', 'width' : '30%', 'height' : '100%'}),
    ], style={'background': '#A5A4A4','height':'64px','padding':'auto'}),

    # ALERTS
    html.Div([
        dbc.Alert("ERROR: File Type Unsupported. Please upload a different file.", id="alert", dismissable=True, color="danger", is_open=False),
        dbc.Alert("ERROR: Session ID Not Found", id="alert2", dismissable=True, color="info", is_open=False),
        dbc.Alert("ERROR: Please replace values with types that match the column type", id="alert3", dismissable=True, color="danger", is_open=False),
    ], style={}),

    # TOP PANEL
    html.Div(id='top-panel', children=[
        html.Div(children=[
            html.Div(children=[
                html.Label('Total Variables', style={'paddingTop': '40px', 'fontFamily': 'Avenir Next', 'fontWeight': '400'}),
                html.H1(id='tot_vars1', style={'fontWeight': '500', 'color': 'black', 'fontFamily': 'Avenir Next'}),
                
            ], className="three columns number-stat-box"),

            html.Div(children=[
                html.Label('Total Rows', style={'paddingTop': '40px', 'fontFamily': 'Avenir Next', 'fontWeight': '400'}),
                html.H1(id='tot_rows1', style={'fontWeight': '500', 'color': 'black', 'fontFamily': 'Avenir Next'}),
            ], className="three columns number-stat-box"),

            html.Div(children=[
                html.Label('Total NaNs/Blanks', style={'paddingTop': '40px', 'fontFamily': 'Avenir Next', 'fontWeight': '400'}),
                html.H1(id='tot_nans1', style={'fontWeight': '500', 'color': 'black', 'fontFamily': 'Avenir Next'}),
                dbc.Button('Display', id='NanDisp', style={'paddingBottom': '0px','paddingTop': '0px','borderRadius':'7px','backgroundColor':'#002463'}, size="sm")
            ], className="three columns number-stat-box"),

            html.Div(children=[
                html.Label('Total Duplicate Columns', style={'paddingTop': '40px', 'fontFamily': 'Avenir Next', 'fontWeight': '400'}),
                html.H1(id='dup_cols1', style={'fontWeight': '500', 'color': 'black', 'fontFamily': 'Avenir Next'}),
            ], className="three columns number-stat-box"),
            html.Div(children=[
                html.Label('Total Duplicate Rows', style={'paddingTop': '40px', 'fontFamily': 'Avenir Next', 'fontWeight': '400'}),
                html.H1(id='dup_rows1', style={'fontWeight': '500', 'color': 'black', 'fontFamily': 'Avenir Next'}),
                dbc.Button('Display', id='rowDisp', style={'paddingBottom': '0px','paddingTop': '0px','borderRadius':'7px','backgroundColor':'#002463'}, size="sm")
            ], className="three columns number-stat-box"),
        ], style={'display': 'flex', 'justifyContent': 'space-evenly', 'width': '100%', 'height': '150px', 'flexWrap': 'wrap'}),
    ], className="eight columns", style={'backgroundColor': 'white', 'marginTop': '15px', 'marginLeft': '15px', 'marginBottom': '20px', 'marginRight': '15px', 'borderRadius': '25px', 'display': 'none'}),

#hi

    html.Div(id= 'upload-div', children=[
        html.Div(children=[
            dcc.Upload(
            id='upload-data',
                children=html.Div([
                    html.A('Drag and Drop/Select Files'),
                    html.Label('(Supported Types: .txt, .csv, .xls)', style={'marginTop': '15px','fontWeight':'400', 'fontSize':'0.8rem'}),
                ]),
            style={
                'verticalAlign': 'middle',
                'margin' : '0px',
                'height' : '300px',
                'width' : '300px',
                'borderRadius': '25px',
                'textAlign': 'center',
                'margin' : 'auto',
                'background' : 'white',
                'cursor' : 'pointer',
                'fontFamily' : 'Avenir Next',
                'fontWeight':'bold',
                'color' : 'black',
                'boxShadow' : '0px 6px 4px #D6D6D6',
                'fontSize':'1.0rem',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'space-evenly',
                
            }, multiple=False),
        ], style = {'borderRadius': '25px', 'height' : '200px', 'width' : '300px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-evenly'}),

        html.Div(children=[
            html.Label('or Enter Session ID:', style={'paddingTop' : '20px', 'textAlign': 'center', 'width' : '100%', 'fontFamily': 'Avenir Next', 'fontWeight': '400', 'color': 'black', 'fontFamily' : 'Avenir Next', 'fontWeight':'bold',}),
            
            html.Div(children=[
                dcc.Input(
                    id='session-text',
                    value='',
                    type="text",
                    style={'marginTop' : '25px', 'width': '60%', 'height': 45, 'margins': '15px'},
                ),
                dbc.Button('Go', id='prev-sess', class_name="me-md-2", style={'borderRadius': '15px', 'size':'sm', 'marginLeft' : '10px', 'marginTop' : '25px'}),
            ], style={'marginTop' : '10px', 'width': '70%', 'height': 25, 'margins': '15px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',}),
        ], style = {'borderRadius': '25px', 'height' : '120px', 'width' : '300px', 'backgroundColor' : 'white', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-equally', 'flexDirection': 'column'}),
        
    ], style = {'marginTop':'10%', 'width' : '100%', 'height' : '400px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'flexDirection': 'column'}),

    html.Div([
        dcc.Dropdown([''], id='dropdown', style={'marginLeft': '8px', 'width': '220px', 'display' : 'none'}, placeholder="Select Variable"),
        #html.A(dbc.Button('Upload New Datset', href = '/new', id='new', style={'marginLeft': '8px', 'marginRight' : '15px', 'borderRadius': '25px', 'backgroundColor':'#0A2463', 'display' : 'none'})),
        html.Div([
            dbc.Button('Undo', id='undo1', n_clicks=0, style={'backgroundColor':'#D8315B', 'marginRight': '15px', 'borderRadius': '25px', 'display': 'none'}),
            dbc.Button('Export', id='export1', n_clicks=0, style={'backgroundColor':'#0A2463', 'borderRadius': '25px', 'display': 'none'}),
        ], style={'marginRight': '15px'}),
    ], style={'marginTop': '24px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

    html.Div(id='datatable-div', children=[
        html.Div([
            html.Label('', id='title', style={'marginLeft': '30px', 'fontWeight': '700', 'color': 'black', 'fontFamily': 'Avenir Next', 'fontSize': '25px', }),
            html.Div([
                dcc.Input(
                    id='search-text',
                    value='',
                    placeholder='Search Dataset',
                    type="text",
                    debounce=True,
                    style={'width': '175px', 'height': 35, 'marginRight': '30px', 'borderRadius':'12px', 'textIndent':'5px', 'fontWeight':'bold','display':'none'},
                ),
            ])

        ], style={'backgroundColor': 'clear', 'borderRadius' : '25px', 'height': '20%', 'display': 'flex', 'align-items': 'center', 'justifyContent': 'space-between','marginBottom':'-15px'}),

        html.Div([
            dcc.Loading(html.Div(id="datatable", style={}), color='#119DFF', type='dot', fullscreen=True),
        ], style={'backgroundColor': 'clear', 'borderRadius' : '25px', 'height': '65%', 'marginLeft': '15px', 'marginRight': '15px'}),

        html.Div([
            dbc.Button('Delete', id='delete_button', n_clicks=0, style={'marginLeft': '30px', 'display' : 'none', 'backgroundColor' : '#D8315B'}),
            html.Div([
                dbc.Button('Delete All', id='delete_all', n_clicks=0, style={'marginRight': '30px', 'display' : 'none', 'backgroundColor' : '#D8315B','width':'150px'}),
                dcc.Checklist([' Keep One Copy'],['keep'], id = 'keep_one', inline=True, style = {'marginRight':'30px','display':'none'}),
                dbc.Button('Delete All', id='delete_all_rows', n_clicks=0, style={'marginRight': '30px', 'backgroundColor' : '#D8315B','width':'150px','display':'none'}),
            ],  style={'backgroundColor': 'clear', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginRight':'30px',})
        ], style={'backgroundColor': 'clear', 'borderRadius' : '25px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),
    ], style={'height' : '450px', 'backgroundColor': 'clear', 'marginTop': '15px', 'marginLeft': '15px', 'marginBottom': '20px', 'marginRight': '15px', 'borderRadius': '25px'}),

    html.Div(id='output-data-upload'),
    dcc.Store(id='store-data', data=[], storage_type='session'), # 'local' or 'session'
    dcc.Store(id='info-data', data=[], storage_type='session'), # 'local' or 'session'
    dcc.Store(id='edit-data', data=[], storage_type='session'), # 'local' or 'session'
    dcc.Store(id='filename-data', data=[], storage_type='session'), # 'local' or 'session'
    dcc.Store(id ='dbutrevert',data=[], storage_type='memory'),
    html.Div(id="hidden_div"),
    html.Div(id="dummy"),
    html.Div(id="dummy2"),
    html.Div(id="dummy3"),
    html.Div(id="hidden_new"),
], style={'background': '#EAEAEA'})


def parse_contents(contents, filename, uid):
    # Obtain the configuration parameters
    params = configdb.config()
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**params)
    # Create a new cursor
    curr = conn.cursor()

    # vars for parsing
    name = filename[:-4]
    data = list()

    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            if 'csv' in filename:
                # Assume user uploaded CSV file
                df = pd.read_csv(
                    io.StringIO(decoded.decode('utf-8')), header=None, engine='python')
            elif 'xlsx' in filename:
                # Assume user uploaded excel file
                df = pd.read_excel(io.BytesIO(decoded), header=None)
                
                #df = pd.read_excel(io.StringIO(decoded.decode('utf-8')), header=None)
            elif 'txt' in filename:
                # Assume user uploaded txt file 
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter = r'\t', header=None, engine='python')
            else:
                return False

        except Exception as e:
            print("here")
            return general_info, name, uid

        # set hash for dataset
        hashString = "_" + custom_hash(df)

        # modify set (add id column, remove spaces)
        titles = list()
        hasTitles = True
        
        for col in list(df.iloc[0]):
            if colNameIsNum(col):
                hasTitles = False
                break

        if hasTitles:
            df.columns = df.iloc[0]
            df = df.drop(labels=0, axis=0)
            if 'id' in df.columns:
                df = df.drop(labels='id', axis=1)
            df.insert(0, 'id', np.arange(0, df.shape[0])) # add id column

            for col in list(df.columns):
                col = str(col).strip()
                col = str(col).replace(" ", "_")
                col = str(col).replace("/", "_")
                titles.append(str(col))
        else:
            #titles.append("id")
            for i in range(0, len(list(df.columns))):
                titles.append("column_" + str(i+1))
            df.columns = titles # replace titles to modified version

        modifiedTypes = typeCheck(df)

        for key in modifiedTypes:
            df[key] = modifiedTypes[key]
        
        df.insert(0, 'id', np.arange(0, df.shape[0])) if not hasTitles else df
    
        file = df.to_dict('records') # df as dictionary

        # create table and populate in postgres
        general_info = defineColumns(file, hashString)

        # retrieve general dataset info and append hashString
        general_info = list(general_info)
        general_info.append(hashString)
        general_info = tuple(general_info)

        # execute SQL scripts
        curr.execute(general_info[0])
        conn.commit()
        curr.execute(populateTable(file, general_info))
        curr.execute(editTable([], [], general_info, findAndReplace([], [], [], hashString), f_i=[], r_i=[], c_fri=[]))

        # fetch data from call and create dataframe
        titles = general_info[2].split(", ")
        titles.pop(0)
        rows = curr.fetchall()
        for row in rows:
            data.append(list(row))
        dff = pd.DataFrame.from_records(data, columns=titles)

        conn.commit()
        curr.close()
        conn.close()
        
        return dff, general_info, name, uid
    else:
        return [{}]
    
def custom_hash(df):
    '''returns a custom hash created using pandas hash_pandas_object.
        uses .resetIndex.T in order to hash the column titles as well.
        returns a series of uint64 values.
        hexdigest() returns one string for the entire data frame'''
    to_hash = df.reset_index().T
    pandas_hash = pd.util.hash_pandas_object(to_hash, index=True)
    combined_hash = hashlib.sha256(pandas_hash.values).hexdigest()

    return combined_hash

def typeCheck(df):
    dic = dict()
    nan = 'nan' # constant for NaN
    period = "." # period to denote float
    val = str()
    
    for col in df.columns:
        i = 0
        val = str(df[col].iloc[0])

        while nan in val and i < len(df[col]):
            val = str(df[col].iloc[i])
            i = i + 1

        if period in val:
            new = list()
            try:
                val = float(val)
                if val.is_integer():
                    vals = df[col].values.tolist()
                    vals = list(map(str, vals))

                    for v in vals:
                        if nan in v:
                            new.append(v)
                        else:
                            new.append(str(int(float(v))))
                    dic[col] = new
            except:
                vals = df[col].values.tolist()
                vals = list(map(str, vals))
                for v in vals:
                    new.append(v)
        
    return dic

# undo
@app.callback(
    Output('dummy', 'children'),
    Input('undo1', 'n_clicks'),
    State('general-info', 'data'),
    State('info-data', 'data'),
    State('sesh-id', 'data'),
    prevent_initial_call = True
)
def undoMain(clicks, general_info, data, u_id):
    undoButton(u_id, data[3]) # trigger undo script
    return None

# helper for closing zip file
def close_tmp_file(tf):
    try:
        os.unlink(tf.name)
        tf.close()
    except:
        pass

# export file to csv
@app.callback(
        Output('hidden_new', 'children'),
        Output('upload-new', 'data'),
        Input('new', 'n_clicks'),
        prevent_initial_call = True
)
def new(n):
    return dcc.Location(pathname="/", id="1", refresh=True), True

# export file to csv
@app.callback(
        Output('download1', 'data'),
        Input('export1', 'n_clicks'),
        [State('info-data', 'data'),
        State('changed-data', 'data'),
        State('filename-data', 'data'),
        State('sesh-id', 'data')],
        prevent_initial_call = True
)
def generate_csv(n_nlicks, general_info, data, file_n, u_id):
    # create dataset and get filename
    dataset = revertAllEdits(general_info, u_id)[0]
    name = str(file_n)
    hash_code = general_info[3]

    # create dic to store data
    data_dic = {'data' : dataset}
    zip_dic = {}

    string = pullChanges(u_id, hash_code) # retrieve changelog from database

    # create temp file and store df
    for name, df in data_dic.items():
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        df.to_csv(temp.name)
        temp.flush()
        zip_dic[name] = temp.name

    zip_tf = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    zf = zipfile.ZipFile(zip_tf, mode='w', compression=zipfile.ZIP_DEFLATED)

    # write df and txt to zip
    for name, fn in zip_dic.items():
        zf.write(fn,f"{name}.csv")
    zf.writestr('README.txt', string)

    # close uploaded temporary files
    zf.close()
    zip_tf.flush()
    zip_tf.seek(0)
    [close_tmp_file(_tf) for _tf in zip_dic]

    return dcc.send_file(zip_tf.name, filename= "edited_files.zip")

# store a copy of the data to be passed
app.clientside_callback(
    """
    function(data) {
        return data
    }
    """,
    Output('store-data', 'data'),
    Input('datatable', 'data'),
    prevent_initial_call = True
)

# # store a copy of the data to be passed
# @app.callback(
#     Output('store-data', 'data'),
#     Input('datatable', 'data'),
#     prevent_initial_call = True
# )
# def store_data(data):
#     return data

# dropdown showing column headers
@app.callback(Output('dropdown', 'options'),
              [Input('store-data', 'data')],
              prevent_initial_call = True
)
def create_dropdown(data):
    df = pd.DataFrame(data)
    #"stored data", df)
    #global_.dt = df

    return [{'label':x, 'value':x} for x in df.columns]

# return basic stats
@app.callback(Output('tot_vars1', 'children'),
                Output('tot_rows1', 'children'),
                Output('tot_nans1', 'children'),
                Output('dup_cols1', 'children'),
                Output('dup_rows1', 'children'),
                Output('top-panel', 'style'),
              [Input('store-data', 'data')],
              [State('info-data', 'data'),
              State('sesh-id', 'data'),],
              prevent_initial_call = True
)
def showStats(data,info, u_id):
    # passed column and df for dataset
    df = pd.DataFrame(data)
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()
    find_vals = list()
    replace_vals = list()
    title_vals = list()
    r_i = list()
    c_i = list()
    f_i = list()
    del_cols = set()
    del_rows = set()
    titles = info[2].split(", ") # create titles list
    h_c = info[3].lower() #hashcode for the imported set
    curr.execute("SELECT d_r FROM CHANGELOG WHERE s_id="+str(u_id))
    deleted = curr.fetchone()
    curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = " + str(u_id))
    changesMade = curr.fetchone()
    if changesMade is not None:
        select_indices = [i for i, j in enumerate(changesMade[5])] # find indicies to which the find and replace hss been modified previously  if j == selected
        sel_indices = [i for i, j in enumerate(changesMade[10])]
        del_cols = {int(col) for col in changesMade[1]} # add deleted cols to set
        del_rows = {row for row in changesMade[2]} # add deleted rows to set
        f_i = [str(changesMade[8][i]) for i in sel_indices] # add findi rows to set
        r_i = [changesMade[9][i] for i in sel_indices] # add findi vals to set
        c_i = [changesMade[10][i] for i in sel_indices] # add findi cols to set
        delete = [titles[int(i)] for i in del_cols] # add cols to be deleted as ints
        titles = [title for title in titles if title not in delete] # edit titles to match deletions
        find_vals = [changesMade[3][i] for i in select_indices] # add find values to list
        replace_vals = [changesMade[4][i] for i in select_indices] # add replace values to list
        title_vals = [changesMade[5][i] for i in select_indices] # add column for find and replace to list

        # retrieve dictionary for sql call
    dic1 = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=h_c)
    xd = getIDTable(col_num=list(del_cols), row_num=list(del_rows), col_info=info, dictionary=dic1, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i)) # execute script to return new dataset with hidden columns
    script = "SELECT COUNT(*) FROM (" + xd[:-1] + ") AS TRP WHERE NOT (TRP IS NOT NULL)"
    if isinstance(deleted, tuple):
        if len(deleted[0]) != 0:
            check = True
        else:
            check = False
    else:
        if deleted is not None:
            check = True
        else:
            check = False
    
    if check is True:
        script += " AND id NOT IN("
        for item in deleted[0]:
                script += str(item)+ ","
        script = script[:-1]
        script += ");"
    else:
        script += ";"
    curr.execute(script)
    query = curr.fetchall()
    
    # general stats
    num_rows = len(df)
    num_vars = len(df.columns)
    tot_nans = query[0][0]
    dup_rows = df.duplicated().sum()
    dup_cols = df.T.duplicated().sum()

    # show top panel
    style = {'backgroundColor': 'white', 'marginTop': '15px', 'marginLeft': '15px', 'marginBottom': '20px', 'marginRight': '15px', 'borderRadius': '25px'}

    return num_vars, num_rows, tot_nans, dup_cols,  dup_rows, style

@app.callback(
    [Output('local-id', 'data'),
    Output('alert2', 'is_open')],
    Input('prev-sess', 'n_clicks'),
    State('session-text', 'value'),
    prevent_initial_call = True
)
def sendTrigger(prev, seshid):
    d_id = ctx.triggered_id # determine which data upload triggered save
    #print(d_id)

    # check if the id is valid
    if d_id == 'prev-sess' and seshid != '':
        # setup config to make sql calls
        params = configdb.config()
        conn = psycopg2.connect(**params)
        curr = conn.cursor()

        # retrieve basic data 
        curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = %s" % str(seshid))
        changes = curr.fetchone()

        # cursor statements
        conn.commit()
        curr.close()
        conn.close()

        # if invalid display alert
        if changes is None:
            return no_update, True
        else:
            return seshid, no_update
    else:
        return no_update, no_update

#NEED TO CHANGE TO CLIENTSIDE
# show datatable
@app.callback(\
    [Output('alert','is_open'),
    Output('search-text', 'style'),
    Output('datatable', 'children'),
    Output('delete_button', 'style'),
    Output('dropdown', 'style'),
    Output('info-data', 'data'),
    Output('filename-data', 'data'),
    Output('upload-div', 'children'),
    Output('upload-div', 'style'),
    Output('title', 'children'),
    Output('datatable-div', 'style'),
    Output('export1', 'style'),
    Output('undo1', 'style'),
    Output('new', 'style'),],
    [Input('upload-data', 'contents'),
    Input('upload-data', 'filename'),
    Input('prev-sess', 'n_clicks')],
    [State('upload-div', 'children'),
    State('general-info', 'data'),
    State('return-from', 'data'),
    State('sesh-id', 'data'),
    State('session-text', 'value'),],
    prevent_initial_call = False
)
def create_datatable(contents, filename, prev_sess, container, g, rt_from, uid, input):
    # dict to hold dataset
    data = dict()
    dataframe = pd.DataFrame()
    d_id = ctx.triggered_id # determine which data upload triggered save

    # styles
    export = {'backgroundColor':'#0A2463', 'borderRadius': '25px'}
    un = {'backgroundColor':'#D8315B', 'marginRight': '15px', 'borderRadius': '25px'}
    newButton = {'marginLeft': '8px', 'borderRadius': '25px', 'backgroundColor':'#0A2463'}
    dt_div = {'height' : '450px', 'backgroundColor': 'white', 'marginTop': '15px', 'marginLeft': '15px', 'marginBottom': '20px', 'marginRight': '15px', 'borderRadius': '25px'}

    # check if user is returning from the columnview page
    return_from = rt_from

    # check if session id was used
    if d_id == 'prev-sess':
        s_id = input
        cols = list()
        tps = list()

        # update display
        container.pop(-1)
        container.pop(-1)

        # setup config to make sql calls
        params = configdb.config()
        conn = psycopg2.connect(**params)
        curr = conn.cursor()

        # retrieve basic data 
        curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = %s" % str(s_id))
        changes = curr.fetchone()

        # show error if the set is invalid
        if changes is None: return no_update,no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        h_c = str(changes[7]).lower()
        hash_code = str(changes[7])
        u_id = str(changes[0])
        file_n = 'data'
        
        # scripts to retrieve table data
        script1 = "select column_name from information_schema.columns where table_name = '%s';" % (h_c)
        script2 = "select data_type from information_schema.columns where table_name = '%s';" % (h_c)

        # run scripts
        curr.execute(script1)
        rows = curr.fetchall()
        for row in rows:
            cols.append(row[0])

        curr.execute(script2)
        rows = curr.fetchall()
        for row in rows:
            tps.append(row[0])
        tps = [x.upper() for x in tps]

        # cursor statements
        conn.commit()
        curr.close()
        conn.close()

        # recreate general_info
        g_info = list()
        cl = ", "
        cl = cl.join(cols)

        g_info.append('None') # script to create table not needed
        g_info.append(tps)
        g_info.append(cl)
        g_info.append(hash_code)

        # revert changes
        reverted = revertAllEdits(g_info, u_id)
        data = reverted[1]
        dataframe = reverted[0]

        return False,{'width': '175px', 'height': 35, 'marginRight': '30px', 'borderRadius':'12px', 'textIndent':'5px', 'fontWeight':'bold'},  dash_table.DataTable(
                id='datatable',
                data=data,
                columns=[{'name': i, 'id': i, "selectable": True} for i in dataframe.columns],
                page_size=15,
                page_action='none',
                fixed_rows={'headers': True},
                fill_width= False,
                style_cell={
                    'minWidth': '220px', 'width': '220px', 'maxWidth': '220px',
                    #'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                style_table={
                    'height': '300px',
                    'padding' : '15px',
                    'overflowY': 'auto',
                    'overflowX': 'auto',
                    'minWidth': '100%'
                },
                column_selectable="multi",
                row_selectable="multi",
                selected_columns=[],
                selected_rows=[],
                editable=True,
                virtualization=True,
            ), {'marginLeft': '30px', 'backgroundColor' : '#D8315B', 'borderRadius' : '25px', 'width' : '100px', 'height': '50px'}, {'marginLeft': '8px', 'width': '220px', 'borderRadius': '15px',}, g_info, 'data', container, {'marginTop':'15px',}, file_n, dt_div, export, un, newButton
    
    else:
        # if the user is returnign
        if return_from:
            # retrieve data
            u_id = g[5]
            file_n = g[6]

            # update display
            container.pop(-1)
            container.pop(-1)

            # revert changes
            reverted = revertAllEdits(g, u_id)
            data = reverted[1]
            dataframe = reverted[0]

            # styles yor dataset display
            dt_div = {'height' : '450px', 'backgroundColor': 'white', 'marginTop': '15px', 'marginLeft': '15px', 'marginBottom': '20px', 'marginRight': '15px', 'borderRadius': '25px'}
            
            return False,{'width': '175px', 'height': 35, 'marginRight': '30px', 'borderRadius':'12px', 'textIndent':'5px', 'fontWeight':'bold'}, dash_table.DataTable(
                id='datatable',
                data=data,
                columns=[{'name': i, 'id': i, "selectable": True} for i in dataframe.columns],
                page_size=15,
                page_action='none',
                fixed_rows={'headers': True},
                fill_width= False,
                style_cell={
                    'minWidth': '220px', 'width': '220px', 'maxWidth': '220px',
                    #'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                style_table={
                    'height': '300px',
                    'padding' : '15px',
                    'overflowY': 'auto',
                    'overflowX': 'auto',
                    'minWidth': '100%'
                },
                column_selectable="multi",
                row_selectable="multi",
                selected_columns=[],
                selected_rows=[],
                editable=True,
                virtualization=True,
            ), {'marginLeft': '30px', 'backgroundColor' : '#D8315B', 'borderRadius' : '25px', 'width' : '100px', 'height': '50px'}, {'marginLeft': '8px', 'width': '220px', 'borderRadius': '15px',}, no_update, no_update, container, {'marginTop':'15px',}, file_n, dt_div, export, un, newButton

        elif return_from is False and d_id is None:
            return False,no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        else:
            # initial load of the application don't hide
            # parse uploaded file
            parsed = parse_contents(contents, filename, uid)

            # show error if the id is invalid
            if(parsed == False):
                return True,no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

            df = parsed[0]
            general_info = parsed[1]
            file_n = parsed[2]
            u_id = parsed[3]

            # update display
            container.pop(-1)
            container.pop(-1)

            # check if reverted changes need to be updated
            data = df.to_dict('records')
            dataframe = df
            
            # styles yor dataset display
            dt_div = {'height' : '450px', 'backgroundColor': 'white', 'marginTop': '15px', 'marginLeft': '15px', 'marginBottom': '20px', 'marginRight': '15px', 'borderRadius': '25px'}

            return False,{'width': '175px', 'height': 35, 'marginRight': '30px', 'borderRadius':'12px', 'textIndent':'5px', 'fontWeight':'bold'}, dash_table.DataTable(
                id='datatable',
                data=data,
                columns=[{'name': i, 'id': i, "selectable": True} for i in dataframe.columns],
                page_size=15,
                page_action='none',
                fixed_rows={'headers': True},
                fill_width= False,
                style_cell={
                    'minWidth': '220px', 'width': '220px', 'maxWidth': '220px',
                    #'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                },
                style_table={
                    'height': '300px',
                    'padding' : '15px',
                    'overflowY': 'auto',
                    'overflowX': 'auto',
                    'minWidth': '100%'
                },
                column_selectable="multi",
                row_selectable="multi",
                selected_columns=[],
                selected_rows=[],
                editable=True,
                virtualization=True,
            ), {'marginLeft': '30px', 'backgroundColor' : '#D8315B', 'borderRadius' : '25px', 'width' : '100px', 'height': '5c0px'}, {'marginLeft': '8px', 'width': '220px', 'borderRadius': '15px',}, general_info, file_n, container, {'marginTop':'15px',}, file_n, dt_div, export, un, newButton
    

@app.callback(
    Output('datatable', 'style_data_conditional'),
    Input('datatable', 'selected_columns'),
    prevent_initial_call = True
)
def update_styles(selected_columns):
    val = [{'if': { 'column_id': i }, 'background_color': '#D2F3FF'} for i in selected_columns]
    #print("background highlight", selected_columns)
    
    return val

@app.callback(
    Output('dummy3', 'children'),
    Input('datatable', 'data_timestamp'),
    [State('datatable', 'data'),
    State('datatable', 'data_previous')],
    prevent_initial_call = True
)
def table_edited(data_time, data, data_prev):
    df, df_previous = pd.DataFrame(data=data), pd.DataFrame(data_prev)
    oldRowCount = len(df_previous)
    oldColCount = len(df_previous.columns)
    newRowCount = len(df)
    newColCount = len(df.columns)

    if newRowCount == oldRowCount and newColCount == oldColCount:
        return None
    else:
        return no_update

# delete columns and rows
@app.callback(
    [
    Output('datatable', 'data'),
    Output('datatable', 'columns'),
    Output('datatable', 'selected_columns'),
    Output('datatable', 'selected_rows'),
    Output('edit-data', 'data'),
    Output('NanDisp', 'children'),
    Output('rowDisp', 'children'),
    Output('dbutrevert','data'),
    Output('datatable', 'row_selectable'),
    Output('delete_all', 'style'),
    Output('NanDisp', 'n_clicks'),
    Output('delete_all_rows','style'),
    Output('keep_one','style'),
    Output('NanDisp', 'style'),
    Output('rowDisp', 'style'),
    Output('alert3', 'is_open'),],
    [Input('dbutrevert','data'),
    Input('delete_button', 'n_clicks'),
    Input('dummy', 'children'),
    Input('search-text', 'value'),
    Input('NanDisp', 'n_clicks'),
    Input('rowDisp', 'n_clicks'),
    Input('dummy3', 'children'),
    Input('delete_all', 'n_clicks'),
    Input('delete_all_rows', 'n_clicks')],
    [State('keep_one','value'),
    State('datatable', 'selected_columns'),
    State('datatable', 'selected_rows'),
    State('store-data', 'data'),
    State('info-data', 'data'),
    State('edit-data', 'data'),
    State('datatable', 'derived_virtual_selected_row_ids'),
    State('sesh-id', 'data'),
    State('datatable','data'),
    State('datatable', 'data_previous')],
    prevent_initial_call = True
)
def update_output(butrevert, n_clicks, dummy, search, nanbut, rowbut, active, delall, deldups, keepone, selected_columns, selected_rows, data, general_info, edit_data, ids, u_id, init, data_prev, row_id_name=None):
    d_id = ctx.triggered_id # determine which data upload triggered save
    df, df_previous = pd.DataFrame(data=data), pd.DataFrame(data_prev)
    #print(df)
    oldRowCount = len(df_previous)
    oldColCount = len(df_previous.columns)
    newRowCount = len(df)
    newColCount = len(df.columns)
    data_retrieved = list() # store data from sql call
    data2 = list() # store data from sql call
    info = general_info # place general_info into a variable
    titles = info[2].split(", ") # create titles list
    h_c = info[3].lower() #hashcode for the imported set
    original_titles = info[2].split(", ") # create original titles list
    middle = ''
    mod_rows = list()
    find_vals = list()
    replace_vals = list()
    title_vals = list()
    r_i = list()
    c_i = list()
    f_i = list()
    del_cols = set()
    del_rows = set()
    edits = edit_data # store edits
    hash_code = general_info[3]
    dic = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=hash_code)
    # connect to the PostgreSQL database
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor() # create a new cursor
    curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = " + str(u_id))
    changesMade = curr.fetchone()

    ###print("u_id", u_id)
    # if there were previous changes
    if changesMade is not None:
        select_indices = [i for i, j in enumerate(changesMade[5])] # find indicies to which the find and replace hss been modified previously  if j == selected
        sel_indices = [i for i, j in enumerate(changesMade[10])]
        del_cols = {int(col) for col in changesMade[1]} # add deleted cols to set
        del_rows = {row for row in changesMade[2]} # add deleted rows to set
        f_i = [str(changesMade[8][i]) for i in sel_indices] # add findi rows to set
        r_i = [changesMade[9][i] for i in sel_indices] # add findi vals to set
        c_i = [changesMade[10][i] for i in sel_indices] # add findi cols to set
        delete = [titles[int(i+1)] for i in del_cols] # add cols to be deleted as ints
        titles = [title for title in titles if title not in delete] # edit titles to match deletions
        find_vals = [changesMade[3][i] for i in select_indices] # add find values to list
        replace_vals = [changesMade[4][i] for i in select_indices] # add replace values to list
        title_vals = [changesMade[5][i] for i in select_indices] # add column for find and replace to list

        # retrieve dictionary for sql call
    dic1 = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=h_c)
    xd = getIDTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic1, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i)) # execute script to return new dataset with hidden columns
    curr.execute("SELECT d_r FROM CHANGELOG WHERE s_id="+str(u_id))
    deleted = curr.fetchone()

    if d_id == 'search-text':
        if search is not None:
        
            # fetch any previous changes
            curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = " + str(u_id))
            changesMade = curr.fetchone()

            # if there were previous changes
            if changesMade is not None:
                select_indices = [i for i, j in enumerate(changesMade[5])] # find indicies to which the find and replace hss been modified previously  if j == selected
                sel_indices = [i for i, j in enumerate(changesMade[10])]
                del_cols = {int(col) for col in changesMade[1]} # add deleted cols to set
                del_rows = {row for row in changesMade[2]} # add deleted rows to set
                f_i = [str(changesMade[8][i]) for i in sel_indices] # add findi rows to set
                r_i = [changesMade[9][i] for i in sel_indices] # add findi vals to set
                c_i = [changesMade[10][i] for i in sel_indices] # add findi cols to set
                # delete = [titles[int(i)] for i in del_cols] # add cols to be deleted as ints
                # titles = [title for title in titles if title not in delete] # edit titles to match deletions
                find_vals = [changesMade[3][i] for i in select_indices] # add find values to list
                replace_vals = [changesMade[4][i] for i in select_indices] # add replace values to list
                title_vals = [changesMade[5][i] for i in select_indices] # add column for find and replace to list

            # retrieve dictionary for sql call
            dic1 = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=h_c)
            xd = getIDTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic1, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i)) # execute script to return new dataset with hidden columns

            for i in range(0, len(titles)):
                middle += "CAST(" + str(titles[i])+ " AS TEXT) LIKE '%" + search + "%' OR "
            middle = middle[:-4]

            xd = xd[:-1] # get rid of semicolon
            script = "SELECT * FROM( " + xd + " ) AS TMP" + " WHERE " + middle #root of all search queries
            script += ";"

            curr.execute(script)
            result = curr.fetchall()
            df = pd.DataFrame(result, columns= titles)
            ###print(script)

            return df.to_dict('records'), no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    if d_id == 'NanDisp':
        tip = False
        ###print(nanbut)
        if nanbut%2 == 0 and nanbut != 0:
            # if titles.index("id") != -1:
            #     titles.pop(titles.index("id"))
            # reverto = pd.DataFrame(butrevert,columns=titles)
            # return reverto.to_dict('records'), no_update, no_update, no_update, no_update, 'display', no_update, no_update, no_update 
            #titles.pop(titles.index("id"))
            revert = pd.DataFrame(butrevert,columns=titles)
            revert.pop('id')

            st = {'display':'none'}
            return revert.to_dict('records'), [{'name': i, 'id': i, "selectable": True} for i in revert.columns], no_update, no_update, no_update, 'display', no_update, no_update, no_update, st, None, no_update, no_update, no_update, {'paddingBottom': '0px','paddingTop': '0px','borderRadius':'7px','backgroundColor':'#002463'}, no_update

        else:
            # get current table displayed
            dic2 = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=h_c)
            curr.execute(getIDTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic2, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i))) # execute script to return new dataset with hidden columns

            # fetch data from call
            rows2 = curr.fetchall()
            for row in rows2:
                data2.append(list(row))

            # create new dataframe from fetched data
            df2 = pd.DataFrame.from_records(data2, columns=titles)

            curr.execute("SELECT d_r FROM CHANGELOG WHERE s_id="+str(u_id))
            deleted = curr.fetchone()
            script = "SELECT * FROM (" + xd[:-1] + ") AS TRP WHERE NOT (TRP IS NOT NULL)"

            if isinstance(deleted, tuple):
                if len(deleted[0]) != 0:
                    check = True
                else:
                    check = False
            else:
                if deleted is not None:
                    check = True
                else:
                    check = False
            
            if check is True:
                script += " AND id NOT IN("
                for item in deleted[0]:
                        script += str(item)+ ","
                script = script[:-1]
                script += ");"
            else:
                script += ";"

            curr.execute(script)
            query = curr.fetchall()
            result = pd.DataFrame(query, columns=titles)
            ind = pd.DataFrame(init, columns=titles)
            result.pop('id')
            st = {'marginRight': '30px', 'backgroundColor' : '#D8315B', 'borderRadius' : '25px', 'width' : '140px', 'height': '50px'}

            return result.to_dict('records'), [{'name': i, 'id': i, "selectable": True} for i in result.columns], no_update, no_update, no_update, 'hide', no_update, data2, no_update, st, no_update, no_update, no_update, no_update, {'display':'none'}, no_update
    
    if d_id == 'rowDisp':
        tip = True
        if rowbut is None:
            rowbut = 0
        if rowbut%2 == 0 and rowbut != 0:
            titles.pop(titles.index("id"))
            revert = pd.DataFrame(butrevert,columns=titles)
            st = {'display':'none'}

            return revert.to_dict('records'), [{'name': i, 'id': i, "selectable": True} for i in revert.columns], no_update, no_update, no_update, no_update, 'display', no_update, 'multi', no_update, no_update, st, st, {'paddingBottom': '0px','paddingTop': '0px','borderRadius':'7px','backgroundColor':'#002463'}, no_update, no_update
        
        else:
            script1 = "SELECT COUNT(*) AS count,"
            for item in titles:
                if item != "id":
                    script1 += item + ","
            script1 = script1[:-1]
            script1 += " FROM " + h_c + " GROUP BY "
            for item in titles:
                if item != "id" and item != "count":
                    script1 += item + ","
            script1 = script1[:-1]
            script1 += " HAVING COUNT(*) > 1;"
            #print("script1", script1)
            curr.execute(script1)
            query = curr.fetchall()
            titles.insert(0,"count")
            titles.pop(titles.index("id"))

            result = pd.DataFrame(query, columns=titles)
            checkst = {'marginRight':'30px'}
            st = {'marginright': '-30px', 'backgroundColor' : '#D8315B', 'borderRadius' : '25px', 'width' : '140px', 'height': '50px'}

            return result.to_dict('records'), [{'name': i, 'id': i, "selectable": True} for i in result.columns], no_update, no_update, no_update, no_update, 'hide', init, False, no_update, no_update, st , checkst, {'display':'none'}, no_update, no_update
    
    titles.pop(0) # remove the id col from variables
    ###print("titles before pull", titles)
    # fetch any previous changes
    curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = " + str(u_id))
    changesMade = curr.fetchone()

    # if there were previous changes
    if changesMade is not None:
        select_indices = [i for i, j in enumerate(changesMade[5])] # find indicies to which the find and replace hss been modified previously  if j == selected
        sel_indices = [i for i, j in enumerate(changesMade[10])]
        del_cols = {int(col) for col in changesMade[1]} # add deleted cols to set
        del_rows = {row for row in changesMade[2]} # add deleted rows to set
        f_i = [str(changesMade[8][i]) for i in sel_indices] # add findi rows to set
        r_i = [changesMade[9][i] for i in sel_indices] # add findi vals to set
        c_i = [changesMade[10][i] for i in sel_indices] # add findi cols to set
        # delete = [titles[int(i)] for i in del_cols] # add cols to be deleted as ints
        # print("delete", delete)
        # titles = [title for title in titles if title not in delete] # edit titles to match deletions
        find_vals = [changesMade[3][i] for i in select_indices] # add find values to list
        replace_vals = [changesMade[4][i] for i in select_indices] # add replace values to list
        title_vals = [changesMade[5][i] for i in select_indices] # add column for find and replace to list

    # retrieve dictionary for sql call
    dic1 = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=hash_code)
    curr.execute(getIDTable(col_num=[], row_num=[], col_info=general_info, dictionary=dic1, f_i=f_i, r_i=r_i, c_fri=c_i)) # execute script to return new dataset with hidden columns

    # fetch data from call
    rows2 = curr.fetchall()
    for row in rows2:
        data2.append(list(row))

    # create new dataframe from fetched data
    df2 = pd.DataFrame.from_records(data2, columns=info[2].split(", "))

    # retrieve dictionary for sql call
    dic = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=hash_code)

    # if a column has been selected
    if len(selected_columns) != 0:
        newly_selected = list()
        for col in selected_columns:
            index = original_titles.index(col) - 1 # retreive original index of variable to remove
            del_cols.add(index) # add index to list to hold variables to be removed
            newly_selected.append(str(index)) # add index to current delete rows list
            if col in titles: titles.remove(col) # remove col name for deleted column
        curr.execute(editTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic, f_i= f_i, r_i=r_i, c_fri=c_i)) # execute script to return new dataset with hidden columns
        pushChanges(user_id=u_id, action_id=6, change='ARRAY ' + str(newly_selected), hash_code=hash_code)
        conn.commit()
        
    # if a row has been selected
    if len(selected_rows) != 0:
        x = pd.DataFrame.from_records(data)
        newly_selected = list()
        for row in selected_rows:
            selRow = x.iloc[row].to_dict()
            inx = df2.loc[df2[list(selRow.keys())].replace(np.nan,0).isin(list(selRow.values())).all(axis=1), :]['id'].tolist()
            if len(inx) > 0: indx = inx[0] #selected_rows[0] + len(edits) # index is the row id selected
            del_rows.add(indx) # add index to delete rows list
            newly_selected.append(indx) # add index to current delete rows list
        curr.execute(editTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i))) # execute script to return new dataset with hidden columns
        pushChanges(user_id=u_id, action_id=5, change='ARRAY ' + str(newly_selected), hash_code=hash_code) # push changes to database
        conn.commit()

    df, df_previous = pd.DataFrame(data=init), pd.DataFrame(data_prev)

    if d_id == "dummy3":
        if row_id_name is not None:
            # If using something other than the index for row id's, set it here
            for _df in [df, df_previous]:

                # Why do this?  Guess just to be sure?
                assert row_id_name in _df.columns

                _df = _df.set_index(row_id_name)
        else:
            row_id_name = "index"

        # Pandas/Numpy says NaN != NaN, so we cannot simply compare the dataframes.  Instead we can either replace the
        # NaNs with some unique value (which is fastest for very small arrays, but doesn't scale well) or we can do
        # (from https://stackoverflow.com/a/19322739/5394584):
        # Mask of elements that have changed, as a dataframe.  Each element indicates True if df!=df_prev
        df_mask = ~((df == df_previous) | ((df != df) & (df_previous != df_previous)))

        # ...and keep only rows that include a changed value
        df_mask = df_mask.loc[df_mask.any(axis=1)]

        changes = []

        # This feels like a place I could speed this up if needed
        for idx, row in df_mask.iterrows():
            row_id = row.name

            # Act only on columns that had a change
            row = row[row.eq(True)]

            for change in row.iteritems():

                changes.append(
                    {
                        row_id_name: row_id,
                        "column_name": change[0],
                        "current_value": df.at[row_id, change[0]],
                        "previous_value": df_previous.at[row_id, change[0]],
                    }
                )
                #print("u_id", u_id)

        # retrieve dictionary for sql call
        dic = findAndReplace(find=[], replace=[], column=[], hashCode=hash_code)
        
        # if a value has been edited, get absolute id for row
        x = pd.DataFrame.from_records(data_prev)
        selRow = x.iloc[row_id].to_dict()
        inx = df2.loc[df2[list(selRow.keys())].replace(np.nan,0).isin(list(selRow.values())).all(axis=1), :]['id'].tolist()
        print("df2", df2)
        if len(inx) > 0: indx = inx[0] #selected_rows[0] + len(edits) # index is the row id selected

        # add new data to lists
        nulls = ['nan', 'None', "None"]
        indx = str(indx)
        c_index = original_titles.index(change[0]) # retreive original index of variable to remove
        c_type = info[1][c_index] # retrieve type of variable to remove

        # add new data to lists
        r = df.at[row_id, change[0]]

        print("column", change[0])
        print("type of col", info[1][c_index])
        print("replace val", r)
        print("check", type_check(c_type, str(r)))
        t_check = type_check(c_type, str(r))

        print("f_i", f_i, "c_i", c_i, "r_i", r_i)
        if t_check[0] == True:
            r = str(t_check[1])
            prev = prev_check(change[0], indx, r, f_i, r_i, c_i)
            if prev[0] == True:
                print("prev check true")
                # replace old data
                prev_index = prev[1]
                f_i[prev_index] = indx
                r_i[prev_index] = r if r not in nulls else str("NULL")
                c_i[prev_index] = change[0]

            else:
                print("prev check false")
                # append
                f_i.append(indx) # add index to delete rows list
                r_i.append(r) if r not in nulls else r_i.append(str("NULL"))
                c_i.append(change[0])
            
            print("f_i", f_i, "c_i", c_i, "r_i", r_i)

            # get new val and column name and run query to push changes to changelog
            currVal = r if r not in nulls else 'NULL'
            colName = change[0]
            ff_i = [int(i) for i in f_i]
            curr.execute(editTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic, f_i= f_i, r_i=r_i, c_fri=c_i))
            pushChanges(user_id=u_id, action_id=4, change=[indx, currVal, colName], hash_code=hash_code)
            #pushChanges(user_id=u_id, action_id=4, change=['ARRAY ' + str(ff_i), 'ARRAY ' + str(r_i), 'ARRAY ' + str(c_i)], hash_code=hash_code)
            conn.commit()
        else:
            # show banner that type is incorrect
            print("banner incorrect type")

            # execute script to return new dataset with hidden columns
            curr.execute(editTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i)))
            
            # fetch data from call
            rows = curr.fetchall()
            for row in rows:
                data_retrieved.append(list(row))

            # create new dataframe from fetched data
            dff = pd.DataFrame.from_records(data_retrieved, columns=titles)

            # cursor statements
            conn.commit()
            curr.close()
            conn.close()

            newData=dff.to_dict('records') # create new dictionary to return to table
            
            return newData, [{'name': i, 'id': i, "selectable": True} for i in dff.columns], [], [], edits, 'display', no_update, no_update, no_update, {'display': 'none'}, None, no_update, no_update, no_update, no_update, True

    # if delete all is clicked
    if d_id == 'delete_all':
        curr.execute("SELECT id FROM (" + xd[:-1] + ") AS TRP WHERE NOT (TRP IS NOT NULL)")
        nan_ids = curr.fetchall()
        curr_del = list()
        for nan in nan_ids:
            del_rows.add(nan[0])
            curr_del.append(nan[0])
    
        pushChanges(user_id=u_id, action_id=5, change='ARRAY ' + str(curr_del), hash_code=hash_code) # push changes to database
        conn.commit()
        curr.execute(editTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i)))

    # delete all rows that are duplicates
    if d_id == 'delete_all_rows':
        df2 = pd.DataFrame(data2, columns=info[2].split(", "))
        revert = pd.DataFrame(butrevert,columns=titles)
        dfd = revert[revert.duplicated(keep=False)]
        duplist = dfd.groupby(list(dfd)).apply(lambda x: tuple(x.index)).tolist()
        print("duplist", duplist, dfd)
        
        # list to hold absolute ids of duplicate rows
        og_ids = list()

        # get absolute id for row by finding row in df2 that matches row in revert and add to og_ids
        for dup_id in duplist:
            selRow = revert.iloc[dup_id[0]].to_dict()
            inx = df2.loc[df2[list(selRow.keys())].replace(np.nan,0).isin(list(selRow.values())).all(axis=1), :]['id'].tolist()
            og_ids.append(tuple(inx))

        # if user elects to keep one copy
        if keepone == ['keep', ' Keep One Copy']:
            curr_deletions = list()

            # leave first copy of duplicate row and delete the rest
            for item in og_ids:
                item = list(item)
                item.pop(0)
                for dup in item:
                    del_rows.add(dup)
                    curr_deletions.append(dup)

            print("del_rows in del all", del_rows)
            
            # push changes to db
            pushChanges(user_id=u_id, action_id=5, change='ARRAY ' + str(curr_deletions), hash_code=hash_code) # push changes to database
            curr.execute(editTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i)))
            query = curr.fetchall()
            
            result = pd.DataFrame(query, columns=titles)

            return result.to_dict('records'), [{'name': i, 'id': i, "selectable": True} for i in result.columns], no_update,no_update,no_update,no_update,'display',no_update,'multi', {'display' : 'none'},rowbut+1, {'display' : 'none'}, {'display' : 'none'}, no_update, no_update, no_update

        else:
            curr_deletions = list()

            # delete all copies of duplicate rows
            for item in og_ids:
                for dup in item:
                    del_rows.add(dup)
                    curr_deletions.append(dup)
            
            # push changes to db
            pushChanges(user_id=u_id, action_id=5, change='ARRAY ' + str(curr_deletions), hash_code=hash_code) # push changes to database
            curr.execute(editTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i)))
            query = curr.fetchall()
         
            result = pd.DataFrame(query, columns=titles)
            
            return result.to_dict('records'), [{'name': i, 'id': i, "selectable": True} for i in result.columns], no_update,no_update,no_update,no_update,'display',no_update,'multi', {'display' : 'none'},rowbut+1, {'display' : 'none'}, {'display' : 'none'}, no_update, no_update, no_update

    # if dummy called it, just return an empty table
    if d_id == 'dummy':
        curr.execute(editTable(col_num=list(del_cols), row_num=list(del_rows), col_info=general_info, dictionary=dic, f_i= list(f_i), r_i=list(r_i), c_fri=list(c_i))) # execute script to return new dataset with hidden columns

    # fetch data from call
    rows = curr.fetchall()
    for row in rows:
        data_retrieved.append(list(row))

    # create new dataframe from fetched data
    dff = pd.DataFrame.from_records(data_retrieved, columns=titles)

    # cursor statements
    conn.commit()
    curr.close()
    conn.close()

    newData=dff.to_dict('records') # create new dictionary to return to table
    st = {'paddingBottom': '0px','paddingTop': '0px','borderRadius':'7px','backgroundColor':'#002463'}

    return newData, [{'name': i, 'id': i, "selectable": True} for i in dff.columns], [], [], edits, 'display', 'display', no_update, no_update, {'display' : 'none'}, None, {'display' : 'none'}, {'display' : 'none'}, st, st, no_update
    
# navigate to the column view page
@app.callback(
    Output('hidden_div','children'),
    Input('check', 'data'),
    State('store-data', 'data'),
    prevent_initial_call = True
)
def display_page(value, data):
    d_id = ctx.triggered_id # determine which data upload triggered save

    # determine the id source and update sesh-id as necessary
    if d_id == 'check':
        return dcc.Location(pathname="/column", id="random_id", refresh=True)
    else:
        return no_update

# save data
@app.callback(
    [Output('global-data', 'data'),
    Output('gen-info1', 'data')],
    [Input('dropdown','value')],
    [State('store-data', 'data'),
    State('info-data', 'data'),
    State('filename-data', 'data'),
    State('sesh-id', 'data')],
    prevent_initial_call = True
)
def send_data(value, data, general_info, filename, u_id):
    # check if not initial page load
    if value == None:
        return no_update, no_update
    else:
        selected = str(value)
        ###print("select", selected)
        general_info = list(general_info)
        general_info.append(selected)
        general_info.append(u_id)
        general_info.append(str(filename))
        general_info = tuple(general_info)

        return data, general_info

def storeSelection():
    return selected

def colNameIsNum(string):
    try:
        float(string)
        if isinstance(string, np.floating) and str(string) == 'nan':
            return False
        return True
    except ValueError:
        return False




