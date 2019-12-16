import os
import sqlite3
f = open("regions.txt", "r")

list = f.read()
list = list.splitlines()
print(list)
for da in list:
    data = da.split('.')
    print(da)
    print(data)
    connect = sqlite3.connect('bcbot.db')
    c = connect.cursor()
    #c.execute("INSERT INTO region(region_id,region_name) VALUES({},'{}')".format(data[0],data[1]))
    #connect.commit()