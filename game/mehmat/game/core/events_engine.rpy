## Реестр случайных ивентов, лимиты за день, домашки, журнал дня.

## Шанс ивента по слотам (раздел 10).
define SLOT_CHANCE = {
    "morning": 10,
    "pair": 20,
    "break": 25,
    "smoke": 30,
    "skip": 25,
    "evening": 20,
    "night": 10,
}

## Лимит за день: не больше 2 случайных ивентов и 1 шага линии.
define EVENTS_PER_DAY = 2
define LINE_STEPS_PER_DAY = 1

default seen_events = set()
default last_seen = {}
default events_today = 0
default line_steps_today = 0

## Журнал дня — строки для итога дня.
default day_log = []

## Домашки: subj, teacher, given (день), known (знаешь ли), done, cheated.
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

    def event_ok(e):
        if e.once and e.id in seen_events:
            return False
        if day - last_seen.get(e.id, -999) < e.cooldown:
            return False
        if e.cond is not None and not e.cond():
            return False
        return True

    def pick_event(slot, force=False):
        """Вернуть ивент для слота или None. force — без броска шанса (лимит всё равно действует)."""
        if events_today >= EVENTS_PER_DAY:
            return None
        if not force and not roll(SLOT_CHANCE[slot]):
            return None
        pool = [e for e in EVENTS if e.slot == slot and event_ok(e)]
        if not pool:
            return None
        return renpy.random.choices(pool, weights=[e.weight for e in pool])[0]

    def mark_event(e):
        global events_today
        events_today += 1
        seen_events.add(e.id)
        last_seen[e.id] = day

    ## ----- Домашки -----

    def give_homework(p, known=True):
        homework.append(dict(subj=p["subj"], teacher=p["teacher"], given=day,
                             known=known, done=False, cheated=False))
        if known:
            day_log.append("Задали домашку: {}.".format(p["subj"]))

    def due_homework(p):
        """Домашки, срок которых — эта пара: первая пара предмета в следующий день."""
        return [h for h in homework if h["subj"] == p["subj"] and h["given"] < day]

    def known_todo():
        return [h for h in homework if h["known"] and not h["done"]]

    def hw_short():
        hw = hw_list()
        if not hw:
            return "нет"
        return ", ".join(h["subj"] + (" (готово)" if h["done"] else "") for h in hw)

    def hw_list():
        return [h for h in homework if h["known"]]

    ## ----- Скрытые правила (для «Параллельного потока» и досье) -----

    HIDDEN_RULES = [
        ("gruzin_lectures", "Грузин: лекции можно пропускать спокойно, а каждый пропущенный семинар — +1 к сложности экзамена."),
        ("gruzin_seminars", "Грузин: кто был на всех семинарах недели Грузина — у того он заметно лучше принимает."),
        ("sakishev_sleep", "Сакишев: на лекции можно поспать, но если заметит — будет долгая лекция про молодёжь."),
        ("fizruk_attend", "Физрук: ему главное, чтобы ты пришёл. За посещение принимает лояльно."),
        ("apai_talk", "Апай: всё решают разговоры. Пропуски прощает, если с ней нормально общаться."),
        ("two_skips", "Все преподы: два прогула подряд у одного — и он тебя запомнит (не в лучшую сторону)."),
    ]

    def unknown_rules():
        return [r for r in HIDDEN_RULES if r[0] not in known_rules]
