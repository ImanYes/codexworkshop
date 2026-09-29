## Реестр случайных ивентов, лимиты за день, домашки, журнал дня.

## Шанс ивента по слотам (раздел 10). Числа выше доковых: с лимитом 2 в день доковые
## 10/20/25/30/20/10 давали ~1,3 ивента в день, а цель — «около 2». Частоту держат паузы
## (cooldown) в add_event: ивент не повторяется раньше, чем через 3–4 дня.
## Вечер и ночь идут после дня и часто упираются в лимит, поэтому их шанс выше, чем кажется нужным.
define SLOT_CHANCE = {
    "morning": 10,
    "pair": 35,
    "break": 45,
    "smoke": 50,
    "skip": 40,
    "sunday": 70,
    "evening": 45,
    "night": 30,
}

## Лимит за день: не больше 2 случайных ивентов и 1 шага линии.
define EVENTS_PER_DAY = 2
define LINE_STEPS_PER_DAY = 1

default seen_events = set()
default last_seen = {}          # ивент -> abs_day, когда был последний раз
default events_today = 0
default line_steps_today = 0

## Журнал дня — строки для итога дня.
default day_log = []

## Домашки: subj, teacher, given (abs_day), wd (день недели), known (знаешь ли), done, cheated.
default homework = []

## Скрытые правила преподов, которые герой уже узнал.
default known_rules = set()

init -1 python:

    class Event(object):
        def __init__(self, id, slot, label, title, cond=None, weight=10, once=False, cooldown=2):
            self.id = id
            self.slot = slot
            self.label = label
            self.title = title
            self.cond = cond
            self.weight = weight
            self.once = once
            self.cooldown = cooldown

    EVENTS = []

    def add_event(*args, **kwargs):
        EVENTS.append(Event(*args, **kwargs))

    def event_ready(eid, cooldown):
        """Прошло ли cooldown дней с последнего показа ивента (для ивентов вне пула)."""
        return abs_day - last_seen.get(eid, -999) >= cooldown

    def event_ok(e):
        if e.once and e.id in seen_events:
            return False
        if abs_day - last_seen.get(e.id, -999) < e.cooldown:
            return False
        if e.cond is not None and not e.cond():
            return False
        return True

    def take_event(slot):
        """Бросить шанс слота. Выпал ивент — отметить его и вернуть имя сцены (label), иначе None.
        В переменные игры кладём только строку: сам ивент с условием-lambda сохранить нельзя."""
        if events_today >= EVENTS_PER_DAY:
            return None
        if not roll(SLOT_CHANCE[slot]):
            return None
        pool = [e for e in EVENTS if e.slot == slot and event_ok(e)]
        if not pool:
            return None
        e = renpy.random.choices(pool, weights=[e.weight for e in pool])[0]
        mark_event(e.id)
        return e.label

    def mark_event(eid):
        global events_today
        events_today += 1
        seen_events.add(eid)
        last_seen[eid] = abs_day

    ## ----- Домашки -----

    def give_homework(p, known=True):
        homework.append(dict(subj=p["subj"], teacher=p["teacher"], given=abs_day,
                             wd=weekday_short(), known=known, done=False, cheated=False))
        if known:
            day_log.append("Задали домашку: {}.".format(p["subj"]))

    def due_homework(p):
        """Домашки, срок которых — эта пара: первая пара предмета в один из следующих дней."""
        return [h for h in homework if h["subj"] == p["subj"] and h["given"] < abs_day]

    def known_todo():
        return [h for h in homework if h["known"] and not h["done"]]

    def hw_list():
        return [h for h in homework if h["known"]]

    def hw_title(h):
        """«Ангем (задали в пн)» — чтобы две домашки по одному предмету не путались."""
        return "{} (задали в {})".format(h["subj"], h["wd"])

    def hw_short():
        """Для полоски сверху: коротко, чтобы не уезжало за край экрана."""
        hw = hw_list()
        if not hw:
            return "нет"
        counts = {}
        for h in hw:
            counts[h["subj"]] = counts.get(h["subj"], 0) + 1
        parts = []
        for s in SUBJECTS:
            if s in counts:
                parts.append(s if counts[s] == 1 else "{} ×{}".format(s, counts[s]))
        done = len([h for h in hw if h["done"]])
        text = ", ".join(parts[:3])
        if len(parts) > 3:
            text += "…"
        if done:
            text += " (готово {})".format(done)
        return text

    ## ----- Скрытые правила (для «Параллельного потока» и досье) -----

    HIDDEN_RULES = [
        ("gruzin_lectures", "Грузин: лекции можно пропускать спокойно, а каждый пропущенный семинар — +1 к сложности экзамена."),
        ("gruzin_seminars", "Грузин: кто был на всех семинарах недели Грузина — у того он заметно лучше принимает."),
        ("sakishev_sleep", "Сакишев: на лекции можно поспать, но если заметит — будет долгая лекция про молодёжь."),
        ("fizruk_attend", "Физрук: ему главное, чтобы ты {g=пришла}пришёл{/g}. За посещение принимает лояльно."),
        ("apai_talk", "Апай: всё решают разговоры. Пропуски прощает, если с ней нормально общаться."),
        ("two_skips", "Все преподы: два прогула подряд у одного — и он тебя запомнит (не в лучшую сторону)."),
    ]

    def unknown_rules():
        return [r for r in HIDDEN_RULES if r[0] not in known_rules]
