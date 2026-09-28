## Графика-заглушки: фон = цветной прямоугольник с названием места,
## персонаж = плашка с именем. Потом заменим настоящим артом.

init -10 python:
    def place(name, color):
        return Fixed(
            Solid(color),
            Text(name, size=90, color="#ffffff30", xalign=0.5, yalign=0.35),
        )

    def plate(name, color="#3b4252"):
        return Fixed(
            Solid(color),
            Text(name, size=44, color="#ffffff", xalign=0.5, yalign=0.5),
            xysize=(360, 520),
        )

image bg home = place("Общага", "#2e3440")
image bg home_evening = place("Общага, вечер", "#232834")
image bg night = place("Ночь", "#0d1017")
image bg aud = place("Аудитория", "#3a4a3a")
image bg zoom = place("Зум", "#1f2f4f")
image bg gym_hall = place("Спортзал", "#4a3a2a")
image bg corridor = place("Коридор", "#4a4a55")
image bg canteen = place("Столовая", "#5a4636")
image bg smoke = place("Курилка", "#3d3d3d")
image bg street = place("Улица", "#3a4550")
image bg gymnasium = place("Качалка", "#503838")
image bg work = place("Работа", "#384050")

init python:
    for _pid, _d in STUDENTS.items():
        renpy.image(("plate", _pid), plate("№{} {}".format(_d["num"], _d["name"]), "#5e4b6e"))
    for _tid, _d in TEACHERS.items():
        renpy.image(("plate", _tid), plate(_d["name"], "#4b5e6e"))
    renpy.image(("plate", "director"), plate("Директор", "#6e3b3b"))

transform plate_pos:
    xalign 0.5 yalign 0.35

init python:
    config.tag_transform["plate"] = plate_pos
