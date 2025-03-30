def func(a, b, x2, tables, table_ind):
    rt = tables[table_ind].temperature*8.314462618
    x1 = 1 - x2
    return rt * x1 * x2*(x1 * a + x2 * b)

def sum_of_deviations(a, b, tables, table_ind, l_points):
    sum = 0
    for i in range(0, len(l_points)):
        x2 = l_points[i][0]
        ge = l_points[i][1]
        sum += (func(a, b, x2, tables, table_ind) - ge) ** 2
    return sum / len(l_points)
def gauss(tables, table_ind):
    l_points = []
    for point in tables[table_ind].points.all():
        l_points.append((point.x_value, point.y_value))


    a, b = 1, 1
    eps = 0.0000001
    flag = True
    count = 0
    da, db = 0.001, 0.001
    while flag:
        pa, pb = a, b
        if sum_of_deviations(a + da, b, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind, l_points):
            a += da
        elif sum_of_deviations(a - da, b, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind, l_points):
            a -= da
        if sum_of_deviations(a, b + db, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind, l_points):
            b += db
        elif sum_of_deviations(a, b - db, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind, l_points):
            b -= db
        count += 1
        flag = abs(sum_of_deviations(a, b, tables, table_ind, l_points) - sum_of_deviations(pa, pb, tables, table_ind, l_points )) > eps
        print(a, b, "gauss", table_ind)
    return a, b
