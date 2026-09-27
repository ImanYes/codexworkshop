"""Симуляция: один чайный пакетик, кружка, глоток 10% кружки каждые t минут.

Запуск: python3 study/tea-bag-simulation.py
Разбор задачи и выводы — в study/tea-bag-optimization.md
"""
import math

# --- Параметры (допущения, их можно менять под себя) ---
V = 300.0        # объём кружки, мл
SIP = 0.1 * V    # глоток = 10% кружки
T_ROOM = 22.0    # температура комнаты, °C
T_START = 92.0   # температура сразу после заливки кипятка в холодную кружку
H = 0.03         # скорость остывания кружки, 1/мин (закон Ньютона)
K90 = 0.35       # скорость отдачи вкуса пакетиком при 90°C, 1/мин
S_MIN = 0.5      # порог вкуса: 0.5 = «вдвое слабее обычной кружки»


def k(T):
    """Скорость экстракции: при остывании на 20°C — вдвое медленнее."""
    return K90 * 2 ** ((T - 90) / 20)


def normal_cup():
    """«Обычная кружка»: пакетик 4 минуты, ничего не пьём. Её крепость = 1.0."""
    bag, mug, T, dt = 1.0, 0.0, T_START, 1 / 600
    for _ in range(int(4 / dt)):
        d = k(T) * bag * dt
        bag, mug = bag - d, mug + d
        T -= H * (T - T_ROOM) * dt
    return mug / V


C_NORM = normal_cup()


def run(t_sip=2.0, every=1, t_water=100.0, wait=3.0, s_min=S_MIN):
    """Пьём глоток каждые t_sip минут, доливаем до краёв после каждых `every` глотков.

    Долив урезается, если после него крепость упала бы ниже s_min,
    т.е. в конце доливаем «ровно до порога» и допиваем остаток.
    Возвращает список глотков (время, мл, крепость, температура) и остаток в пакетике.
    """
    vol, bag, mug, T = V, 1.0, 0.0, T_START  # bag/mug — доли вещества пакетика
    time, dt, next_sip, n = 0.0, 1 / 60, wait, 0
    sips = []
    while vol > 1e-9 and time < 300:
        d = k(T) * bag * dt
        bag, mug = bag - d, mug + d
        T -= H * (T - T_ROOM) * dt
        time += dt
        if time < next_sip:
            continue
        take = min(SIP, vol)
        c = mug / vol
        sips.append((time, take, c / C_NORM, T))
        mug -= c * take
        vol -= take
        n += 1
        next_sip += t_sip
        if n % every == 0:
            add = min(V - vol, max(0.0, mug / (s_min * C_NORM) - vol))
            if add > 1e-6:
                T = (T * vol + t_water * add) / (vol + add)
                vol += add
    return sips, bag


def summary(sips):
    w = sum(s[1] for s in sips)
    strength = sum(s[1] * s[2] for s in sips) / w
    temp = sum(s[1] * s[3] for s in sips) / w
    return w, strength, temp


if __name__ == "__main__":
    print(f"Верхняя граница объёма (сохранение вещества): {1 / (S_MIN * C_NORM):.0f} мл\n")

    print("1) Стратегии долива (глоток раз в 2 мин, кипяток 100°C)")
    for name, every in [("доливать после каждого глотка", 1),
                        ("доливать после 5 глотков", 5),
                        ("допить до дна, потом залить", 10)]:
        sips, bag = run(every=every)
        w, s, t = summary(sips)
        print(f"   {name:32s} выпито {w:4.0f} мл, средняя крепость {s:.2f}, "
              f"объём×крепость {w * s:.0f}, средняя t {t:.0f}°C")

    print("\n2) Температура: формула vs симуляция (долив после каждого глотка)")
    for t_sip in (1, 2, 4):
        for t_water in (100, 80):
            r = 0.1 / t_sip
            formula = (r * t_water + H * T_ROOM) / (r + H)
            sips, _ = run(t_sip=t_sip, t_water=t_water, s_min=0.001)
            late = [s[3] for s in sips[20:40]]  # глотки после выхода на режим
            print(f"   глоток раз в {t_sip} мин, долив {t_water}°C: "
                  f"формула {formula:.0f}°C, симуляция {sum(late) / len(late):.0f}°C")

    print("\n3) Долив водой разной температуры (глоток раз в 2 мин)")
    for t_water in (100, 80, 50, 22):
        sips, bag = run(t_water=t_water)
        w, s, t = summary(sips)
        print(f"   долив {t_water:3d}°C: выпито {w:4.0f} мл, в пакетике осталось {bag * 100:.1f}%")

    print("\n4) Порог вкуса -> сколько можно выпить (долив 80°C после каждого глотка)")
    for s_min in (0.3, 0.5, 0.7, 1.0):
        sips, _ = run(t_water=80, s_min=s_min)
        w, s, _ = summary(sips)
        print(f"   не слабее {s_min:.1f}: {w:4.0f} мл ({w / V:.1f} кружки), "
              f"граница {1 / (s_min * C_NORM):4.0f} мл")

    print("\n5) Только разбавление: объём на каждое «ослабление в e раз», доля кружки")
    for q in (0.1, 0.3, 0.5, 0.9):
        print(f"   доливать {q:.0%} кружки за раз: {q / -math.log(1 - q):.2f}")
