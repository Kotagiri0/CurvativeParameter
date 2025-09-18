import time
import numpy as np


def func(a, b, x2, tables, table_ind):
    """Модель: g^E = RT * x1 * x2 * (a * x1 + b * x2)."""
    rt = tables[table_ind].temperature * 8.314462618
    x1 = 1.0 - x2
    return rt * x1 * x2 * (a * x1 + b * x2)


def sum_of_deviations(a, b, tables, table_ind, l_points):
    """Среднеквадратичное отклонение (MSE)."""
    x2 = np.array([p[0] for p in l_points])
    gexp = np.array([p[1] for p in l_points])
    gmod = func(a, b, x2, tables, table_ind)
    return float(np.mean((gmod - gexp) ** 2))


def gauss(tables, table_ind, *, eps=1e-7, max_iters=100000, init_step=0.01):
    start_time = time.time()

    l_points = [(p.x_value, p.y_value) for p in tables[table_ind].points.all()]
    if not l_points:
        return 0.0, 0.0, 0, 0.0, [0.0, 1.0], [0, 0], [0, 0], [0, 0], [0, 0], 0.0

    # начальные параметры
    a, b = 1.0, 1.0
    da, db = init_step, init_step
    val = sum_of_deviations(a, b, tables, table_ind, l_points)

    count = 0
    while count < max_iters:
        count += 1
        pa, pb, pval = a, b, val

        # пробуем шаг по "a"
        for sign in (+1, -1):
            new_a = a + sign * da
            new_val = sum_of_deviations(new_a, b, tables, table_ind, l_points)
            if new_val < val:
                a, val = new_a, new_val
                break  # нашли улучшение → выходим из цикла

        # пробуем шаг по "b"
        for sign in (+1, -1):
            new_b = b + sign * db
            new_val = sum_of_deviations(a, new_b, tables, table_ind, l_points)
            if new_val < val:
                b, val = new_b, new_val
                break

        # адаптация шага
        if abs(val - pval) < eps:
            da *= 0.5
            db *= 0.5
            if da < 1e-6 and db < 1e-6:
                break  # шаг слишком мал → выходим

    # === Формирование данных для таблицы ===
    l_x2, l_gmod, l_gexp, l_op, l_ap = [0.0], [0], [0], [0], [0]
    for x2, gexp in l_points:
        gmod = func(a, b, x2, tables, table_ind)
        l_x2.append(x2)
        l_gexp.append(gexp)
        l_gmod.append(round(gmod))
        if gexp != 0:
            l_op.append(round(abs((gmod - gexp) / gexp * 100), 1))
        else:
            l_op.append(0)
        l_ap.append(round(abs(gmod - gexp)))

    l_x2.append(1.0)
    l_gmod.append(0)
    l_gexp.append(0)
    l_op.append(0)
    l_ap.append(0)

    exec_time = time.time() - start_time
    avg_op = round(sum(l_op) / len(l_op), 1)

    print(f"Gauss completed in {exec_time:.3f} seconds with {count} iterations")

    return a, b, count, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op
