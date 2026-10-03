## Персонажи прототипа: 7 преподов и 6 одногруппников из досье (game/design/characters/students.md).
## Ключи n1…n6 — внутренние, остались от заглушек: на них завязаны линия №1 и ивенты.
## Когда добавим всех 26, перейдём на ключи по именам.

## Кто говорит в диалогах.
define gr = Character("Грузин", color="#e0a060")
define ak = Character("Акижан", color="#a0c0e0")
define bk = Character("Бекмагистров", color="#a0c0e0")
define va = Character("Василий", color="#90d090")
define fz = Character("Физрук", color="#d0d0d0")
define sk = Character("Сакишев", color="#c0a0d0")
define ap = Character("Апай", color="#f0b0c0")
define dr = Character("Директор", color="#ff7070")
define mom = Character("Мама", color="#f0e0a0")

## Одногруппники. num — номер в досье; attend — посещаемость; smokes — курит;
## hint — коротко о характере (видно в карточке «Люди»). Разговоры — game/dialogues/.
define STUDENTS = {
    "n1": dict(name="Гаухар", num=14, sex="ж", attend="часто", smokes=False,
               hint="в школе отличница, здесь тяжело"),
    "n2": dict(name="Даниил", num=24, sex="м", attend="всегда", smokes=True,
               hint="душа компании, шутит про Германию"),
    "n3": dict(name="Вика", num=23, sex="ж", attend="иногда", smokes=True,
               hint="торнадо, взрывается на несправедливость"),
    "n4": dict(name="Ноидор", num=3, sex="м", attend="редко", smokes=True,
               hint="харизматичный, знает все слухи"),
    "n5": dict(name="Саид", num=19, sex="м", attend="всегда", smokes=False,
               hint="физмат-школа, тихий, всегда поможет"),
    "n6": dict(name="Карина", num=26, sex="ж", attend="всегда", smokes=False,
               hint="старательная, на связи с преподами"),
}

define STUDENT_ORDER = ["n1", "n2", "n3", "n4", "n5", "n6"]

## Шанс прийти в универ за день.
define ATTEND_CHANCE = {"всегда": 90, "часто": 70, "иногда": 45, "редко": 20}

## Шанс, что пришедший прогуливает эту же пару вместе с тобой (компания для прогула).
define SKIP_CHANCE = {"всегда": 5, "часто": 15, "иногда": 30, "редко": 50}

## Преподы. Отношения с ними скрыты от игрока, старт — 5/10.
define TEACHERS = {
    "gruzin": dict(name="Грузин", char="gr", subj="Ангем"),
    "akizhan": dict(name="Акижан", char="ak", subj="Матан"),
    "bekmag": dict(name="Бекмагистров", char="bk", subj="Матан"),
    "vasily": dict(name="Василий", char="va", subj="Алгебра"),
    "fizruk": dict(name="Физрук", char="fz", subj="Физра"),
    "sakishev": dict(name="Сакишев", char="sk", subj="История"),
    "apai": dict(name="Апай", char="ap", subj="Языки"),
}

define SUBJECTS = ["Ангем", "Матан", "Алгебра", "Физра", "История", "Языки"]

define SUBJECT_TEACHER = {
    "Ангем": "gruzin",
    "Алгебра": "vasily",
    "Физра": "fizruk",
    "История": "sakishev",
    "Языки": "apai",
    ## Матан — Акижан или Бекмагистров, решается при составлении расписания.
}

init -5 python:

    def who(pid):
        """Имя для текста: одногруппник или препод."""
        if pid in STUDENTS:
            return STUDENTS[pid]["name"]
        if pid in TEACHERS:
            return TEACHERS[pid]["name"]
        return pid

    def smokes(pid):
        return STUDENTS[pid]["smokes"]

    def sx(pid, m, f):
        """Слово в роде одногруппника: sx(pid, "думал", "думала")."""
        return f if STUDENTS[pid]["sex"] == "ж" else m

    def say_as(pid, what):
        """Реплика одногруппника без отдельного объекта Character на каждого."""
        renpy.say(Character(STUDENTS[pid]["name"], color="#ffd27a"), what)

    def tsay(tid, what):
        """Реплика препода."""
        renpy.say(getattr(store, TEACHERS[tid]["char"]), what)

init python:
    ## Стартовые отношения с преподами — нейтральные 5/10.
    ## 55, а не 50: середина деления «5». С 50 любая мелочь (несданная домашка) роняет до 4/10,
    ## а «все семинары Грузина» (+Б) не доводят до 6/10 надёжно.
    def init_teacher_rels():
        for t in TEACHERS:
            rels[t] = 55
        rels["director"] = 50

## После всех define (они выполняются на init 0).
init 1 python:
    ## Проверка при запуске: новый одногруппник с опечаткой в посещаемости или характере
    ## иначе уронит игру посреди дня. Лучше сразу понятная ошибка.
    for _pid, _d in STUDENTS.items():
        if _d["attend"] not in ATTEND_CHANCE:
            raise Exception("Одногруппник {}: посещаемость «{}» — нужно одно из: {}".format(
                _pid, _d["attend"], ", ".join(ATTEND_CHANCE)))
        if _d["sex"] not in ("м", "ж"):
            raise Exception("Одногруппник {}: пол «{}» — нужно «м» или «ж»".format(_pid, _d["sex"]))
    for _pid in STUDENT_ORDER:
        if _pid not in STUDENTS:
            raise Exception("STUDENT_ORDER: нет одногруппника {} в STUDENTS".format(_pid))

    ## Разговоры: у каждого есть файл в game/dialogues/, в каждой сцене ровно один хороший ответ.
    def _check_scene(_pid, _where, _sc):
        _q = [o[1] for o in _sc["options"]]
        if any(x not in ("good", "ok", "bad") for x in _q) or _q.count("good") != 1:
            raise Exception("Разговор {} ({}): ответы должны быть good / ok / bad, good — ровно один".format(_pid, _where))
        for o in _sc["options"]:
            if len(o) > 3 and o[3] not in [r[0] for r in HIDDEN_RULES]:
                raise Exception("Разговор {} ({}): нет скрытого правила {}".format(_pid, _where, o[3]))
    for _pid in STUDENT_ORDER:
        if _pid not in DIALOGUES:
            raise Exception("Нет разговоров для {} — добавь файл в game/dialogues/".format(_pid))
        _d = DIALOGUES[_pid]
        for _k in ("mood_bad", "topics", "phone_ok", "phone_no", "date"):
            if _k not in _d:
                raise Exception("Разговор {}: нет поля {}".format(_pid, _k))
        if "intro" in _d:
            _check_scene(_pid, "intro", _d["intro"])
        for _t in _d["topics"]:
            for _i, _sc in enumerate(_t["scenes"]):
                _check_scene(_pid, "{} #{}".format(_t["id"], _i + 1), _sc)
