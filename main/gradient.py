def derivative(l_param, tables, table_ind, l_points):
    a, b = l_param[0], l_param[1]
    e = 0.0001
    da, pva = 1, 0
    va = (sum_of_deviations([a+da, b], tables, table_ind, l_points)-sum_of_deviations(l_param, tables, table_ind, l_points)) / da
    while (abs(va-pva)>e):
        pva = va
        da *= 0.5
        va = (sum_of_deviations([a+da, b], tables, table_ind, l_points)-sum_of_deviations(l_param, tables, table_ind, l_points)) / da
    db, pvb = 1, 0
    vb = (sum_of_deviations([a, b+db], tables, table_ind, l_points) - sum_of_deviations(l_param, tables, table_ind, l_points)) / db
    while (abs(vb - pvb) > e):
        pvb = vb
        db *= 0.5
        vb = (sum_of_deviations([a, b+db], tables, table_ind, l_points) - sum_of_deviations(l_param, tables, table_ind, l_points)) / db
    return [va, vb]

def func(l_param, x2, tables, table_ind):
    rt = tables[table_ind].temperature * 8.314462618
    x1 = 1 - x2
    return rt * x1 * x2*(x1 * l_param[0] + x2 * l_param[1])

def sum_of_deviations(l_param, tables, table_ind, l_points):
    sum = 0
    for i in range(0, len(l_points)):
        x2, ge = l_points[i][0], l_points[i][1]
        sum += (func(l_param, x2, tables, table_ind) - ge) ** 2
    return sum / len(l_points)
def gradient(tables, table_ind):
    l_points = []
    for point in tables[table_ind].points.all():
        l_points.append((point.x_value, point.y_value))
    l_param = [1, 1]
    eps = 0.0001
    d = 0.01
    flag = True
    while flag:
        pa, pb = l_param[0], l_param[1]
        da, db = derivative(l_param, tables, table_ind, l_points)
        if ((da**2+db**2)**0.5) < eps:
            break
        l_param[0], l_param[1] = pa - da*d/((da**2+db**2)**0.5), pb - db*d/((da**2+db**2)**0.5)
        if abs(sum_of_deviations(l_param, tables, table_ind, l_points) - sum_of_deviations([pa, pb], tables, table_ind, l_points)) < eps:
            d *= 0.5
            if d < 10e-5:
                flag = False
        print(l_param[0], l_param[1], 'gradient', table_ind)
    return l_param[0], l_param[1]
