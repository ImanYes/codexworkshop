## Календарь прототипа и расписание дня.
## Прототип — одна неделя: 6 учебных дней (пн–сб), воскресенье пропускаем.

define WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
define DAYS_IN_PROTOTYPE = 6

default day = 1                 # 1..6
default week = 1                # в прототипе всегда 1, но переключатель делает её неделей Грузина
default gruzin_week = False     # тестовый переключатель «эта неделя — неделя Грузина»

## Расписание на сегодня: список из 4 пар.
## Пара: subj, teacher, kind ("лекция" / "семинар" / "практика"), zoom, status.
## status: None (ещё не было), "был", "прогул", "своим" (зум, занимался своим).
default schedule = []

## Кто из одногруппников пришёл сегодня.
default arrived = []

## Во сколько встал: 8, 11 или 12.
default wake_hour = 8

init python:

    def weekday_name():
        return WEEKDAYS[(day - 1) % 6]

    def day_title():
        t = "Неделя {} · день {} · {}".format(week, day, weekday_name())
        if gruzin_week:
            t += " · неделя Грузина"
        return t

    def is_gruzin_week():
        return gruzin_week

    def gruzin_zoom():
        """Недели 1 и 3 — Грузин в зуме. В прототипе зум всегда, кроме недели Грузина."""
        return not gruzin_week

    def make_pair():
        if gruzin_week:
            subj = "Ангем"
        else:
            subj = renpy.random.choice(SUBJECTS)
        if subj == "Матан":
            teacher = renpy.random.choice(["akizhan", "bekmag"])
        else:
            teacher = SUBJECT_TEACHER[subj]
        if subj == "Физра":
            kind = "практика"
        else:
            kind = renpy.random.choice(["лекция", "семинар"])
        zoom = (teacher == "gruzin" and gruzin_zoom())
        return dict(subj=subj, teacher=teacher, kind=kind, zoom=zoom, status=None)

    def make_schedule():
        global schedule
        schedule = [make_pair() for i in range(4)]

    def roll_attendance():
        """Утром решаем, кто из одногруппников пришёл."""
        global arrived
        arrived = [pid for pid in STUDENT_ORDER
                   if roll(ATTEND_CHANCE[STUDENTS[pid]["attend"]])]

    PAIR_TIME = ["8:30–9:50", "10:00–11:20", "12:10–13:30", "13:40–15:00"]

    def pair_label(p):
        s = "{} ({})".format(p["subj"], who(p["teacher"]))
        s += ", " + p["kind"]
        if p["zoom"]:
            s += ", зум"
        return s
