import os
import sqlite3
import numpy as np
table_ind = 1
def derivative(l_param):
    a, b = l_param[0], l_param[1]
    e = 0.0001
    da, pva = 1, 0
    va = (sum_of_deviations([a+da, b])-sum_of_deviations(l_param)) / da
    while (abs(va-pva)>e):
        pva = va
        da *= 0.5
        va = (sum_of_deviations([a+da, b])-sum_of_deviations(l_param)) / da
    db, pvb = 1, 0
    vb = (sum_of_deviations([a, b+db]) - sum_of_deviations(l_param)) / db
    while (abs(vb - pvb) > e):
        pvb = vb
        db *= 0.5
        vb = (sum_of_deviations([a, b+db]) - sum_of_deviations(l_param)) / db
    return [va, vb]
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
def func(l_param, x2):
    x1 = 1 - x2
    return rt * x1 * x2*(x1 * l_param[0] + x2 * l_param[1])
def sum_of_deviations(l_param):
    sum = 0
    for i in range(0, len(l_points)):
        x2, ge = l_points[i][0], l_points[i][1]
        sum += (func(l_param, x2) - ge) ** 2
    return sum / len(l_points)


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
db_path = os.path.join(parent_dir, 'db.sqlite3')
l_points, temp_list = get_data_from_db(db_path)
rt = temp_list[table_ind] * 8.314462618    # температура на газовую постоянную
l_param = [10, 10]
eps = 0.0001
d = 0.01
flag = True
count, count_iter = 0, 0
iter_max = 10
const_learning = 1.01
while flag:
    pa, pb = l_param[0], l_param[1]
    pda, pdb = derivative([pa, pb])
    da, db = derivative(l_param)
    if ((da**2+db**2)**0.5) < eps:
        break
    l_param[0], l_param[1] = pa - da*d/((da**2+db**2)**0.5), pb - db*d/((da**2+db**2)**0.5)
    if abs(sum_of_deviations(l_param) - sum_of_deviations([pa, pb])) < eps:
        d *= 0.5
        if d < 10e-5:
            flag = False
    count_iter += 1
    count += 1

gradient_a, gradient_b = l_param[0], l_param[1]
