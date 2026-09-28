## Статы героя, размеры изменений (М / С / Б), отношения.
## Все числа — заглушки из game/design/study-day.md, раздел 12.
## Внутри шкала 0–100, игрок видит 0–10.

## Размеры изменений. Пишем в коде: change("morale", +S), rel("n1", -M).
define M = 1
define S = 2
define B = 3

## Сколько это в числах для каждого стата. Баланс правим только здесь.
define SIZE = {
    "know":    {1: 0.3, 2: 0.5, 3: 2},
    "morale":  {1: 3,   2: 7,   3: 15},
    "fatigue": {1: 3,   2: 7,   3: 15},
    "rel":     {1: 2,   2: 5,   3: 10},
    "rep":     {1: 1,   2: 3,   3: 7},
    "cha":     {1: 1,   2: 3,   3: 5},
    "att":     {1: 1,   2: 3,   3: 5},
}

define STAT_NAME = {
    "know": "знания",
    "morale": "мораль",
    "fatigue": "усталость",
    "rep": "репутация",
    "cha": "харизма",
    "att": "привлекательность",
    "money": "деньги",
}

## Старт героя в прототипе (раздел 12).
default stats = {
    "know": 30.0,
    "cha": 50.0,
    "att": 30.0,
    "morale": 60.0,
    "fatigue": 20.0,
    "rep": 40.0,
}
default money = 2

## Отношения: id -> 0..100. Одногруппника нет в словаре, пока не познакомились.
default rels = {}

init -10 python:

    def clamp(x, lo=0, hi=100):
        return max(lo, min(hi, x))

    def amount(stat, size):
        """+S → +7 для морали, −M → −0,3 для знаний и т. д."""
        sign = 1 if size > 0 else -1
        return sign * SIZE[stat][abs(size)]

    def change(stat, size, factor=1.0):
        """Изменить стат героя на размер М/С/Б. factor — для надоедания."""
        stats[stat] = clamp(stats[stat] + amount(stat, size) * factor)

    def change_raw(stat, value):
        stats[stat] = clamp(stats[stat] + value)

    def money_add(n):
        global money
        money = max(0, money + n)

    def shown(stat):
        """Как видит игрок: 0–10, с округлением вниз."""
        return int(stats[stat] // 10)

    def total_cha():
        """Итоговая харизма = харизма + 0,25 × привлекательность (в шкале 0–10)."""
        return stats["cha"] / 10.0 + 0.25 * stats["att"] / 10.0

    ## ----- Отношения -----

    def met(pid):
        return pid in rels

    def meet(pid):
        """Знакомство: стартовые отношения = 5 + репутация ÷ 10."""
        if pid not in rels:
            rels[pid] = clamp(5 + int(stats["rep"] // 10))
            if pid in STUDENTS:
                day_log.append("Познакомились: {}.".format(who(pid)))

    def rel(pid, size):
        if pid not in rels:
            meet(pid)
        rels[pid] = clamp(rels[pid] + amount("rel", size))

    def rel_value(pid):
        return rels.get(pid, 0)

    def tier(pid):
        """Ступень отношений: 0 незнакомец … 4 близкий."""
        if pid not in rels:
            return 0
        v = rels[pid]
        if v >= 70:
            return 4
        if v >= 50:
            return 3
        if v >= 30:
            return 2
        return 1

    TIER_NAME = ["незнакомец", "знакомый", "приятель", "друг", "близкий"]

    def tier_name(pid):
        return TIER_NAME[tier(pid)]

    def rep_words():
        r = stats["rep"]
        if r < 20:
            return "о тебе шепчутся"
        if r < 40:
            return "тебя почти не знают"
        if r < 60:
            return "тебя знают"
        if r < 80:
            return "тебя уважают"
        return "звезда курса"

    def talk_chance(pid):
        """Шанс удачного разговора, 10–95%."""
        p = (50
             + 8 * (total_cha() - 5)
             + 3 * (stats["morale"] / 10.0 - 5)
             + 5 * tier(pid))
        return clamp(p, 10, 95)

    def roll(percent):
        """True с шансом percent %. Только renpy.random — откат не меняет результат."""
        return renpy.random.random() * 100 < percent

    ## ----- Надоедание -----
    ## Мораль от одного и того же занятия несколько дней подряд: 100 / 75 / 50 / 25 %.

    BOREDOM = [1.0, 0.75, 0.5, 0.25]

    def boredom_factor(act):
        n = boredom.get(act, 0)          # сколько дней подряд уже было до сегодня
        return BOREDOM[min(n, 3)]

    def did_activity(act):
        today_acts.add(act)

default boredom = {}
default today_acts = set()
