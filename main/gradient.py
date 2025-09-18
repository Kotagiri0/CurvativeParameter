import time
import numpy as np

def func(params, x2, temperature):
    """
    Векторизованная модель: params = [a, b]
    x2 может быть скаляром или numpy-массивом
    """
    a, b = params[0], params[1]
    rt = temperature * 8.314462618
    x2 = np.asarray(x2)
    x1 = 1.0 - x2
    return rt * x1 * x2 * (x1 * a + x2 * b)


def sum_of_deviations(params, x2_arr, gexp_arr, temperature):
    """
    Возвращает среднеквадратичную ошибку (MSE) для векторных входов.
    """
    preds = func(params, x2_arr, temperature)
    errs = (preds - gexp_arr) ** 2
    return float(np.mean(errs)) if errs.size > 0 else 0.0


def derivative(params, x2_arr, gexp_arr, temperature):
    """
    Численный градиент (центральная разность) с адаптивным шагом h.
    Возвращает градиент по a и b.
    """
    params = np.asarray(params, dtype=float)
    grad = np.zeros_like(params)
    base = sum_of_deviations(params, x2_arr, gexp_arr, temperature)

    # адаптивный h в зависимости от масштаба параметра
    for i in range(len(params)):
        p = params[i]
        h = max(1e-6, abs(p) * 1e-6)  # можно настроить
        # центральная разность
        p_plus = params.copy()
        p_minus = params.copy()
        p_plus[i] += h
        p_minus[i] -= h
        f_plus = sum_of_deviations(p_plus, x2_arr, gexp_arr, temperature)
        f_minus = sum_of_deviations(p_minus, x2_arr, gexp_arr, temperature)
        grad[i] = (f_plus - f_minus) / (2 * h)
    return grad.tolist()


def gradient(tables, table_ind, *, eps=1e-5, initial_params=(0.0, 0.0), max_iters=10000):
    """
    Оптимизированный градиентный спуск с backtracking line search (Armijo).
    Возвращает:
    a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, average_op
    """
    start_time = time.time()

    # Извлекаем точки в numpy-массивы (чтобы обращаться к БД только один раз)
    table = tables[table_ind]
    points = list(table.points.all())
    if len(points) == 0:
        # пустая таблица — возвращаем нули в том же формате
        l_x2 = [0.0, 1.0]
        l_gmod = [0, 0]
        l_gexp = [0, 0]
        l_op = [0, 0]
        l_ap = [0, 0]
        exec_time = time.time() - start_time
        return 0.0, 0.0, 0, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, 0.0

    x2_arr = np.array([p.x_value for p in points], dtype=float)
    gexp_arr = np.array([p.y_value for p in points], dtype=float)
    temperature = float(table.temperature)

    params = np.array(initial_params, dtype=float)
    it = 0

    # параметры для backtracking line search
    alpha = 0.3   # параметр Armijo
    beta = 0.5    # уменьшение шага
    base_loss = sum_of_deviations(params, x2_arr, gexp_arr, temperature)

    while it < max_iters:
        it += 1
        grad = np.array(derivative(params, x2_arr, gexp_arr, temperature), dtype=float)
        grad_norm = np.linalg.norm(grad)
        if grad_norm < eps:
            break

        # направление -grad (минимизация)
        direction = -grad
        # начальный шаг (можно подбирать)
        t = 1.0

        # backtracking line search (Armijo condition)
        while t > 1e-8:
            new_params = params + t * direction
            new_loss = sum_of_deviations(new_params, x2_arr, gexp_arr, temperature)
            # Armijo условие: f(x + t p) <= f(x) + alpha * t * grad^T p
            if new_loss <= base_loss + alpha * t * np.dot(grad, direction):
                params = new_params
                base_loss = new_loss
                break
            else:
                t *= beta

        # если шаг слишком мал — выходим
        if t <= 1e-8:
            break

    # Формируем данные для таблицы в формате, аналогичном вашему
    l_x2 = [0.0] + [float(x) for x in x2_arr.tolist()] + [1.0]
    l_gexp = [0] + [float(g) for g in gexp_arr.tolist()] + [0]
    # вычисляем модельные значения и метрики
    gmod_vals = func(params, x2_arr, temperature)
    l_gmod = [0] + [float(np.round(v, 6)) for v in gmod_vals.tolist()] + [0]

    # вычисляем проценты и абсолютные отклонения; безопасно для нуля
    deltas = np.abs(gmod_vals - gexp_arr)
    with np.errstate(divide='ignore', invalid='ignore'):
        sigmas = np.where(gexp_arr != 0, (deltas / np.abs(gexp_arr)) * 100.0, 0.0)

    l_op = [0] + [float(np.round(s, 1)) for s in sigmas.tolist()] + [0]
    l_ap = [0] + [float(np.round(d, 6)) for d in deltas.tolist()] + [0]

    exec_time = time.time() - start_time
    avg_op = float(np.round(np.mean(l_op[1:-1]) if len(l_op) > 2 else 0.0, 1))

    print(f"Gradient completed in {exec_time:.3f} seconds with {it} iterations")

    return float(params[0]), float(params[1]), it, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op
