import random
from math import exp

def func(a, b, x2, tables, table_ind):
    rt = tables[table_ind].temperature*8.314462618    # температура на газовую постоянную
    x1 = 1 - x2
    return rt * x1 * x2*(x1 * a + x2 * b)

def sum_of_deviations(a, b, tables, table_ind, l_points):
    sum = 0
    for i in range(0, len(l_points)):
        x2 = l_points[i][0]
        ge = l_points[i][1]
        sum += (func(a, b, x2, tables, table_ind) - ge) ** 2
    return sum / len(l_points)
def otzhig(tables, table_ind):
    l_points = []
    for point in tables[table_ind].points.all():
        l_points.append((point.x_value, point.y_value))
    a, b = 2, 2

    eps = 0.0000001
    flag = True

    ans = sum_of_deviations(a, b, tables, table_ind, l_points)

    t = 1.0

    count = 0

    while flag:
        t *= 0.9999
        otzh_a = random.uniform(0, 10)
        otzh_b = random.uniform(0, 10)
        val = sum_of_deviations(otzh_a, otzh_b, tables, table_ind, l_points)
        if t > eps and (val <= ans or random.uniform(0, 1) < exp((ans - val) / t)):
            ans = val
            a = otzh_a
            b = otzh_b

        pa, pb = a, b
        da, db = 0.001, 0.001

        if sum_of_deviations(a + da, b, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind, l_points):
            a += da
        elif sum_of_deviations(a - da, b, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind, l_points):
            a -= da

        if sum_of_deviations(a, b + db, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind, l_points):
            b += db
        elif sum_of_deviations(a, b - db, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind, l_points):
            b -= db

        flag = abs(sum_of_deviations(a, b, tables, table_ind, l_points) - sum_of_deviations(pa, pb, tables, table_ind, l_points)) > eps
        count+=1
        print(a, b, 'otzhig', table_ind)
    return a, b
