import random
import time
import numpy as np


def func(a, b, x2, tables, table_ind):
    """Модель: g^E = RT * x1 * x2 * (a * x1 + b * x2)."""
    rt = tables[table_ind].temperature * 8.314462618
    x1 = 1.0 - x2
    return rt * x1 * x2 * (x1 * a + x2 * b)


def sum_of_deviations(a, b, tables, table_ind, l_points):
    """Среднеквадратичное отклонение (MSE)."""
    x2 = np.array([p[0] for p in l_points])
    gexp = np.array([p[1] for p in l_points])
    gmod = func(a, b, x2, tables, table_ind)
    return float(np.mean((gmod - gexp) ** 2))


def otzhig(tables, table_ind, *, init_temp=5.0, cooling=0.995, eps=1e-7, max_iters=50000):
    start_time = time.time()

    l_points = [(p.x_value, p.y_value) for p in tables[table_ind].points.all()]
    if not l_points:
        return 0.0, 0.0, 0, 0.0, [0.0, 1.0], [0, 0], [0, 0], [0, 0], [0, 0], 0.0

    # стартовые параметры
    a, b = random.uniform(0, 5), random.uniform(0, 5)
    best_a, best_b = a, b
    best_val = sum_of_deviations(a, b, tables, table_ind, l_points)

    T = init_temp
    count = 0

    while T > eps and count < max_iters:
        count += 1

        # случайный сосед (шаг уменьшается вместе с T)
        new_a = max(0, a + random.gauss(0, 0.5 * T))
        new_b = max(0, b + random.gauss(0, 0.5 * T))

        new_val = sum_of_deviations(new_a, new_b, tables, table_ind, l_points)

        # вероятность принятия
        delta = best_val - new_val
        prob = np.exp(min(700, delta / T)) if delta < 0 else 1.0

        if new_val < best_val or random.random() < prob:
            a, b = new_a, new_b
            best_val = new_val
            best_a, best_b = a, b

        T *= cooling

    # === Формирование данных для таблицы ===
    l_x2, l_gmod, l_gexp, l_op, l_ap = [0.0], [0], [0], [0], [0]

    for x2, gexp in l_points:
        gmod = func(best_a, best_b, x2, tables, table_ind)
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

    print(f"Otzhig completed in {exec_time:.3f} seconds with {count} iterations")

    return best_a, best_b, count, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op
