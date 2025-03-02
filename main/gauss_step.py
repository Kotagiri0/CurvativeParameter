import os
import sqlite3
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
a=1
b=1
eps = 0.0000001
flag = True
count = 0
f_stepa = True
f_stepb = True
b_stepa = False
b_stepb = False
count_iter_a = 0
count_iter_b = 0
const_learning = 1.01
flag_ch = False
da, db = 0.0001, 0.0001
count_iter = 0
iter_max = 10
while flag:
    pa, pb = a, b
    if count_iter_a >= iter_max:
        da *= const_learning
    else:
        da = 0.0001
    if count_iter_b >= iter_max:
        db *= const_learning
    else:
        db = 0.0001
    if sum_of_deviations(a + da, b) < sum_of_deviations(a, b):
        a += da
        if b_stepa:
            f_stepa = True
            b_stepa = False
            count_iter_a = 0
        count_iter_a += 1
    elif sum_of_deviations(a - da, b) < sum_of_deviations(a, b):
        a -= da
        if f_stepa:
            f_stepa = False
            b_stepa = True
            count_iter_a = 0
        count_iter_a += 1
    if sum_of_deviations(a, b + db) < sum_of_deviations(a, b):
        b += db
        if b_stepb:
            f_stepb = True
            b_stepb = False
            count_iter_b = 0
        count_iter_b += 1
    elif sum_of_deviations(a, b - db) < sum_of_deviations(a, b):
        b -= db
        if f_stepb:
            f_stepb = False
            b_stepb = True
            count_iter_b = 0
        count_iter_b += 1
    count += 1
    flag = abs(sum_of_deviations(a, b) - sum_of_deviations(pa, pb)) > eps

gauss_step_a = a
gauss_step_b = b