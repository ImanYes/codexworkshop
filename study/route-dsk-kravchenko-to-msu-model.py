# Модель времени в пути «ДСК (ул. Кравченко, 7) → Главное здание МГУ».
# Метод Монте-Карло: 100 000 случайных поездок по каждому сценарию.
# Допущения и источники — в route-dsk-kravchenko-to-msu.md, раздел 5.
# Запуск: python3 route-dsk-kravchenko-to-msu-model.py

import math
import random

random.seed(42)
U = random.uniform
T = random.triangular  # T(мин, макс, чаще всего)
N = 100_000


def haversine_km(a, b):
    """Расстояние по прямой между двумя точками (широта, долгота)."""
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    d = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(d))


PV = (55 + 40 / 60 + 37 / 3600, 37 + 30 / 60 + 22 / 3600)   # м. Проспект Вернадского
UNI = (55 + 41 / 60 + 32 / 3600, 37 + 31 / 60 + 58 / 3600)  # м. Университет
GZ = (55.7039, 37.5286)                                      # Главное здание МГУ


def metro_part(peak):
    t = 1 + (T(0, 5, 1) if peak else 0)   # вход, турникеты, давка в час пик
    t += U(0, 2 if peak else 3.5)         # ожидание поезда
    t += U(2.5, 3.5)                      # перегон до «Университета»
    t += U(1, 2.5)                        # выход на улицу
    return t


def metro_walk(peak, walk_k=1.0):
    return U(2.5, 4) * walk_k + metro_part(peak) + U(13, 17) * walk_k


def metro_bus(peak, walk_k=1.0, traffic_k=1.0):
    t = U(2.5, 4) * walk_k + metro_part(peak)
    t += U(1, 2) * walk_k                 # к остановке «Метро Университет»
    t += U(0, 8)                          # ожидание любого подходящего автобуса
    t += U(3, 5) * traffic_k              # до «Библиотеки МГУ»
    t += U(5.5, 7.5) * walk_k             # ~500 м до ГЗ
    return t


def bus266(peak, live=True, walk_k=1.0, traffic_k=1.0):
    t = U(2, 4) * walk_k                  # до остановки «Ул. Кравченко»
    t += U(0, 3) if live else U(0, 15)    # по приложению / наугад
    ride = T(12, 25, 16) if peak else T(11, 18, 13)
    t += ride * traffic_k                 # 7 остановок до «Библиотеки МГУ»
    t += U(5.5, 7.5) * walk_k
    return t


def scooter():
    return U(2, 5) + U(15, 19) + U(2, 4)  # найти + ехать ~4,1 км + парковка


def metro_scooter(peak):
    return U(2.5, 4) + metro_part(peak) + U(1, 4) + U(5, 7) + U(2, 4)


SCENARIOS = [
    ("Метро + пешком, час пик", lambda: metro_walk(True)),
    ("Метро + пешком, не пик", lambda: metro_walk(False)),
    ("Метро + пешком, снег/гололёд", lambda: metro_walk(True, 1.2)),
    ("Метро + автобус, час пик", lambda: metro_bus(True)),
    ("Метро + автобус, снег", lambda: metro_bus(True, 1.2, 1.4)),
    ("Автобус 266, пик, по приложению", lambda: bus266(True, True)),
    ("Автобус 266, пик, наугад", lambda: bus266(True, False)),
    ("Автобус 266, не пик", lambda: bus266(False, True)),
    ("Автобус 266, дождь", lambda: bus266(True, True, 1.05, 1.25)),
    ("Автобус 266, снегопад", lambda: bus266(True, True, 1.2, 1.5)),
    ("Самокат от двери", scooter),
    ("Метро + самокат от «Университета»", lambda: metro_scooter(True)),
]

if __name__ == "__main__":
    print("По прямой: Пр. Вернадского → Университет %.2f км, Университет → ГЗ %.2f км, Пр. Вернадского → ГЗ %.2f км\n"
          % (haversine_km(PV, UNI), haversine_km(UNI, GZ), haversine_km(PV, GZ)))
    print("%-36s %6s %6s %14s" % ("Сценарий", "p50", "p90", "выходить за"))
    for name, f in SCENARIOS:
        xs = sorted(f() for _ in range(N))
        p50, p90 = xs[N // 2 - 1], xs[int(0.9 * N) - 1]
        print("%-36s %6.1f %6.1f %10d мин" % (name, p50, p90, math.ceil(p90 + 10)))
