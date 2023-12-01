# SQLTest.py
# Truze.AI
#
# Created by Shun Sakai and Joseph Fernando on May 14, 2023
# Copyright © 2023 Shun Sakai. All rights reserved.
#
# THE CONTENTS OF THIS PROJECT ARE PROPRIETARY AND CONFIDENTIAL.
# UNAUTHORIZED COPYING, TRANSFERRING OR REPRODUCTION OF THE CONTENTS OF THIS PROJECT, VIA ANY MEDIUM IS STRICTLY PROHIBITED.

import psycopg2
import pandas as pd
import plotly.graph_objects as go

from pages import configdb

# Obtain the configuration parameters
params = configdb.config()
# Connect to the PostgreSQL database
conn = psycopg2.connect(**params)
# Create a new cursor
curr = conn.cursor()

# clear chains for find and replace feature
def clearReplaceChains(keys,values):
    for i in range(len(values) - 2, -1, -1):
        value = values[i]
        if value in keys[i + 1:]:
            values[i] = values[len(values) - list(reversed(keys)).index(value) - 1]
        #print(keys, values)

    for j in range(len(values) - 1, -1, -1):
        if keys[j] == values[j]:
            keys.pop(j)
            values.pop(j)

    dups = [i for i, key in enumerate(keys) if key in keys[:i]]
    for val in sorted(dups, reverse=True):
        del keys[val]
        del values[val]

    return dict(zip(keys, values))

# convert input to a dictionary
def convertToDict(find, replace, column):
    dictionary = {}
    for i in range(len(find)):
        if column[i] in dictionary.keys():
            dictionary[column[i]][find[i]] = replace[i]
        else:
            dictionary[column[i]] = {find[i]: replace[i]}
    return dictionary

# find and replace code 
def findAndReplace(find, replace, column, hashCode):
    # setup config to make sql calls
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()
    
    log = convertToDict(find, replace, column)

    refine = log
    script = ""

    for key in log.keys():
        typeFinder = "SELECT pg_typeof(%s) FROM %s WHERE id = 0;" %(str(key),str(hashCode))
        curr.execute(typeFinder)
        colType = curr.fetchone()[0]
        script = ""
        noQuotes = False

        # clear the replace chain in the specified column
        log[key] = clearReplaceChains(find, replace)

        # check if value is an int and chooses to put quotes
        if colType == "integer" or colType == "boolean":
            noQuotes = True

        if len(log[key]) == 1 and "NULL" in log[key]:
            if noQuotes:
                script += "COALESCE(" + key + ", " + str(list(log[key].values())[0]) + ")"
                refine[key] = script
            else:
                script += "COALESCE(" + key + ", '" + str(list(log[key].values())[0]) + "')"
                refine[key] = script
        elif len(log[key]) > 1 and "NULL" in log[key]:
            script += "CASE " + key
            for seckey in log[key].keys():
                if seckey != "NULL":
                    if noQuotes:
                        script += " WHEN " + str(seckey) + " THEN " + str(log[key][seckey])
                    else:
                        if str(log[key][seckey]) == "NULL":
                            script += " WHEN '" + str(seckey) + "' THEN NULL"
                        else:
                            script += " WHEN '" + str(seckey) + "' THEN " + "'" + str(log[key][seckey]) + "'"
            if noQuotes:
                script += " ELSE COALESCE(" + key + "," + str(log[key]["NULL"]) + ") END"
            else:
                script += " ELSE COALESCE(" + key + ",'" + str(log[key]["NULL"]) + "') END"
            refine[key] = script
        elif "NULL" not in log[key]:
            script += "CASE " + key
            for seckey in log[key].keys():
                if seckey != "NULL":
                    if noQuotes:
                        script += " WHEN " + str(seckey) + " THEN " + str(log[key][seckey])
                    else:
                        script += " WHEN '" + str(seckey) + "' THEN '" + str(log[key][seckey]) + "'"
            script += " ELSE " + key + " END"
            refine[key] = script

     # cursor statements
    conn.commit()
    curr.close()
    conn.close()

    return refine

    """
    sanitize make sure there are only ints and "None"
        if there is only nan then only do a coalesce
            SELECT COALESCE(column[0], replace[0]) FROM test1;
        if there is nan and numbers then do a case and coalesce in the else
            SELECT CASE column[
        if there is only numbers then do just a case
    """

def findAndReplaceInd(find, replace, column, info):
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()

    frdic = {}
    result = {}
    temp = " CASE id "
    script = ""
    
    #casting not needed for boolean
    #casting not needed for real

    for i in range(len(column)):
        if str(column[i]+",") not in frdic.keys():
            frdic[str(column[i])+","] = [i]
        else:
            print("find", find)
            frdic[str(column[i])+ ","].append(i)

    # store rows of changes for each column
    row_dic = {}

    # create a dictionary that holds for every col,row cell all the changes that have been made to it
    for key in frdic.keys():
        for num in frdic[key]:
            new_key = "col: " + str(key)[:-1] + "," + " row: " + str(find[num]) # create a key with id col,row
            if new_key not in row_dic.keys(): # add the index of find that holds changes to that specific cell
                row_dic[new_key] = [num]
            else:
                row_dic[new_key].append(num)

    # check if there are multiple changes to a cell
    for key in row_dic.keys():
        if len(row_dic[key]) > 1:
            most_recent = max(row_dic[key]) # get the index of the most recent change
            col = key.split(",")[0].split(":")[1].strip() + "," # get the column name
            row_dic[key] = [item for item in row_dic[key] if item != most_recent] # remove the most recent change from the list of changes
            rem_list = [item for item in frdic[str(col)] if item not in row_dic[key]] # remove changes other than the most recent change
            frdic[str(col)] = rem_list # update the list of changes for that column
            

    # add when then statements where necessary
    for item in frdic.keys():
        for num in frdic[item]:
            curr.execute("SELECT pg_typeof(%s) FROM %s WHERE id = 0;" %(str(item)[:-1],str(info[3])))
            colType = curr.fetchall()[0]
            if str(colType).lower() == 'text':
                temp += "WHEN " + str(find[num]) + " THEN '" + str(replace[num]) + "' "
            else:
                temp += "WHEN " + str(find[num]) + " THEN " + str(replace[num]) + " "
        temp += "ELSE "+ str(item)[:-1] +" END, "
        result[item] = temp
        temp = "CASE id "

    conn.commit()
    curr.close()
    conn.close()

    return result
                
#deletes rows and columns from the col_num and row_num arrays
def editTable(col_num, row_num, col_info, dictionary, f_i, r_i, c_fri):
    titles = col_info[2].split()
    hashStr = col_info[3]
    alias = titles
    hidden = ""
    id_col = 'id,'
    script = "SELECT "
    x = list()
    second_table = col_info[2].split()
    #remove id column if it exists
    if id_col in alias: alias.remove(id_col)
    if id_col in second_table: second_table.remove(id_col)

    #remove any columns that are in the list to be deleted
    for i in range(len(col_num), 0, -1):
        alias.pop(col_num[i - 1])
        second_table.pop(col_num[i - 1])
    
    second_table = ' '.join(second_table)
 
    #remove any rows that are in the list to be deleted
    for j in range(len(row_num)):
        if j == len(row_num)-1:
            hidden += str(row_num[j])
        else:
            hidden += str(row_num[j])
            hidden += ","

    selected = (item for item in alias if item != "id")  

    for item in selected:
        script += item + " "
    for key in dictionary.keys():
        if key in script:
            script = script.replace(key + ",", dictionary[key]+",")
    #script = script[:-1]
   # script += " FROM test1 WHERE id IN("
    script += "FROM " + hashStr

    if len(row_num) != 0: 
        script += " WHERE id NOT IN("
        script += hidden
        script += ");"
    else:
        script += ";"


    individuals = findAndReplaceInd(f_i,r_i,c_fri,col_info)


    if len(f_i) > 0:
        for item in individuals.keys():
            second_table = str(second_table).replace(str(item), individuals[item])

        script = 'SELECT ' + second_table + " FROM (" + script[:-1] + ") AS TMP"
        script = script.replace("FROM (SELECT", "FROM (SELECT id, ")
        return script
    else: 
        return script

    
def getIDTable(col_num, row_num, col_info, dictionary, f_i, r_i, c_fri):
    titles = col_info[2].split()
    hashStr = col_info[3]
    alias = titles
    hidden = ""
    id_col = 'id,'
    script = "SELECT "
    x = list()
    second_table = col_info[2].split()
    if id_col in second_table: second_table.remove(id_col)

    #remove any columns that are in the list to be deleted
    for i in range(len(col_num), 0, -1):
        alias.pop(col_num[i - 1] + 1)
        second_table.pop(col_num[i - 1])
    
    second_table = ' '.join(second_table)
 
    #remove any rows that are in the list to be deleted
    for j in range(len(row_num)):
        if j == len(row_num)-1:
            hidden += str(row_num[j])
        else:
            hidden += str(row_num[j])
            hidden += ","

    selected = (item for item in alias)  

    for item in selected:
        script += item + " "
    for key in dictionary.keys():
        if key in script:
            script = script.replace(key + ",", dictionary[key]+",")
   # script += " FROM test1 WHERE id IN("
    script += "FROM " + hashStr

    if len(row_num) != 0: 
        script += " WHERE id NOT IN("
        script += hidden
        script += ");"
    else:
        script += ";"

    individuals = findAndReplaceInd(f_i,r_i,c_fri,col_info)

    if len(f_i) > 0:
        for item in individuals.keys():
            second_table = str(second_table).replace(str(item), individuals[item])

        script = 'SELECT id,' + second_table + " FROM (" + script[:-1] + ") AS TMP"
        script = script.replace("FROM (SELECT", "FROM (SELECT")
        ###print("final", script)
        return script
    else: 
        ###print("final", script)
        return script

# push changes to the sql database
def pushChanges(user_id, action_id, change, hash_code):
    """
    action_id glossary:
        1 = Delete Row (Not Used Anymore)
            Provide Int
        2 = Delete Column
            Provide Int
        3 = Find and Replace
            Provide Array/List formatted as follows:
                [ Value to find, Value to replace, Name of Column to Operate on ]
        4 = Find and Replace INDIVIDUAL
            Provide Array/List formatted as follows:
                [id of entry, Value to replace with, Name of Column to operate on]
        5 = Delete Multiple Rows (Delete-Nans, Delete-Dups, Delete-Range)
        6 = Delete Multiple Columns
    """

    # setup config to make sql calls
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()

    curr.execute("SELECT COUNT(*) FROM CHANGELOG WHERE S_ID = %s AND H_C = '%s'" % (str(user_id), str(hash_code)))

    if list(curr.fetchone())[0] < 1:
        curr.execute("INSERT INTO CHANGELOG VALUES (" + str(user_id) + ", '{}', '{}', '{}', '{}', '{}','{}','%s','{}','{}','{}', '{}');" % (str(hash_code)))
        conn.commit()
    if action_id == 1:
        curr.execute("UPDATE CHANGELOG SET d_r = array_append(d_r, %s), a_t = array_append(a_t,1) WHERE s_id = %s AND h_c = '%s';" % (change, str(user_id), str(hash_code)))
    elif action_id == 2:
        change = "'" + str(change) + "'"
        curr.execute("UPDATE CHANGELOG SET d_c = array_append(d_c, %s), a_t = array_append(a_t,2) WHERE s_id = %s AND h_c = '%s';" % (change, str(user_id), str(hash_code)))
    elif action_id == 3:
        change[0] = "'" + change[0] + "'"
        change[1] = "'" + change[1] + "'"
        curr.execute("UPDATE CHANGELOG SET f_v = array_append(f_v, %s), a_t = array_append(a_t,3) WHERE s_id = %s AND h_c = '%s';" % (change[0], str(user_id), str(hash_code)))
        curr.execute("UPDATE CHANGELOG SET r_v = array_append(r_v, %s) WHERE s_id = %s AND h_c = '%s';" % (change[1],str(user_id), str(hash_code)))
        change[2] = "'" + change[2] + "'"
        curr.execute("UPDATE CHANGELOG SET c_fr = array_append(c_fr, %s) WHERE s_id = %s AND h_c = '%s';" % (change[2], str(user_id), str(hash_code)))
    elif action_id == 4:
        print("change", change)
        change[0] = "'" + change[0] + "'"
        change[1] = "'" + change[1] + "'"
        curr.execute("UPDATE CHANGELOG SET f_i = array_append(f_i, %s), a_t = array_append(a_t,4) WHERE s_id = %s AND h_c = '%s';" % (change[0], str(user_id), str(hash_code)))
        curr.execute("UPDATE CHANGELOG SET r_i = array_append(r_i, %s) WHERE s_id = %s AND h_c = '%s';" % (change[1],str(user_id), str(hash_code)))
        change[2] = "'" + change[2] + "'"
        curr.execute("UPDATE CHANGELOG SET c_fri = array_append(c_fri, %s) WHERE s_id = %s AND h_c = '%s';" % (change[2], str(user_id), str(hash_code)))

        # ##change
        # curr.execute("UPDATE CHANGELOG SET f_i = %s, a_t = array_append(a_t,4) WHERE s_id = %s AND h_c = '%s';" % (change[0], str(user_id), str(hash_code)))
        # curr.execute("UPDATE CHANGELOG SET r_i = %s WHERE s_id = %s AND h_c = '%s';" % (change[1],str(user_id), str(hash_code)))
        # curr.execute("UPDATE CHANGELOG SET c_fri = %s WHERE s_id = %s AND h_c = '%s';" % (change[2], str(user_id), str(hash_code)))
    elif action_id == 5:
        curr.execute("UPDATE CHANGELOG SET d_r = array_cat(d_r, %s), a_t = array_append(a_t,5) WHERE s_id = %s AND h_c = '%s';" % (change, str(user_id), str(hash_code)))
        curr.execute("UPDATE CHANGELOG SET d_rc = array_append(d_rc, %s) WHERE s_id = %s AND h_c = '%s';" % (len(change.split(', ')), str(user_id), str(hash_code)))
    elif action_id == 6:
        curr.execute("UPDATE CHANGELOG SET d_c = array_cat(d_c, %s), a_t = array_append(a_t,6) WHERE s_id = %s AND h_c = '%s';" % (change, str(user_id), str(hash_code)))
        curr.execute("UPDATE CHANGELOG SET d_cc = array_append(d_cc, %s) WHERE s_id = %s AND h_c = '%s';" % (len(change.split(', ')), str(user_id), str(hash_code)))

        
    conn.commit()

# revert edits from previous sessions
def revertAllEdits(general_info, u_id):
    # setup config to make sql calls
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()

    # store passed column + create list to store data
    data = list()
    u_id = str(u_id)
    find_vals = list()
    replace_vals = list()
    title_vals = list()
    row_vals = list()
    col_vals = list()
    findi_vals = list()
    replacei_vals = list()
    c_vals = list()
    hash_code = general_info[3]

    # fetch any previous changes
    curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = " + str(u_id) + ";")
    changesMade = curr.fetchone()

    # fetch any previous find and replace
    curr.execute("SELECT C_FR FROM CHANGELOG WHERE S_ID = " + str(u_id) + ";")
    replacesMade = curr.fetchone()

    # fetch any previous find and replace individual
    curr.execute("SELECT C_FRI FROM CHANGELOG WHERE S_ID = " + str(u_id) + ";")
    indReplacesMade = curr.fetchone()

    # if there were replaces
    if replacesMade is not None:
        select_indices = [i for i, j in enumerate(changesMade[5])] # find indicies to which the find and replace hss been modified previously  if j == selected
        find_vals = [changesMade[3][i] for i in select_indices] # add find values to list
        replace_vals = [changesMade[4][i] for i in select_indices] # add replace values to list
        title_vals = [changesMade[5][i] for i in select_indices] # add column for find and replace to list

    # if there were individual replaces
    if indReplacesMade is not None:
        sel_indices = [i for i, j in enumerate(changesMade[10])] # find indicies to which the find and replace hss been modified previously  if j == selected
        findi_vals = [changesMade[8][i] for i in sel_indices] # add find values to list
        replacei_vals = [changesMade[9][i] for i in sel_indices] # add replace values to list
        c_vals = [changesMade[10][i] for i in sel_indices] # add column for find and replace to list

    # if there were previous changes
    if changesMade is not None:
        col_vals = list(map(int, changesMade[1])) # add column for del col
        row_vals = list(map(int, changesMade[2])) # add rows for del row

    # perform sql queries and save changes to changelog
    dic = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=hash_code)
    curr.execute(editTable(col_num=col_vals, row_num=row_vals, col_info=general_info, dictionary=dic, f_i=findi_vals, r_i=replacei_vals, c_fri=c_vals))

    # fetch data from call and create dataframe
    titles = general_info[2].split(", ")
    titles.pop(0) # remove id column
    title_vals = [titles[i] for i, j in enumerate(titles) if i in col_vals] # find values to remove from titles list
    titles = [t for t in titles if t not in title_vals] # return only remaining titles

    # add titles to data
    rows = curr.fetchall()
    for row in rows:
        data.append(list(row))

    # cursor statements
    conn.commit()
    curr.close()
    conn.close()

    # data to return
    df = pd.DataFrame.from_records(data, columns=titles)
    dff = df.to_dict('records') # create new dictionary to return to table

    return df, dff

# revert edits from previous sessions
def revertColEdits(general_info):
    # setup config to make sql calls
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()

    # store passed column + create list to store data
    data = list()
    u_id = str(general_info[5])
    find_vals = list()
    replace_vals = list()
    title_vals = list()
    row_vals = list()
    col_vals = list()
    findi_vals = list()
    replacei_vals = list()
    c_vals = list()
    hash_code = general_info[3]

    # fetch any previous changes
    curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = %s AND h_c = '%s';" % (str(u_id), hash_code))
    changesMade = curr.fetchone()

    # fetch any previous find and replace
    curr.execute("SELECT C_FR FROM CHANGELOG WHERE S_ID = %s AND h_c = '%s';" % (str(u_id), hash_code))
    replacesMade = curr.fetchone()

    # fetch any previous find and replace individual
    curr.execute("SELECT C_FRI FROM CHANGELOG WHERE S_ID = " + str(u_id) + ";")
    indReplacesMade = curr.fetchone()

    # if there were replaces
    if replacesMade is not None:
        select_indices = [i for i, j in enumerate(changesMade[5])] # find indicies to which the find and replace hss been modified previously  if j == selected
        find_vals = [changesMade[3][i] for i in select_indices] # add find values to list
        replace_vals = [changesMade[4][i] for i in select_indices] # add replace values to list
        title_vals = [changesMade[5][i] for i in select_indices] # add column for find and replace to list

    # if there were individual replaces
    if indReplacesMade is not None:
        sel_indices = [i for i, j in enumerate(changesMade[10])] # find indicies to which the find and replace hss been modified previously  if j == selected
        findi_vals = [changesMade[8][i] for i in sel_indices] # add find values to list
        replacei_vals = [changesMade[9][i] for i in sel_indices] # add replace values to list
        c_vals = [changesMade[10][i] for i in sel_indices] # add column for find and replace to list

    # if there were previous changes
    if changesMade is not None:
        col_vals = list(map(int, changesMade[1])) # add column for del col
        row_vals = list(map(int, changesMade[2])) # add rows for del row

    # perform sql queries and save changes to changelog
    dic = findAndReplace(find=find_vals, replace=replace_vals, column=title_vals, hashCode=hash_code)
    curr.execute(editTable(col_num=col_vals, row_num=row_vals, col_info=general_info, dictionary=dic, f_i=findi_vals, r_i=replacei_vals, c_fri=c_vals))

    # fetch data from call and create dataframe
    titles = general_info[2].split(", ")
    titles.pop(0) # remove id column
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
    dff = df.to_dict('records') # create new dictionary to return to table
    dtf = df[[general_info[4]]] # extract column being viewed from df
    newData= dtf.to_dict('records') # create new dictionary to return to table
    columns = [{'name': str(i), 'id': str(i), "selectable": True} for i in dtf.columns]

    return newData, columns, dff

def pullChanges(user_id, hash_code):
    # setup config to make sql calls
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()

    curr.execute("SELECT * FROM CHANGELOG WHERE s_id = %s AND h_c = '%s'" % (str(user_id), hash_code))
    changes = curr.fetchone()
    #hash_code = hash_code.lower()
    #print("changes",changes)
    if changes is None:
        output = 'No Changes Made'
    else:
        output = "User ID: " + str(user_id) + "\n"
        output += "***\nPlease keep track of your user id in order to save progress on our website.\nWhen you reopen the website, copy this user id into the textbox and all of your progress will be restored.\n***\n"
        if len(changes[1]) > 0:
            output += "\nColumns deleted: \n \t"
            for col in changes[1]:
                output += col + "\n\t"
        if len(changes[2]) > 0:
            output += "\nRows deleted: \n \t"
            for row in changes[2]:
                output += str(row) + ","
            output = output[:-1] + "\n\n"
        if len(changes[3]) > 0:
            output += "Find and Replace:\n\t"

            for i in range(0, len(changes[3])):
                output+= "All instances of %s replaced with %s in column %s\n\t" % (str(changes[3][i]), str(changes[4][i]), str(changes[5][i]))
        if len(changes[8]) > 0:
            for j in range(0, len(changes[8])):
                output += "Row ID %s in column %s replaced with %s\n\t" %(str(changes[8][j]),str(changes[10][j]),str(changes[9][j]))

    # cursor statements
    conn.commit()
    curr.close()
    conn.close()
    
    return output

# check if the user is a previous user (will change later to check username in db)
def previousUser(u_id):
    # setup config to make sql calls
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()

    user_id = str(u_id)
    curr.execute("SELECT * FROM CHANGELOG WHERE s_id = %s;" % (user_id))
    changes = curr.fetchone()

    # cursor statements
    conn.commit()
    curr.close()
    conn.close()

    # need to cross reference dataset id as well
    if changes is None:
        return False
    else:
        return True

# function for undo
def undoButton(user_id, hash_code):
    # setup config to make sql calls
    params = configdb.config()
    conn = psycopg2.connect(**params)
    curr = conn.cursor()

    # var to store if the change is the last change left
    last = True
    last2 = False

    print("user_id", user_id)
    # return all changes
    curr.execute("SELECT * FROM CHANGELOG WHERE S_ID = %s AND H_C = '%s';" % (user_id, hash_code))

    # check if the undo removes all changes from changelog
    current = curr.fetchone()
    if current is None: return

    curr.execute("SELECT a_t[array_upper(a_t, 1)] FROM CHANGELOG WHERE S_ID = %s AND H_C = '%s';" % (user_id, hash_code))
    action_id = curr.fetchone()[0]
    if action_id == 1:
        curr.execute("UPDATE CHANGELOG SET d_r = d_r[0: array_length(d_r, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET a_t = a_t[0: array_length(a_t, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
    elif action_id == 2:
        curr.execute("UPDATE CHANGELOG SET d_c = d_c[0: array_length(d_c, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET a_t = a_t[0: array_length(a_t, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
    elif action_id == 3:
        curr.execute("UPDATE CHANGELOG SET f_v = f_v[0: array_length(f_v, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET r_v = r_v[0: array_length(r_v, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET c_fr = c_fr[0: array_length(c_fr, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET a_t = a_t[0: array_length(a_t, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
    elif action_id == 4:
        curr.execute("UPDATE CHANGELOG SET f_i = f_i[0: array_length(f_i, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET r_i = r_i[0: array_length(r_i, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET c_fri = c_fri[0: array_length(c_fri, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET a_t = a_t[0: array_length(a_t, 1)-1 ] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
    elif action_id == 5:
        # fetch number of items to remove
        curr.execute("SELECT d_rc FROM CHANGELOG WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        ret = curr.fetchone()[0]
        print("ret", ret)
        count = ret[len(ret)-1]

        print("count fertch", count)

        # normal scripts to execute
        curr.execute("UPDATE CHANGELOG SET d_r = d_r[0: array_length(d_r, 1)-%s] WHERE s_id = %s AND H_C = '%s';" % (count, user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET d_rc = d_rc[0: array_length(d_rc, 1)-1] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET a_t = a_t[0: array_length(a_t, 1)-1] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
    elif action_id == 6:
        # fetch number of items to remove
        curr.execute("SELECT d_cc FROM CHANGELOG WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        ret = curr.fetchone()[0]
        print("ret", ret)
        count = ret[len(ret)-1]

        print("count fertch", count)

        # normal scripts to execute
        curr.execute("UPDATE CHANGELOG SET d_c = d_c[0: array_length(d_c, 1)-%s] WHERE s_id = %s AND H_C = '%s';" % (count, user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET d_cc = d_cc[0: array_length(d_cc, 1)-1] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
        curr.execute("UPDATE CHANGELOG SET a_t = a_t[0: array_length(a_t, 1)-1] WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
    conn.commit()

    # check if it is the last change
    curr.execute("SELECT D_C, D_R, F_V, R_V, C_FR, F_I, R_I, C_FRI FROM CHANGELOG WHERE S_ID = %s AND H_C = '%s';" % (user_id, hash_code))
    changes = curr.fetchone()

    for v in changes:
        if len(v) > 0: last = False 

    if last: curr.execute("DELETE FROM CHANGELOG WHERE s_id = %s AND H_C = '%s';" % (user_id, hash_code))
    conn.commit()

def blankFig():
    fig = go.Figure(go.Scatter(x=[], y = []))
    fig.update_layout(template = None)
    fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
    fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
    return fig

def getId(row_id_name, df, df_previous):
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

    return changes


def type_check(type, replace_val):
    nulls = ['nan', 'None', "None"]

    if replace_val in nulls:
        return (True, replace_val)
    else:
        if(type == "BOOL" and replace_val == '0'):
            replace_val = False
            print("x", replace_val)
            
        if type == "INTEGER":
            try:
                x = int(replace_val)
            except:
                return (False, replace_val)
        elif type == "REAL":
            try:
                x = float(replace_val)
            except:
                return (False, replace_val)
        elif type == "BOOL":
            try:
                x = bool(replace_val)
            except:
                return (False, replace_val)
        elif type == "TEXT":
            try:
                x = str(replace_val)
            except:
                return (False, replace_val)
            
        if(type == "BOOL" and replace_val != False):
            replace_val = True

        return (True, replace_val)
    

def prev_check(curr_col, curr_row, curr_replace, f_i, r_i, c_i):

    for i in range(len(f_i)):
        col = c_i[i]
        find = f_i[i]

        if (col == curr_col) and (find == curr_row) and (r_i[i] == "NULL"):
            return (True, i)
        
    return (False, 0)

def get_diff(a: list, b: list) -> list:
    return list(set(a) ^ set(b))



