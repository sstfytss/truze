# index.py
# Truze.AI
#
# Created by Shun Sakai and Joseph Fernando on May 11, 2023
# Copyright © 2023 Shun Sakai. All rights reserved.
#
# THE CONTENTS OF THIS PROJECT ARE PROPRIETARY AND CONFIDENTIAL.
# UNAUTHORIZED COPYING, TRANSFERRING OR REPRODUCTION OF THE CONTENTS OF THIS PROJECT, VIA ANY MEDIUM IS STRICTLY PROHIBITED.

from dash import html, dcc, ctx, no_update
from dash.dependencies import Input, Output, State
import numpy as np
import os
import logging
from app import app
from database.SQLTest import previousUser

from pages import import_page, overview_page, columnview_page

log = logging.getLogger('werkzeug') 
log.setLevel(logging.CRITICAL)

# connect to database
page_container = html.Div(
    children=[
        # represents the URL bar, doesn't render anything
        dcc.Location(
            id='url',
            refresh=True,
        ),
        # content will be rendered in this element
        html.Div(id='page-content'),
        dcc.Store(id='global-data', data=[], storage_type='session'),
        dcc.Store(id='general-info', data=[], storage_type='memory'), # 'local' or 'session'
        dcc.Store(id='gen-info1', data=[], storage_type='session'),
        dcc.Store(id='gen-info2', data=[], storage_type='session'),
        dcc.Store(id='changed-data', data=[], storage_type='memory'), # 'local' or 'session'
        dcc.Store(id='return-from', data=False, storage_type='session'),
        dcc.Store(id='upload-new', data=False, storage_type='session'),
        dcc.Store(id='sesh-id', data=[], storage_type='session'),
        dcc.Store(id='local-id', data='', storage_type='session'),
        dcc.Store(id='local-id2', data='', storage_type='session'),
        dcc.Store(id='check', data=False, storage_type='session'),
    ]
)

index_layout = html.Div(
    children=[
        dcc.Link(
            children='Go to Page 1',
            href='/page-1',
        ),
        html.Br(),
        dcc.Link(
            children='Go to Page 2',
            href='/page-2',
        ),
    ] 
)

app.layout = page_container

app.validation_layout = html.Div(
    children = [
        page_container,
        index_layout,
        import_page.layout,
        overview_page.layout,
    ]
)

### Update Page Container ###
@app.callback(
    Output('local-id2', 'data'),
    Output('return-from', 'data'),
    Output('page-content','children'),
    [Input('url','pathname'),],
    State('general-info', 'data'),
    State('upload-new', 'data'),
    State('sesh-id', 'data'),
)
def display_page(pathname, data, new, uid):
    if pathname == '/':
        return_from = False if data == [] else True
        exist = True
        u_id = np.random.randint(100) if return_from is False else uid

        # script to check if user_id has already been assigned
        while return_from == False and exist == True:
            exist = previousUser(u_id)
            if exist == True:
                u_id = np.random.randint(100)

        return u_id, return_from, import_page.layout

    elif pathname == '/page-1':
        return  no_update, no_update, import_page.layout
    elif pathname == '/column':
        return no_update, no_update, columnview_page.layout
    elif pathname == '/new':
        return_from = False
        return no_update, return_from, import_page.layout
    else:
        return '404'

# update store of session id depending on upload format
@app.callback(
    Output('sesh-id', 'data'),
    Input('local-id', 'data'),
    Input('local-id2', 'data'),
)
def save_uid(local, local2):
    d_id = ctx.triggered_id # determine which data upload triggered save

    # determine the id source and update sesh-id as necessary
    if d_id == 'local-id':
        return local
    elif d_id == 'local-id2':
        return local2
    else:
        return no_update

# update store of general info depending on upload format
@app.callback(
    Output('general-info', 'data'),
    Output('check', 'data'),
    [Input('gen-info1', 'data'),
    Input('gen-info2', 'data')],
    prevent_initial_call = True
)
def save_gen(gen1, gen2):
    d_id = ctx.triggered_id # determine which data upload triggered save
    storage = list() # empty dict to store datail a

    if d_id == 'gen-info1': # if triggered by reload
        storage = tuple(gen1)
        return storage, True
    elif d_id == 'gen-info2': # if triggered by data revertion
        storage = tuple(gen2)
        return storage, no_update


if __name__ == '__main__':
    app.run_server(debug=True)
    #app.run_server(debug=False, port=5433, host='0.0.0.0')
    #test

