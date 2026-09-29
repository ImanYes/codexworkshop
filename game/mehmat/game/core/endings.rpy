## Мораль на нуле → досрочный конец «Ушёл сам» (study-day.md, раздел 9; mehmat-framework.md, 2.10).
## Каждую ночь: мораль 0 → +1 к счётчику дней подряд, иначе счётчик = 0.
## Сначала предупреждение с шансом спастись, потом конец.
## Пороги — заглушки: в доке «порог решим с актами».

define ZERO_MORALE_WARN = 4     # дней подряд на нуле → предупреждение
define ZERO_MORALE_LEAVE = 7    # неделя подряд на нуле → конец «Ушёл сам»

default zero_morale_days = 0
default gave_up = False

init python:

    def best_friend():
        """Самый близкий одногруппник (приятель и выше) или None."""
        pool = [p for p in STUDENT_ORDER if tier(p) >= 2]
        if not pool:
            return None
        return max(pool, key=rel_value)


label morale_check:
    if shown("morale") > 0:
        $ zero_morale_days = 0
        return
    $ zero_morale_days += 1
    $ day_log.append("Мораль на нуле уже {} дн. подряд.".format(zero_morale_days))
    if zero_morale_days >= ZERO_MORALE_LEAVE:
        $ gave_up = True
    elif zero_morale_days == ZERO_MORALE_WARN:
        call zero_morale_warning
    return


label zero_morale_warning:
    scene bg night
    "Ты лежишь и смотришь в потолок. В телефоне открыт сайт университета: «Заявление на отчисление по собственному желанию»."
    $ best = best_friend()
    if best:
        $ bname = who(best)
        $ renpy.show("plate " + best)
        "Телефон вибрирует. [bname]."
        $ say_as(best, "Ты куда {g=пропала}пропал{/g}? Завтра идёшь? Без тебя на парах совсем тоска.")
        $ change("morale", +B)
        $ rel(best, +S)
        "Ты закрываешь вкладку. Может, ещё не всё потеряно."
        $ renpy.hide("plate")
    else:
        "Звонит мама."
        mom "Голос у тебя грустный. Что случилось?"
        menu:
            "Рассказать всё":
                if roll(50):
                    mom "Слушай меня. Один семестр — это не вся жизнь. Держись, мы рядом."
                    $ change("morale", +S)
                    "После разговора становится чуть легче."
                else:
                    mom "Ну… может, это и правда не твоё. Подумай."
                    "Легче не стало."
            "«Всё нормально, мам»":
                mom "Ну смотри."
                "Ты кладёшь трубку и снова открываешь вкладку."
    $ day_log.append("Была мысль забрать документы.")
    return


## Сюда приходим прыжком из day_loop, поэтому return в конце — выход в главное меню.
label ending_gave_up:
    hide screen hud
    scene bg home
    "Утром ты не идёшь на пары. Вместо этого — учебная часть."
    "Заявление. Подпись. Документы тебе отдают молча."
    "Мораль была на нуле [zero_morale_days] дн. подряд."
    "Концовка «{g=Ушла}Ушёл{/g} {g=сама}сам{/g}»."
    return
