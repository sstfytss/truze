# columnview_page.py
# Truze.AI
#
# Created by Shun Sakai and Joseph Fernando on May 12, 2023
# Copyright © 2023 Shun Sakai. All rights reserved.
#
# THE CONTENTS OF THIS PROJECT ARE PROPRIETARY AND CONFIDENTIAL.
# UNAUTHORIZED COPYING, TRANSFERRING OR REPRODUCTION OF THE CONTENTS OF THIS PROJECT, VIA ANY MEDIUM IS STRICTLY PROHIBITED.

import tempfile
from dash import html, dcc, dash_table, ctx, no_update
import plotly.express as px

from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import pandas as pd
import psycopg2

from app import app
from pages import configdb
from database.SQLTest import editTable, findAndReplace, pushChanges, pullChanges, revertColEdits, undoButton, blankFig

import visualization as v
import zipfile
import tempfile
import os

'''
# Obtain the configuration parameters
params = config()
# Connect to the PostgreSQL database
conn = psycopg2.connect(**params)
# Create a new cursor
cur = conn.cursor()
'''

header = html.H3('Welcome to the column view page!', style={'marginLeft': '15px', 'marginTop': '15px'})

layout = html.Div([
    # HEADER
    html.Div(children=[
        # EXPORT AND UNDO BUTTONS
        html.Div(children=[
            dbc.Button('Undo', id='undo', n_clicks=0, style={'backgroundColor':'#D8315B', 'marginRight': '15px', 'borderRadius': '25px'}),
            dbc.Button('Export', id='export', n_clicks=0, style={'backgroundColor':'#0A2463', 'borderRadius': '25px'}),
            dcc.Download(id='download')
        ], style={'height': '100%', 'float': 'right', 'marginRight': '15px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

        # LOGO
        dcc.Link(children=[
            html.H1(id='logo', children="truze.ai", style={'width' : '100%', 'marginLeft': '15px', 'fontFamily': 'Avenir Next','fontWeight':'bold','color':'white', 'transform': 'translateY(45%)'}),
        ], href='/', style={'display' : 'block', 'text-decoration': 'none', 'width' : '30%', 'height' : '100%'}),
    ], className="eight columns", style={'height': '64px', 'backgroundColor': '#A5A4A4', 'marginBottom': '20px'}),

    # TOP PANEL
    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.Label('Total Variables', style={'paddingTop': '40px'}),
                html.H1(id='tot_vars', style={'fontWeight': 'bold', 'color': 'black'}),
            ], className="three columns number-stat-box"),

            html.Div(children=[
                html.Label('Total Rows', style={'paddingTop': '40px'}),
                html.H1(id='tot_rows', style={'fontWeight': 'bold', 'color': 'black'}),
            ], className="three columns number-stat-box"),

            html.Div(children=[
                html.Label('Total NaNs/Blanks', style={'paddingTop': '40px'}),
                html.H1(id='tot_nans', style={'fontWeight': 'bold', 'color': 'black'}),
            ], className="three columns number-stat-box"),

            html.Div(children=[
                html.Label('Total Duplicate Columns', style={'paddingTop': '40px'}),
                html.H1(id='dup_cols', style={'fontWeight': 'bold', 'color': 'black'}),
            ], className="three columns number-stat-box"),
            html.Div(children=[
                html.Label('Total Duplicate Rows', style={'paddingTop': '40px'}),
                html.H1(id='dup_rows', style={'fontWeight': 'bold', 'color': 'black'}),
            ], className="three columns number-stat-box"),
        ], style={'display': 'flex', 'justifyContent': 'space-evenly', 'width': '100%', 'height': '150px', 'flexWrap': 'wrap'}),
    ], className="eight columns", style={'backgroundColor': 'white', 'marginTop': '15px', 'marginLeft': '15px', 'marginBottom': '20px', 'marginRight': '15px', 'borderRadius': '25px'}),

    # DROPDOWN MENU
    html.Div([
        dcc.Dropdown([''], id='drop', style={'marginLeft': '8px', 'width': '220px', 'borderRadius': '10px'}, placeholder="Select Variable"),
        html.A(dbc.Button('Back', href = '/', id='back', style={'marginLeft': '8px', 'marginRight' : '15px', 'borderRadius': '25px', 'backgroundColor':'#0A2463'})),
    ], style={'display': 'flex', 'align-items': 'center', 'justifyContent': 'space-between'}),

    # MIDDLE PANEL
    html.Div(children=[
        # LEFT SIDE
        html.Div(children=[
            # COLUMN DATATABLE
            html.Div(children=[
                # HEADER
                html.Div(children=[
                    html.H1('Column Name', id='colName', style={'fontFamily': 'Avenir Next', 'marginTop': '15px', 'marginLeft': '20px', 'fontWeight': 'bold', 'color': 'black'}),
                ], style={'height': '10%', 'width': '100%', 'borderRadius': '25px', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-evenly', 'backgroundColor' : 'clear'}),

                # DATA TABLE
                html.Div(children=[
                    dcc.Loading(html.Div(id="dt", style={'width' : '100%', 'marginTop': '15px', 'height': '50px'}), color='#119DFF', type='dot', fullscreen=False),
                ], style={'height': '80%', 'borderRadius': '25px', 'width' : '100%', 'backgroundColor' : 'clear'}),

                # BUTTONS
                html.Div(children=[
                    html.Div(children=[
                        dbc.Button('Find and Replace', id='replace', n_clicks=0, style={'marginLeft': '15px', 'display' : 'none'}, size ='sm'),
                        #dbc.Button('Delete', id='del-button', n_clicks=0, style={'marginLeft': '15px', 'display' : 'none'}, size ='sm'),
                    ], style={'height': '100%', 'width': '100%', 'backgroundColor': 'clear', 'borderRadius': '25px', 'float': 'right', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-evenly'}),
                ], style={'height': '10%', 'width': '100%', 'borderRadius': '25px', 'backgroundColor' : 'clear'}),

            ], style={'height': '100%', 'width': '100%', 'backgroundColor': 'white', 'borderRadius': '25px', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'space-evenly'}),
        ], style={'height': '100%', 'width' : '30%', 'marginRight': '15px', 'backgroundColor': 'black', 'borderRadius': '25px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',}),

        # RIGHT SIDE
        html.Div(children=[
            # FIRST TWO BOXES
            html.Div(children=[
                # GENERAL INFO PANEL
                html.Div(children=[ 
                        # TOP ROW
                        html.Div(children=[
                            html.H1('Column Name', id='coltitle', style={'fontFamily': 'Avenir Next', 'marginLeft': '20px', 'fontWeight': 'bold', 'color': 'black'}),
                            html.Label('--', style={'marginLeft': '20px'}),
                        ], style={'height': '25%', 'width': '100%', 'borderRadius': '25px', 'marginTop': '15px'}),

                        # CENTER ROW
                        html.Div(children=[
                            html.Label('Column Overview', style={'fontFamily': 'Avenir Next', 'marginLeft': '20px', 'fontWeight': 'bold', 'color': 'black'}),
                            
                            html.Div(children=[
                                html.Div(children=[
                                    html.Label('Total Rows', style={'width': '100%', 'marginLeft': '20px', 'color': 'black', 'fontSize':'12px'}),
                                    html.Label('', id='rows', style={'marginLeft': '20px', 'color': 'black', 'fontWeight': 'bold'}),
                                ], style={'height': '100%', 'width': '33%', 'borderRadius': '25px', 'display': 'inline-block'}),
                                html.Div(children=[
                                    html.Label('Total NaNs/Blanks', style={'width': '100%', 'marginLeft': '20px', 'color': 'black', 'fontSize':'12px'}),
                                    html.Label('', id='nans', style={'marginLeft': '20px', 'color': 'black', 'fontWeight': 'bold'}),
                                ], style={'height': '100%', 'width': '33%', 'borderRadius': '25px', 'display': 'inline-block'}),
                                html.Div(children=[
                                    html.Label('Total Duplicates', style={'width': '100%', 'marginLeft': '20px', 'color': 'black', 'fontSize':'12px'}),
                                    html.Label('', id='dups', style={'marginLeft': '20px', 'color': 'black', 'fontWeight': 'bold'}),
                                ], style={'height': '100%', 'width': '33%', 'borderRadius': '25px', 'display': 'inline-block', 'color': 'black'}),
                            ], style={'height': '70%', 'width': '100%', 'borderRadius': '25px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-evenly'}),
                        
                        ], style={'height': '25%', 'width': '100%', 'borderRadius': '25px'}),

                        # BOTTOM ROW
                        html.Div(children=[
                            html.Label('General Statistics', style={'fontFamily': 'Avenir Next', 'marginLeft': '20px', 'fontWeight': 'bold', 'color': 'black'}),

                            html.Div(children=[
                                html.Div(children=[
                                    html.Label('Mean', style={'width': '100%', 'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontSize':'12px'}),
                                    html.Label('', id='mean', style={'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontWeight': 'bold'}),
                                ], style={'height': '100%', 'width': '20%', 'borderRadius': '25px', 'display': 'inline-block', }),
                                html.Div(children=[
                                    html.Label('Median', style={'width': '100%', 'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontSize':'12px'}),
                                    html.Label('', id='median', style={'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontWeight': 'bold'}),
                                ], style={'top': '50%', 'height': '100%', 'width': '20%', 'borderRadius': '25px', 'display': 'inline-block', 'color': 'black'}),
                                html.Div(children=[
                                    html.Label('Mode', style={'width': '100%', 'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontSize':'12px'}),
                                    html.Label('', id='mode', style={'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontWeight': 'bold'}),
                                ], style={'top': '50%', 'height': '100%', 'width': '20%', 'borderRadius': '25px', 'display': 'inline-block', 'color': 'black'}),
                                html.Div(children=[
                                    html.Label('S.D', style={'width': '100%', 'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontSize':'12px'}),
                                    html.Label('', id='std', style={'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontWeight': 'bold'}),
                                ], style={'top': '50%', 'height': '100%', 'width': '15%', 'borderRadius': '25px', 'display': 'inline-block', 'color': 'black'}),
                                html.Div(children=[
                                    html.Label('Range', style={'width' : '100%', 'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'marginRight': '0px', 'color': 'black', 'fontSize':'12px'}),
                                    html.Label('', id='rng', style={'top': '50%', 'transform': 'translateY(50%)', 'marginLeft': '20px', 'color': 'black', 'fontWeight': 'bold', 'backgroundColor' : 'white'}),
                                ], style={'top': '50%', 'height': '100%', 'width': '25%', 'borderRadius': '25px', 'display': 'inline-block', 'color': 'black', 'alignItems': 'center',}),
                                
                            ], style={'marginRight': '15px', 'height': '100%', 'width': '100%', 'borderRadius': '25px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-evenly'}),
                            
                        ], style={'height': '25%', 'width': '100%', 'borderRadius': '25px', }),
                    
                ], style={'height': '100%', 'width': '48%', 'backgroundColor': 'white', 'borderRadius': '25px', 'display': 'inline-block', 'display': 'flex' , 'flexDirection': 'column', 'justifyContent': 'space-evenly'}),

                html.Div(children=[ 
                    dcc.Loading(dcc.Graph(id='histogram', figure={}, style={'height' : '100%', 'width' : '150%', 'borderRadius': '25px', 'overflow-x':'auto'}), color='#119DFF', type='dot', fullscreen=False),
                ], style={'height': '100%', 'width': '48%', 'backgroundColor': 'white', 'borderRadius': '25px', 'display': 'inline-block', 'backgroundColor' : 'white','marginRight':'30px'}),
            ], style={'height': '48%', 'width': '100%',  'borderRadius': '25px', 'backgroundColor' : 'clear', 'display': 'flex' , 'alignItems': 'center', 'justifyContent': 'space-between'}),

            # BOTTOM TWO BOXES
            html.Div(id='bot-div', children=[
                # CHANGELOG
                html.Div(id='cg-log', children=[
                    html.Div(id='cg-top', children=[
                        html.H1('Change Log', style={'fontFamily': 'Avenir Next', 'paddingTop': '30px', 'marginLeft': '30px', 'marginRight': '30px', 'fontWeight': 'bold', 'color': 'black'}),
                        html.H1('⌄', style={'fontFamily': 'Avenir Next', 'fontSize':'40px', 'paddingTop': '15px', 'marginLeft': '30px', 'marginRight': '40px', 'fontWeight': 'bold', 'color': 'black'}),
                    ], style={'width': '100%', 'borderRadius': '25px', 'display': 'flex' , 'alignItems': 'top', 'justifyContent': 'space-between', 'cursor': 'pointer'}),
                    html.Label('', id='change-log', style={'display':'none', 'top': '50%', 'marginLeft': '30px', 'marginRight': '30px', 'color': 'black', 'fontSize':'12px', 'white-space': 'pre-line'}),
                ], style={'height': '20%', 'width': '48%', 'borderRadius': '25px', 'backgroundColor': 'white'}),
                
                # BOX PLOT
                html.Div(children=[
                    html.Label('box plot is not supported for this data type', id='N/A', style={'display':'none', 'fontFamily': 'Avenir Next', 'textAlign' : 'center', 'color': 'black', 'fontWeight' : '600', 'width' :'100%', 'marginTop': '30%', 'fontSize':'10px'}),
                    dcc.Loading(dcc.Graph(id='box-chart', figure={}, style={'height' : '100%', 'borderRadius': '25px'}), color='#119DFF', type='dot', fullscreen=False),
                ], style={'height': '100%', 'width': '48%', 'backgroundColor': 'white', 'borderRadius': '25px', 'display': 'inline-block','marginRight':'30px'}),
            ], style={'height': '48%', 'width': '100%', 'backgroundColor': 'clear', 'borderRadius': '25px', 'display': 'flex' , 'alignItems': 'top', 'justifyContent': 'space-between'}),

        ], style={'height': '100%', 'width' : '70%', 'marginLeft': '15px', 'backgroundColor': 'clear', 'borderRadius': '25px', 'display': 'flex' , 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'space-between'}),

    ], style={'height': '1000px', 'marginTop': '20px', 'marginBottom': '15px', 'marginLeft': '15px', 'marginRight': '15px', 'backgroundColor': '#EAEAEA', 'borderRadius': '25px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'backgroundColor' : '#EAEAEA'}),

    #html.Button('Delete', id='button', n_clicks=0, style={'marginLeft': '15px', 'display' : 'none'}),
    
    dcc.Store(id='column-data', data=[], storage_type='memory'),
    dcc.Store(id='column2-data', data=[], storage_type='memory'),
    dcc.Store(id='column3-data', data=[], storage_type='memory'),
    dcc.Store(id='hist-data', data=[], storage_type='memory'),
    dcc.Store(id='box-data', data=[], storage_type='memory'),
    
    dbc.Modal(
        [
            dbc.ModalHeader("Find and Replace All"),
            dbc.ModalBody(
                html.Div(children=[
                    html.Div(children=[
                        html.Label('Find Value:', style={'color': 'black', 'fontSize':'15px'}),
                        dcc.Textarea(
                            id='find-text',
                            value='',
                            style={'width': '100%', 'height': 50},
                        ),
                    ], style={'width': '40%', 'height': 50}),
                    html.Div(children=[
                        html.Label('Replace All:', style={'color': 'black', 'fontSize':'15px'}),
                        dcc.Textarea(
                            id='replace-text',
                            value='',
                            style={'width': '100%', 'height': 50, 'margins': '15px'},
                        ),
                    ], style={'width': '40%', 'height': 50}),
                ], style={'width': '100%', 'borderRadius': '25px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),
            ),
            html.Label('Leave box blank to find or replace NaNs and blanks', style={'marginTop' : '10px', 'marginLeft': '15px', 'fontSize' : '12px', 'color': 'black'}),
            dbc.ModalFooter(
                html.Div(
                    [
                        dbc.Button("REPLACE", id='replace-button', className='ml-auto',style = {'backgroundColor':'#D8315B','borderRadius':'25px'}),
                        html.Label('', id='warning', style={'marginTop' : '5px', 'fontSize' : '15px', 'color': 'red', 'fontWeight' : 'bold'}),
                        dbc.Button("CLOSE", id='close', className='ml-auto', style={'backgroundColor':'#0A2463','borderRadius':'25px'}),
                    ],
                style={'width': '100%', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),
            ),
        ],
        id='modal',
    ),
    html.Div(id="hidden"),

], style={'backgroundColor': '#EAEAEA'})

# helper for closing zip file
def close_tmp_file(tf):
    try:
        os.unlink(tf.name)
        tf.close()
    except:
        pass

# change height of changelog box
@app.callback(
    [Output('cg-log', 'style'),
    Output('change-log', 'style')],
    Input('cg-log', 'n_clicks'),
    State('cg-log', 'style'),
    prevent_initial_call = True
)
def collapseChanges(clicks, st):
    height = st['height'] # retrieve height attribute

    # shrink or expand depending on current size
    if height == '100%':
        div_style = {'height': '20%', 'width': '48%', 'borderRadius': '25px', 'backgroundColor': 'white'}
        text_style = {'top': '50%', 'marginLeft': '30px', 'color': 'black', 'fontSize':'12px', 'white-space': 'pre-line', 'display':'none'}
    else:
        div_style = {'height': '100%', 'width': '48%', 'borderRadius': '25px', 'backgroundColor': 'white'}
        text_style = {'top': '50%', 'marginLeft': '30px', 'color': 'black', 'fontSize':'12px', 'white-space': 'pre-line'}
    #print(clicks, st['height'])
    return div_style, text_style

@app.callback(
    Output('column3-data', 'data'),
    Input('undo', 'n_clicks'),
    State('general-info', 'data'),
    prevent_initial_call = True
)
def undoReplace(clicks, general_info):
    u_id = general_info[5]
    hash_code = general_info[3]
    undoButton(u_id, hash_code)
    reverted = revertColEdits(general_info)
    df = reverted[2]
    return df

@app.callback(
    Output('hidden2', 'children'),
    Input('logo', 'n_clicks'),
    prevent_initial_call = True
)
def returnMain(clicks):
    return dcc.Location(pathname="/", id="2", refresh=True)

# update change log
@app.callback(
        Output('change-log', 'children'),
        Input('changed-data', 'data'),
        [State('general-info', 'data')],
        prevent_initial_call = True
)
def updateChanges(data, general_info):
    u_id = general_info[5] # retrieve user id
    hash_code = general_info[3] # retrieve hash
    string = pullChanges(u_id, hash_code) # retrieve changelog from database
    s = string[203:] if len(string) > 200 else string # remove introduction to changelog
    return s

# export file to csv
@app.callback(
        Output('download', 'data'),
        Input('export', 'n_clicks'),
        [State('general-info', 'data'),
        State('changed-data', 'data')],
        prevent_initial_call = True
)
def generate_csv(n_nlicks, general_info, data):
    # create dataset and get filename
    dataset = pd.DataFrame(data)
    name = general_info[6]

    # create dic to store data
    data_dic = {'data' : dataset}
    zip_dic = {}

    u_id = general_info[5] # user id
    hash_code = general_info[3] # retrieve hash
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

@app.callback(
    Output('modal', 'is_open'),
    [Input('replace', 'n_clicks'),
    Input('close', 'n_clicks'),
    Input('replace-button', 'n_clicks')],
    [State('modal', 'is_open')],
    prevent_initial_call = True
)
def toggle_modal(n1, n2, n3, is_open):
    if n1 or n2 or n3:
        return not is_open
    return is_open

@app.callback( 
    [Output('dt', 'data'),
    Output('dt', 'columns'),
    Output('find-text', 'value'),
    Output('replace-text', 'value'),
    Output('column2-data', 'data')],
    [Input('replace-button', 'n_clicks'),
    Input('general-info', 'data'),
    Input('undo', 'n_clicks')],
    [State('find-text', 'value'),
    State('replace-text', 'value')],
    prevent_initial_call = True
)
def update_output(n_clicks, general_info, undo, find, replace):
    # setup config to make sql calls
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()

    # store passed column + create list to store data
    data = list()
    selected = str(general_info[4])
    u_id = str(general_info[5])
    find_vals = list()
    replace_vals = list()
    title_vals = list()
    row_vals = list()
    col_vals = list()
    f_i = list()
    r_i = list()
    c_i = list()
    hash_code = general_info[3]
    d_id = ctx.triggered_id # determine which data upload triggered save

    # fetch any previous changes
    curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = " + str(u_id) + ";")
    changesMade = curr.fetchone()

    # if there were previous changes
    if changesMade is not None:
        select_indices = [i for i, j in enumerate(changesMade[5])] # find indicies to which the find and replace hss been modified previously  if j == selected
        sel_indices = [i for i, j in enumerate(changesMade[10])] # find indicies to which the find and replace hss been modified previously  if j == selected
        col_vals = list(map(int, changesMade[1])) # add rows for del cols
        row_vals = list(map(int, changesMade[2])) # add rows for del row
        find_vals = [changesMade[3][i] for i in select_indices] # add find values to list
        replace_vals = [changesMade[4][i] for i in select_indices] # add replace values to list
        title_vals = [changesMade[5][i] for i in select_indices] # add column for find and replace to list
        f_i = [changesMade[8][i] for i in sel_indices] # add findi rows to set
        r_i = [changesMade[9][i] for i in sel_indices] # add findi vals to set
        c_i = [changesMade[10][i] for i in sel_indices] # add findi cols to set

    # append current find and replace values to list
    if d_id == "replace-button":
        find_vals.append(find) if find != "" else find_vals.append("NULL")
        replace_vals.append(replace) if replace != "" else replace_vals.append("NULL")
        title_vals.append(selected) #if find != "" and replace != "" else title_vals
        find = "NULL" if find == "" else find
        replace = "NULL" if replace == "" else replace

    # perform sql queries and save changes to changelog
    dic = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=hash_code)
    curr.execute(editTable(col_num=col_vals, row_num=row_vals, col_info=general_info, dictionary=dic, f_i=f_i, r_i=r_i, c_fri=c_i))
    if find != "" and replace != "": pushChanges(user_id=u_id, action_id=3, change=[find, replace, selected], hash_code=hash_code)

    # fetch data from call and create dataframe
    titles = general_info[2].split(", ")
    titles.pop(0)
    title_vals = [titles[i] for i, j in enumerate(titles) if i in col_vals] # find values to remove from titles list
    titles = [t for t in titles if t not in title_vals] # return only remaining titles

    rows = curr.fetchall()
    for row in rows:
        data.append(list(row))

    # cursor statements
    conn.commit()
    curr.close()
    conn.close()

    # data to return
    df = pd.DataFrame.from_records(data, columns=titles)
    newDic = df.to_dict('records')
    dtf = df[[general_info[4]]] # extract column being viewed from df
    newData= dtf.to_dict('records') # create new dictionary to return to table
    columns = [{'name': str(i), 'id': str(i), "selectable": False} for i in dtf.columns]

    return newData, columns, '', '', newDic

@app.callback(
    Output('replace-text', 'children'),
    Input('replace-text', 'n_clicks'),
    [State('replace-text', 'value'),
    State('general-info', 'data')],
    prevent_initial_call = True
)
def collect_output(n_clicks, value, general_info):
    # store passed column
    selected = str(general_info[4])
    return 'You have entered: \n{}'.format(value)


# dropdown showing column headers
@app.callback([Output('drop', 'options'),
               Output('drop', 'placeholder'),
               #Output('del-button', 'style'),
               Output('replace', 'style'),
              ],
              [Input('changed-data', 'data')],
              [State('global-data', 'data'),
              State('general-info', 'data')],
              prevent_initial_call = True
)
def create_dropdown(data, dataset, general_info):
    # passed column and df for dataset
    selected = str(general_info[4])
    df = pd.DataFrame(dataset)

    return [{'label':x, 'value':x} for x in df.columns], selected, {'marginLeft': '15px','marginRight': '15px', 'backgroundColor' : '#0A2463', 'borderRadius' : '25px', 'width' : '200px'}

#return [{'label':x, 'value':x} for x in df.columns], selected, {'marginRight': '15px', 'backgroundColor' : '#D8315B',  'borderRadius' : '25px', 'width' : '200px', 'display' : 'none'}, {'marginLeft': '15px', 'backgroundColor' : '#0A2463', 'borderRadius' : '25px', 'width' : '200px'}
#{'marginRight': '15px','marginLeft': '15px', 'backgroundColor' : '#D8315B',  'borderRadius' : '25px', 'width' : '200px'}
# dropdown navigation
@app.callback(
    [Output('hidden','children'),
    Output('gen-info2', 'data')],
    [Input('drop', 'value')],
    [State('changed-data', 'data'),
    State('general-info', 'data')],
    prevent_initial_call = True
)
def display_page(value, data, general_info):
    # check if the value change is the initial load
    if value == None:
        return no_update, no_update
    else: # if it is not the initial load, update the value for general_info
        gen = general_info
        gen[4] = value

        return dcc.Location(pathname="/column", id="2", refresh=True), gen

#669 ms
# show datatable
@app.callback([Output('dt', 'children'),
                Output('coltitle', 'children'),
                Output('colName', 'children'),
                Output('column-data', 'data')],
              [Input('general-info','data')],
              [State('global-data', 'data'),
                State('dt', 'columns'),
                State('general-info', 'data')],
              prevent_initial_call = False
)
def create_datatable(general_info, dataset, status, check):
    # check if a dt has previously been created
    if status is not None: # if a dt has been created, don't create a new one
        selected = str(general_info[4]) # passed column
        
        return no_update, selected, selected, no_update,

    else: # if a dt has not been created, create a new one
        selected = str(general_info[4]) # passed column
        returnVal = revertColEdits(general_info) # return reverted dataset if any previous changes exist
        d = returnVal[0] # data for datatable
        cols = returnVal[1] # columns for datatable
        df = returnVal[2] # dataframe for table
        
        # return a dash table with the updated data
        return dash_table.DataTable(
            id='dt',
            data= d,
            columns= cols,
            page_size=1,
            page_action='none',
            fixed_rows={'headers': True},
            style_cell={
                'minWidth': '100%', 'width': '100%', 'maxWidth': '100%',
                'textOverflow': 'ellipsis', 'fontFamily': 'Avenir Next', 'textAlign':'center', 'fontWeight':'Bold',
                'padding': '5px',
            },
            style_table={
                'height': '900px',
                'padding' : '15px',
                'overflowY': 'auto',
                'overflowX': 'auto',
            },
            css=[
                {'selector': 'table', 'rule': 'width: 100%'},
                {'selector': '.dash-spreadsheet.dash-freeze-top, .dash-spreadsheet .dash-virtualized', 'rule': 'max-height: 780px'},
                #{'border': '1px solid blue', 'border-radius': '15px', 'overflow': 'hidden'}
            ], filter_action='native',
            virtualization=True,
            filter_options={"placeholder_text": "Search Column"},
        ), selected, selected, df


# app.clientside_callback(
#     """
#     function(general_info, dataset, status, check){
#         # if a dt has been created, don't create a new one
#         if (status != null){
#             var selected = String(general_info[4]); # passed column
            
#             return no_update, selected, selected, no_update;
#         }else{
#             var selected = String(general_info[4]); # passed column
#             var returnVal = revertColEdits(general_info); # return reverted dataset if any previous changes exist
#             var d = returnVal[0]; # data for datatable
#             var cols = returnVal[1]; # columns for datatable
#             var df = returnVal[2]; # dataframe for table
            
#             # return a dash table with the updated data
#             return dash_table.DataTable(
#                 id='dt',
#                 data= d,
#                 columns= cols,
#                 page_size=1,
#                 page_action='none',
#                 fixed_rows={'headers': True},
#                 style_cell={
#                     'minWidth': '100%', 'width': '100%', 'maxWidth': '100%',
#                     'textOverflow': 'ellipsis', 'fontFamily': 'Avenir Next', 'textAlign':'center', 'fontWeight':'Bold',
#                     'padding': '5px',
#                 },
#                 style_table={
#                     'height': '900px',
#                     'padding' : '15px',
#                     'overflowY': 'auto',
#                     'overflowX': 'auto',
#                 },
#                 selected_columns=[],
#                 css=[
#                     {'selector': 'table', 'rule': 'width: 100%'},
#                     {'selector': '.dash-spreadsheet.dash-freeze-top, .dash-spreadsheet .dash-virtualized', 'rule': 'max-height: 780px'},
#                     #{'border': '1px solid blue', 'border-radius': '15px', 'overflow': 'hidden'}
#                 ], filter_action='native',row_selectable='multi' ,
#             ), selected, selected, df;
#         }
#     }
#     """,
#     [Output('dt', 'children'),
#     Output('coltitle', 'children'),
#     Output('colName', 'children'),
#     Output('column-data', 'data')],
#     [Input('general-info','data')],
#     [State('global-data', 'data'),
#     State('dt', 'columns'),
#     State('general-info', 'data')]
# )

# load data for histograms
@app.callback([Output('hist-data', 'data'),
                 Output('box-data', 'data'),
                 Output('box-chart', 'style'),
                 Output('N/A', 'style')],
              [Input('changed-data', 'data')],
              [State('general-info', 'data')],
              prevent_initial_call = True
)
def storeData(data, general_info):
    # get selected variable and title array
    selected = str(general_info[4])
    titles = general_info[2].split(", ")
    invalid = 'N/A'

    # get overall df label with titles + drop id column
    df = pd.DataFrame.from_records(data, columns=titles)
    df = df.drop('id', axis=1)

    # load histogram + box plot
    hist = v.hist(df, selected, 'normal')
    box = v.box(df, selected) if v.box(df, selected) != invalid else 'N/A'

    if box != invalid:
        box_style = {'height' : '100%', 'borderRadius': '25px'}
        label_style = {'fontFamily': 'Avenir Next', 'textAlign' : 'center', 'color': 'black', 'fontWeight' : '600', 'width' :'100%', 'marginTop': '40%', 'fontSize':'20px', 'display':'none'}
        return hist, box, box_style, label_style
    else:
        label_style = {'fontFamily': 'Avenir Next', 'textAlign' : 'center', 'color': 'black', 'fontWeight' : '600', 'width' :'100%', 'marginTop': '40%', 'fontSize':'20px'}
        box_style = {'height' : '100%', 'borderRadius': '25px', 'display': 'none'}
        return hist, no_update, box_style, label_style

# create histogram via client-side callback
app.clientside_callback(
    """
    function(figure_data, general_info){
        if(figure_data === undefined) {
            return {'data': [], 'layout': {}};
        }
        const fig = Object.assign({}, figure_data, {
                'layout': {
                    ...figure_data.layout,
                }
        });
        return fig;
    }
    """,
    Output('histogram', 'figure'),
    Input('hist-data', 'data'),
    State('general-info', 'data')
)

# create box plot via client-side callback
app.clientside_callback(
    """
    function(figure_data, general_info){
        if(figure_data === undefined) {
            return {'data': [], 'layout': {}};
        }
        const fig = Object.assign({}, figure_data, {
                'layout': {
                    ...figure_data.layout,
                }
        });
        return fig;
    }
    """,
    Output('box-chart', 'figure'),
    Input('box-data', 'data'),
    State('general-info', 'data')
)

@app.callback(Output('mean', 'children'),
                Output('median', 'children'),
                Output('mode', 'children'),
                Output('std', 'children'),
                Output('rng', 'children'),
                Output('tot_vars', 'children'),
                Output('tot_rows', 'children'),
                Output('tot_nans', 'children'),
                Output('dup_cols', 'children'),
                Output('dup_rows', 'children'),
                Output('rows', 'children'),
                Output('dups', 'children'),
                Output('nans', 'children'),
              [Input('changed-data', 'data')],
              [State('general-info', 'data')],
              prevent_initial_call = True
)
def showStats(data, general_info):
    # passed column and df for dataset
    selected = str(general_info[4])
    df = pd.DataFrame(data)

    # general stats
    num_rows = len(df)
    num_vars = len(df.columns)
    tot_nans = df.isnull().sum().sum()
    dup_rows = df.duplicated().sum()
    dup_cols = df.T.duplicated().sum()

    # create dict for column
    colDf = df[selected]
    dic = v.stats(df, selected)

    # column stats
    mean = dic.get('mean')
    mode = dic.get('mode') if len(dic.get('mode')) == 1 or mean == 'N/A' else 'MANY'
    median = dic.get('median')
    std = dic.get('std')
    rng = dic.get('range')
    median = dic.get('median')
    dups = colDf.duplicated().sum()
    nans = colDf.isnull().sum().sum()
    return mean, median, mode, std, rng, num_vars, num_rows, tot_nans, dup_cols, dup_rows, num_rows, dups, nans


# store a copy of the data to be passed
# @app.callback(
#     Output('changed-data', 'data'),
#     [Input('column-data', 'data'),
#     Input('column2-data', 'data'),
#     Input('column3-data', 'data'),
#     State('changed-data', 'data')],
#     prevent_initial_call = True
# )
# def store_column_data(data1, data2, data3, currentChangedData):
#     d_id = ctx.triggered_id # determine which data upload triggered save
#     storage = dict() # empty dict to store data

#     if d_id == 'column-data': # if triggered by reload
#         return data1
#     elif d_id == 'column2-data': # if triggered by data revertion
#         return data2
#     elif d_id == 'column3-data':
#         return data3

# create box plot via client-side callback
app.clientside_callback(
    """
    function(data1, data2, data3, currentChangedData){
        const ctx = dash_clientside.callback_context;
        const triggered_id = ctx.triggered[0].prop_id.split(".")[0];

        if(triggered_id === 'column-data') {
            return data1;
        }else if(triggered_id === 'column2-data'){
            return data2;
        }else if(triggered_id === 'column3-data'){
            return data3;
        }else{
            return dash_clientside.no_update;
        }
    }
    """,
    Output('changed-data', 'data'),
    [Input('column-data', 'data'),
    Input('column2-data', 'data'),
    Input('column3-data', 'data')],
    State('changed-data', 'data'),
    prevent_initial_call = True
)
