# Table_Populator.py
# Truze.AI
#
# Created by Shun Sakai and Joseph Fernando on April 15, 2023
# Copyright © 2023 Shun Sakai. All rights reserved.
#
# THE CONTENTS OF THIS PROJECT ARE PROPRIETARY AND CONFIDENTIAL.
# UNAUTHORIZED COPYING, TRANSFERRING OR REPRODUCTION OF THE CONTENTS OF THIS PROJECT, VIA ANY MEDIUM IS STRICTLY PROHIBITED.

from database import Table_Creator

#this script reads the rest of the dataset and returns another SQL statement that inserts the data into the dataset
def populateTable(file, info):
    # return types, titles, and hash from info
    types = info[1]
    titles = info[2]
    hashStr = info[3]

    # create base string
    script = "INSERT INTO " + hashStr + "(" + titles
    script += ") SELECT * FROM (VALUES"

    for dictionary in file:
        script += "("
        for i in range(0,len(dictionary)):
            value = str(list(dictionary.values())[i]).lower()

            if i == len(dictionary)-1:

                if value.lower() == "nan" or value.lower() == "nan\n" :
                    script += "NULL), "
                else:
                    if types[i] == "BOOL":
                        if value == "1":
                            script += "TRUE), "
                        else:
                            script += "FALSE), "
                    elif types[i] == "TEXT":
                        value = value.replace("'","''")
                        script += "'" + value + "'), "
                    else:
                        script += value
                        script += "), "
            else:
                if value.lower() == "nan" or value.lower() == "nan\n":
                    script += "NULL, "
                else:
                    if types[i] == "BOOL":
                        if value == "1":
                            script += "TRUE, "
                        else:
                            script += "FALSE, "
                    elif types[i] == "TEXT":
                        value = value.strip()
                        value = value.replace("'","''")
                        script += "'" + value + "', "
                    else:
                        script += value
                        script += ", "
    script = script[:-2]
    #print("script", str(script))
    script += ") as val WHERE NOT EXISTS (SELECT * FROM " + hashStr + ");"
    
    #print("script", str(script))
    return script
