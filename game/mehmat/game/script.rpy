## Мехмат: первый курс — прототип учебной недели.
## Схема дня: game/design/study-day.md. Код дня: core/day_loop.rpy.

label start:
    $ init_teacher_rels()
    scene bg home
    "Прототип учебной недели: пн–сб пары, в воскресенье выходной."
    "Числа — заглушки. Картинки — цветные плашки. Цель — понять, интересно ли жить день."
    call hero_setup
    show screen hud
    menu:
        "Какую неделю проверяем?"
        "Обычная неделя 1 (Грузин в зуме)":
            $ gruzin_week = False
        "Неделя Грузина (тест нагрузки)":
            $ gruzin_week = True
    jump day_loop
