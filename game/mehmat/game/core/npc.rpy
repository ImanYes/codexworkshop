## Персонажи прототипа: 7 преподов и 6 одногруппников-заглушек.
## Одногруппники временные (раздел 13 study-day.md), потом заменим настоящими.

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

## Одногруппники-заглушки.
## attend — посещаемость; smokes — курит; style — какая реплика «под характер».
define STUDENTS = {
    "n1": dict(name="Айгерим", num=1, sex="ж", attend="всегда", smokes=False,
               hint="отличница, прямая", style="direct"),
    "n2": dict(name="Даурен", num=2, sex="м", attend="часто", smokes=True,
               hint="балагур", style="joke"),
    "n3": dict(name="Мира", num=3, sex="ж", attend="иногда", smokes=True,
               hint="тихая, язвит", style="tease"),
    "n4": dict(name="Тимур", num=4, sex="м", attend="редко", smokes=True,
               hint="прогульщик", style="chill"),
    "n5": dict(name="Арман", num=5, sex="м", attend="всегда", smokes=False,
               hint="ботан, много знает", style="study"),
    "n6": dict(name="Дана", num=6, sex="ж", attend="часто", smokes=False,
               hint="староста", style="help"),
}

define STUDENT_ORDER = ["n1", "n2", "n3", "n4", "n5", "n6"]

## Шанс прийти в универ за день.
define ATTEND_CHANCE = {"всегда": 90, "часто": 70, "иногда": 45, "редко": 20}

## Шанс, что пришедший прогуливает эту же пару вместе с тобой (компания для прогула).
define SKIP_CHANCE = {"всегда": 5, "часто": 15, "иногда": 30, "редко": 50}

## Реплики для разговора «с выбором». Правильная — та, что под характер.
define REPLY_TEXT = {
    "direct": "Сказать прямо, что думаешь",
    "joke": "Пошутить",
    "tease": "Ответить колкостью на колкость",
    "chill": "Предложить свалить с пары",
    "study": "Спросить про задачу с прошлой пары",
    "help": "Предложить помочь с делами группы",
}

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
    def init_teacher_rels():
        for t in TEACHERS:
            rels[t] = 50
        rels["director"] = 50

## После всех define (они выполняются на init 0).
init 1 python:
    ## Проверка при запуске: новый одногруппник с опечаткой в посещаемости или характере
    ## иначе уронит игру посреди дня. Лучше сразу понятная ошибка.
    for _pid, _d in STUDENTS.items():
        if _d["attend"] not in ATTEND_CHANCE:
            raise Exception("Одногруппник {}: посещаемость «{}» — нужно одно из: {}".format(
                _pid, _d["attend"], ", ".join(ATTEND_CHANCE)))
        if _d["style"] not in REPLY_TEXT:
            raise Exception("Одногруппник {}: характер «{}» — нужно одно из: {}".format(
                _pid, _d["style"], ", ".join(REPLY_TEXT)))
        if _d["sex"] not in ("м", "ж"):
            raise Exception("Одногруппник {}: пол «{}» — нужно «м» или «ж»".format(_pid, _d["sex"]))
    for _pid in STUDENT_ORDER:
        if _pid not in STUDENTS:
            raise Exception("STUDENT_ORDER: нет одногруппника {} в STUDENTS".format(_pid))
