# Table_Creator.py
# Truze.AI
#
# Created by Shun Sakai and Joseph Fernando on April 15, 2023
# Copyright © 2023 Shun Sakai. All rights reserved.
#
# THE CONTENTS OF THIS PROJECT ARE PROPRIETARY AND CONFIDENTIAL.
# UNAUTHORIZED COPYING, TRANSFERRING OR REPRODUCTION OF THE CONTENTS OF THIS PROJECT, VIA ANY MEDIUM IS STRICTLY PROHIBITED.

from unicodedata import name


def isEnglish(value):
        for char in value:
            if char.isnumeric():
                return False
        return True

def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def defineColumns(file, hash):
    #starting string for SQL statement
    statement = "CREATE TABLE IF NOT EXISTS %s (" %(hash)
    nan_count = 0
    #extracts column names

    titles = list(file[0].keys())

    #contains all of the types of the columns
    types_out = []
    #contains a string with the names of all the columns
    names_out = ""

    #finds type using max value of column
    for key in titles:
        value = str(file[0][key])
        '''
        if isEnglish(value) and value.lower() != "none" and value != np.NaN and value.lower() != "nan" and value.lower() != "nan\n" and value != "":
            types_out.append("TEXT")
        else:
        '''
        global max_val
        max_val = -1
        try:
            for row in file:
                current = str(row[key])
                if current.lower() == "none" or current.lower() == "nan" or current.lower() == "nan\n" or current.lower()=="":
                    continue
                else:
                    if "." in current:
                        if float(current) > max_val:
                            max_val = float(current)
                    else:
                        if int(current) > max_val:
                            max_val = int(current)
            if isinstance(max_val, float):
                types_out.append("REAL")
            elif 0 <= max_val <= 1:
                types_out.append("BOOL")
            elif max_val== -1:
                types_out.append("TEXT")
            else:
                types_out.append("INTEGER")
        except:
            types_out.append("TEXT")
        
        max_val = -1
    for i in range(0, len(titles)):
        
        titles[i] = str(titles[i])
        titles[i] = titles[i].strip()
        titles[i] = titles[i].replace(" ","_")
        titles[i] = titles[i].replace("-","_")
        titles[i] = titles[i].replace("/","_")
        if '#' in titles[i]:
            titles[i] = "\"" + titles[i] + "\"" 
        if i == len(titles) - 1:
            if titles[i] == 'nan':
                statement += "Unnamed_" + str(nan_count)
                statement += " "
                statement += types_out[i]
                names_out += "Unnamed_" + str(nan_count)
                nan_count +=1
            else:
                statement += titles[i]
                statement += " "
                statement += types_out[i]
                names_out += titles[i]
        else:
            if titles[i] == 'nan':
                statement += "Unnamed_" + str(nan_count)
                statement += " "
                statement += types_out[i]
                statement += ", "
                names_out += "Unnamed_" + str(nan_count)
                names_out += ", "
                nan_count +=1
            else:
                statement += titles[i]
                statement += " "
                statement += types_out[i]
                statement += ", "
                names_out += titles[i]
                names_out += ", "
    statement += ");"
    return statement, types_out, names_out
