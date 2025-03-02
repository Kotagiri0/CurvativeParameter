import os
import sqlite3
import random
from math import exp
import numpy as np
table_ind = 1
def get_data_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f""" SELECT mp.x_value, mp.y_value FROM main_table_points mtp JOIN main_point mp ON mtp.point_id = mp.id WHERE mtp.table_id = {table_ind+1} """
    cursor.execute(query)
    rows = cursor.fetchall()
    points_list = [(row[0], row[1]) for row in rows]
    cursor.execute('SELECT temperature FROM main_table')
    temp_rows = cursor.fetchall()
    temp_list = [temp[0] for temp in temp_rows]
    cursor.close()
    conn.close()
    return points_list, temp_list

def func(a, b, x2):
    rt = temp_list[table_ind]*8.314462618    # температура на газовую постоянную
    x1 = 1 - x2
    return rt * x1 * x2*(x1 * a + x2 * b)



def sum_of_deviations(a, b):
    sum = 0
    for i in range(0, len(l_points)):
        x2 = l_points[i][0]
        ge = l_points[i][1]
        sum += (func(a, b, x2) - ge) ** 2
    return sum / len(l_points)


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
db_path = os.path.join(parent_dir, 'db.sqlite3')
l_points, temp_list = get_data_from_db(db_path)

a=2
b=2

eps = 0.0000001
flag = True

ans = sum_of_deviations(a, b)

t = 1.0

count = 0

while flag:
    t *= 0.9999
    otzh_a = random.uniform(0, 10)
    otzh_b = random.uniform(0, 10)
    val = sum_of_deviations(otzh_a, otzh_b)
    if t > eps and (val <= ans or random.uniform(0, 1) < exp((ans - val) / t)):
        ans = val
        a = otzh_a
        b = otzh_b

    pa, pb = a, b
    da, db = 0.00001, 0.00001

    if sum_of_deviations(a + da, b) < sum_of_deviations(a, b):
        a += da
    elif sum_of_deviations(a - da, b) < sum_of_deviations(a, b):
        a -= da

    if sum_of_deviations(a, b + db) < sum_of_deviations(a, b):
        b += db
    elif sum_of_deviations(a, b - db) < sum_of_deviations(a, b):
        b -= db

    flag = abs(sum_of_deviations(a, b) - sum_of_deviations(pa, pb)) > eps
    count+=1
otzhig_a = a
otzhig_b = b
