import time
import numpy as np


def func(l_param, x2, tables, table_ind):
    """
    Векторизованная модель.
    """
    rt = tables[table_ind].temperature * 8.314462618
    x1 = 1 - x2
    return rt * x1 * x2 * (x1 * l_param[0] + x2 * l_param[1])


def sum_of_deviations(l_param, tables, table_ind, l_points):
    """
    Среднеквадратичное отклонение (MSE).
    l_points — список (x2, gexp).
    """
    x2 = np.array([p[0] for p in l_points])
    gexp = np.array([p[1] for p in l_points])
    gmod = func(l_param, x2, tables, table_ind)
    return float(np.mean((gmod - gexp) ** 2))


def derivative(l_param, tables, table_ind, l_points):
    """
    Численный градиент (центральная разность).
    """
    params = np.array(l_param, dtype=float)
    grad = np.zeros_like(params)
    base_loss = sum_of_deviations(params, tables, table_ind, l_points)

    for i in range(len(params)):
        p = params[i]
        h = max(1e-6, abs(p) * 1e-6)  # адаптивный шаг
        p_plus, p_minus = params.copy(), params.copy()
        p_plus[i] += h
        p_minus[i] -= h
        f_plus = sum_of_deviations(p_plus, tables, table_ind, l_points)
        f_minus = sum_of_deviations(p_minus, tables, table_ind, l_points)
        grad[i] = (f_plus - f_minus) / (2 * h)
    return grad.tolist()


def gradient_step(tables, table_ind, *, eps=1e-5, max_iters=5000):
    """
    Оптимизированный градиентный спуск вместо "флагов" и ручного уменьшения d.
    Использует backtracking line search (по Армихо).
    """
    start_time = time.time()

    # Подготовка точек
    l_points = [(p.x_value, p.y_value) for p in tables[table_ind].points.all()]
    if not l_points:
        return 0.0, 0.0, 0, 0.0, [0.0, 1.0], [0, 0], [0, 0], [0, 0], [0, 0], 0.0

    # Начальное приближение
    l_param = np.array([10.0, 10.0])
    iters = 0

    # Параметры line search
    alpha = 0.3
    beta = 0.5

    current_loss = sum_of_deviations(l_param, tables, table_ind, l_points)

    while iters < max_iters:
        grad = np.array(derivative(l_param, tables, table_ind, l_points))
        grad_norm = np.linalg.norm(grad)

        if grad_norm < eps:
            break

        direction = -grad
        t = 1.0

        # Backtracking line search
        while t > 1e-8:
            new_params = l_param + t * direction
            new_loss = sum_of_deviations(new_params, tables, table_ind, l_points)
            if new_loss <= current_loss + alpha * t * np.dot(grad, direction):
                l_param = new_params
                current_loss = new_loss
                break
            t *= beta

        if t <= 1e-8:
            break

        iters += 1

    # Формирование данных для таблицы
    l_x2 = [0.0]
    l_gmod = [0]
    l_gexp = [0]
    l_op = [0]
    l_ap = [0]

    for x2, gexp in l_points:
        gmod = func(l_param, x2, tables, table_ind)
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

    print(f"Gradient_step completed in {exec_time:.3f} seconds with {iters} iterations")

    return (
        float(l_param[0]),
        float(l_param[1]),
        iters,
        exec_time,
        l_x2,
        l_gmod,
        l_gexp,
        l_op,
        l_ap,
        avg_op,
    )
