## Календарь прототипа и расписание дня.
## Неделя — 7 дней: пн–сб учёба, вс — выходной (core/sunday.rpy).

define WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
define WEEKDAYS_SHORT = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
define STUDY_DAYS = 6           # пн–сб
define DAYS_IN_WEEK = 7

default day = 1                 # день недели: 1 = пн … 7 = вс
default abs_day = 1             # сквозной номер дня с начала игры. Сроки домашек и паузы между ивентами — только по нему
default week = 1
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
        return WEEKDAYS[(day - 1) % DAYS_IN_WEEK]

    def weekday_short():
        return WEEKDAYS_SHORT[(day - 1) % DAYS_IN_WEEK]

    def is_sunday():
        return day == DAYS_IN_WEEK

    def day_title():
        t = "Неделя {} · день {} · {}".format(week, day, weekday_name())
        if is_sunday():
            t += " · выходной"
        elif gruzin_week:
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

    def skip_company():
        """Кто из пришедших прогуливает эту пару вместе с тобой."""
        return [pid for pid in arrived
                if roll(SKIP_CHANCE[STUDENTS[pid]["attend"]])]

    PAIR_TIME = ["8:30–9:50", "10:00–11:20", "12:10–13:30", "13:40–15:00"]

    def pair_label(p):
        s = "{} ({})".format(p["subj"], who(p["teacher"]))
        s += ", " + p["kind"]
        if p["zoom"]:
            s += ", зум"
        return s
