import time
import numpy as np


def func(a, b, x2, tables, table_ind):
    """
    Модель: g^E = RT * x1 * x2 * (a * x1 + b * x2).
    """
    rt = tables[table_ind].temperature * 8.314462618
    x1 = 1.0 - x2
    return rt * x1 * x2 * (a * x1 + b * x2)


def sum_of_deviations(a, b, tables, table_ind, l_points):
    """
    Среднеквадратичное отклонение (MSE) между моделью и экспериментом.
    """
    x2 = np.array([p[0] for p in l_points])
    gexp = np.array([p[1] for p in l_points])
    gmod = func(a, b, x2, tables, table_ind)
    return float(np.mean((gmod - gexp) ** 2))


def gauss_step(tables, table_ind, *, eps=1e-7, max_iters=5000):
    """
    Оптимизированный метод координатного спуска.
    """
    start_time = time.time()

    # Точки (x2, gexp)
    l_points = [(p.x_value, p.y_value) for p in tables[table_ind].points.all()]
    if not l_points:
        return 0.0, 0.0, 0, 0.0, [0.0, 1.0], [0, 0], [0, 0], [0, 0], [0, 0], 0.0

    # Начальные значения
    a, b = 1.0, 1.0
    da, db = 1e-3, 1e-3
    const_learning = 1.01
    iter_max = 10

    count = 0
    count_iter_a, count_iter_b = 0, 0
    f_stepa, b_stepa, f_stepb, b_stepb = True, True, True, True

    current_loss = sum_of_deviations(a, b, tables, table_ind, l_points)

    while True:
        pa, pb = a, b
        prev_loss = current_loss

        # === Обновление по a ===
        if count_iter_a >= iter_max:
            da *= const_learning
        else:
            da = 1e-4

        loss_plus = sum_of_deviations(a + da, b, tables, table_ind, l_points)
        loss_minus = sum_of_deviations(a - da, b, tables, table_ind, l_points)

        if loss_plus < current_loss:
            a += da
            current_loss = loss_plus
            if b_stepa:
                f_stepa, b_stepa = True, False
                count_iter_a = 0
            count_iter_a += 1
        elif loss_minus < current_loss:
            a -= da
            current_loss = loss_minus
            if f_stepa:
                f_stepa, b_stepa = False, True
                count_iter_a = 0
            count_iter_a += 1

        # === Обновление по b ===
        if count_iter_b >= iter_max:
            db *= const_learning
        else:
            db = 1e-4

        loss_plus = sum_of_deviations(a, b + db, tables, table_ind, l_points)
        loss_minus = sum_of_deviations(a, b - db, tables, table_ind, l_points)

        if loss_plus < current_loss:
            b += db
            current_loss = loss_plus
            if b_stepb:
                f_stepb, b_stepb = True, False
                count_iter_b = 0
            count_iter_b += 1
        elif loss_minus < current_loss:
            b -= db
            current_loss = loss_minus
            if f_stepb:
                f_stepb, b_stepb = False, True
                count_iter_b = 0
            count_iter_b += 1

        count += 1

        # Критерий остановки
        if abs(current_loss - prev_loss) < eps or count >= max_iters:
            break

        print(a, b, "gauss_step", table_ind)

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

    print(f"Gauss_step completed in {exec_time:.3f} seconds with {count} iterations")

    return a, b, count, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op
