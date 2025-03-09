import os
from .gauss_step import l_points
from .models import Table

table_ind = 0

tables = Table.objects.all()
print(tables[table_ind])

def func(a, b, x2, tables, table_ind):
    rt = tables[table_ind].temperature*8.314462618    # температура на газовую постоянную
    x1 = 1 - x2
    return rt * x1 * x2*(x1 * a + x2 * b)

def sum_of_deviations(a, b, tables, table_ind):
    sum = 0
    for i in range(0, len(l_points)):
        x2 = l_points[i][0]
        ge = l_points[i][1]
        sum += (func(a, b, x2, tables, table_ind) - ge) ** 2
    return sum / len(l_points)
def gauss(tables, table_ind):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    db_path = os.path.join(parent_dir, 'db.sqlite3')

    for point in tables[table_ind].points.all():
        l_points.append((point.x_value, point.y_value))


    a, b = 1, 1
    eps = 0.0000001
    flag = True
    count = 0
    da, db = 0.0001, 0.0001
    while flag:
        pa, pb = a, b
        if sum_of_deviations(a + da, b, tables, table_ind) < sum_of_deviations(a, b, tables, table_ind):
            a += da
        elif sum_of_deviations(a - da, b, tables, table_ind) < sum_of_deviations(a, b, tables, table_ind):
            a -= da
        if sum_of_deviations(a, b + db, tables, table_ind) < sum_of_deviations(a, b, tables, table_ind):
            b += db
        elif sum_of_deviations(a, b - db, tables, table_ind) < sum_of_deviations(a, b, tables, table_ind):
            b -= db
        count += 1
        flag = abs(sum_of_deviations(a, b, tables, table_ind) - sum_of_deviations(pa, pb, tables, table_ind)) > eps
    print(a, b)
    return a, b
