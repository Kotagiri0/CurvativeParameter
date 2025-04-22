import time


def func(a, b, x2, tables, table_ind):
    rt = tables[table_ind].temperature * 8.314462618  # температура на газовую постоянную
    x1 = 1 - x2
    return rt * x1 * x2 * (x1 * a + x2 * b)


def sum_of_deviations(a, b, tables, table_ind, l_points):
    sum = 0
    for i in range(0, len(l_points)):
        x2 = l_points[i][0]
        ge = l_points[i][1]
        sum += (func(a, b, x2, tables, table_ind) - ge) ** 2
    return sum / len(l_points)


def gauss(tables, table_ind):
    # Начало замера времени
    start_time = time.time()

    l_points = []
    for point in tables[table_ind].points.all():
        l_points.append((point.x_value, point.y_value))

    a, b = 1, 1
    eps = 0.0000001
    flag = True
    count = 0
    da, db = 0.001, 0.001

    while flag:
        count += 1
        pa, pb = a, b
        if sum_of_deviations(a + da, b, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind,
                                                                                         l_points):
            a += da
        elif sum_of_deviations(a - da, b, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind,
                                                                                           l_points):
            a -= da
        if sum_of_deviations(a, b + db, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind,
                                                                                         l_points):
            b += db
        elif sum_of_deviations(a, b - db, tables, table_ind, l_points) < sum_of_deviations(a, b, tables, table_ind,
                                                                                           l_points):
            b -= db
        flag = abs(sum_of_deviations(a, b, tables, table_ind, l_points) - sum_of_deviations(pa, pb, tables, table_ind,
                                                                                            l_points)) > eps
        print(a, b, "gauss", table_ind)

    # Формирование данных для таблицы
    l_x2, l_gmod, l_gexp, l_op, l_ap = [0.0], [0], [0], [100], [0]
    for el in l_points:
        x2, ge = el[0], el[1]
        l_x2.append(x2)
        l_gexp.append(ge)
        l_gmod.append(round(func(a, b, x2, tables, table_ind)))
        l_op.append(round(abs((func(a, b, x2, tables, table_ind) - ge) / ge * 100), 1))
        l_ap.append(round(abs(func(a, b, x2, tables, table_ind) - ge)))

    l_x2.append(0.0)
    l_gmod.append(0)
    l_gexp.append(0)
    l_op.append(100)
    l_ap.append(0)

    # Конец замера времени
    exec_time = time.time() - start_time
    print(f"Gauss completed in {exec_time:.3f} seconds with {count} iterations")

    return a, b, count, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap