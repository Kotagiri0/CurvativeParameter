import time
import numpy as np


def derivative(l_param, tables, table_ind, l_points):
    a, b = l_param[0], l_param[1]
    e = 0.0001
    da, pva = 1, 0
    va = (sum_of_deviations([a + da, b], tables, table_ind, l_points) - sum_of_deviations(l_param, tables, table_ind,
                                                                                          l_points)) / da
    while abs(va - pva) > e:
        pva = va
        da *= 0.5
        va = (sum_of_deviations([a + da, b], tables, table_ind, l_points) - sum_of_deviations(l_param, tables,
                                                                                              table_ind, l_points)) / da
    db, pvb = 1, 0
    vb = (sum_of_deviations([a, b + db], tables, table_ind, l_points) - sum_of_deviations(l_param, tables, table_ind,
                                                                                          l_points)) / db
    while abs(vb - pvb) > e:
        pvb = vb
        db *= 0.5
        vb = (sum_of_deviations([a, b + db], tables, table_ind, l_points) - sum_of_deviations(l_param, tables,
                                                                                              table_ind, l_points)) / db
    return [va, vb]


def func(l_param, x2, tables, table_ind):
    rt = tables[table_ind].temperature * 8.314462618
    x1 = 1 - x2
    return rt * x1 * x2 * (x1 * l_param[0] + x2 * l_param[1])


def sum_of_deviations(l_param, tables, table_ind, l_points):
    sum = 0
    for i in range(0, len(l_points)):
        x2, ge = l_points[i][0], l_points[i][1]
        sum += (func(l_param, x2, tables, table_ind) - ge) ** 2
    return sum / len(l_points)


def gradient_step(tables, table_ind):
    # Начало замера времени
    start_time = time.time()

    l_points = []
    for point in tables[table_ind].points.all():
        l_points.append((point.x_value, point.y_value))

    l_param = [10, 10]
    ll_param = []
    eps = 0.00001
    d = 0.01
    flag = True
    count, count_iter = 0, 0
    iter_max = 10
    const_learning = 1.05
    for i in range(0, 1, 1):
        for j in range(0, 1, 1):
            l_param[0],l_param[1] = i, j
            while flag:
                pa, pb = l_param[0], l_param[1]
                pda, pdb = derivative([pa, pb], tables, table_ind, l_points)
                da, db = derivative(l_param, tables, table_ind, l_points)
                if count_iter >= iter_max:
                    d *= const_learning
                if np.sign(pda) != np.sign(da) and np.sign(pdb) != np.sign(db):
                    count_iter = 0
                    d = 0.01
                if ((da ** 2 + db ** 2) ** 0.5) < eps:
                    break
                l_param[0], l_param[1] = pa - da * d / ((da ** 2 + db ** 2) ** 0.5), pb - db * d / ((da ** 2 + db ** 2) ** 0.5)
                if abs(sum_of_deviations(l_param, tables, table_ind, l_points) - sum_of_deviations([pa, pb], tables, table_ind, l_points)) < eps:
                    d *= 0.5
                    if d < 10e-5:
                        flag = False
                count_iter += 1
                count += 1
                print(l_param[0], l_param[1], 'gradient_step', table_ind, 'param_iter', i, j)
            count_iter = 0
            d = 0.01
            flag = True
            ll_param.append(l_param.copy())
    l_param = ll_param[0]
    for el in ll_param:
        # print(sum_of_deviations(el))
        if (sum_of_deviations(l_param, tables, table_ind, l_points) >= sum_of_deviations(el, tables, table_ind, l_points)):
            l_param = el.copy()
    # Формирование данных для таблицы
    l_x2, l_gmod, l_gexp, l_op, l_ap = [0.0], [0], [0], [0], [0]
    for el in l_points:
        x2, ge = el[0], el[1]
        l_x2.append(x2)
        l_gexp.append(ge)
        l_gmod.append(round(func(l_param, x2, tables, table_ind)))
        l_op.append(round(abs((func(l_param, x2, tables, table_ind) - ge) / ge * 100), 1))
        l_ap.append(round(abs(func(l_param, x2, tables, table_ind) - ge)))

    l_x2.append(1.0)
    l_gmod.append(0)
    l_gexp.append(0)
    l_op.append(0)
    l_ap.append(0)

    # Конец замера времени
    exec_time = time.time() - start_time
    print(f"Gradient_step completed in {exec_time:.3f} seconds with {count} iterations")

    return l_param[0], l_param[1], count, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, round(sum(l_op)/len(l_op), 1)