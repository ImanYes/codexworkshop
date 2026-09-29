## Цикл дня. Пн–сб: утро → 4 пары с перерывами → после пар → вечер → ночь.
## Вс — выходной: core/sunday.rpy. Схема — game/design/study-day.md.

## Счётчики и флаги, которые живут дольше дня.
default skips = {}                  # препод -> прогулов подряд
default exam_diff = {}              # препод -> +сложность экзамена (Грузин: пропущенные семинары вживую)
default gruzin_sem_missed = False   # пропустил семинар Грузина на его неделе
default gruzin_sem_seen = 0         # сколько семинаров Грузина было вживую
default has_smoking = False
default smoking_day = 0             # abs_day, когда получил навык
default has_job = False
default job_rate = 4
default gym_pass = False
default heard_anecdotes = []        # анекдоты в этом прохождении

## Счётчики дня.
default talks_today = {}
default talk_counter = 0            # каждый 3-й разговор — выбор реплики
default energy_drink = False
default went_home = False
default worked = False
default phone_used = False
default meeting_refused = False
default now_text = ""
default cur_pair = None
default cur_mode = None             # "normal", "sleep", "own"
default present = []                # кто рядом сейчас: на перерыве или вместе с тобой на прогуле
default break_actions = 0
default snap = {}

init python:

    def start_day():
        global talks_today, energy_drink, went_home, worked, phone_used, meeting_refused
        global events_today, line_steps_today, day_log, today_acts, snap, present, cur_pair
        global sunday_refused
        talks_today = {}
        energy_drink = False
        went_home = False
        worked = False
        phone_used = False
        meeting_refused = False
        sunday_refused = False
        events_today = 0
        line_steps_today = 0
        day_log = []
        today_acts = set()
        present = []
        cur_pair = None
        snap = dict(stats=dict(stats), money=money, rels=dict(rels),
                    rep_words=rep_words())

    def smoking_fresh():
        """Первые 2 дня после навыка курение только снижает статы."""
        return has_smoking and abs_day - smoking_day < 2

    def skip_effects(p):
        """Общие последствия прогула пары (и ручного, и из-за просыпа)."""
        global gruzin_sem_missed
        t = p["teacher"]
        p["status"] = "прогул"
        change("rep", -M)
        if roll(10):
            change("know", -M)
        skips[t] = skips.get(t, 0) + 1
        if skips[t] >= 2:
            rel(t, -B)
            skips[t] = 0
        if t == "gruzin" and not p["zoom"] and p["kind"] == "семинар":
            gruzin_sem_missed = True
            exam_diff["gruzin"] = exam_diff.get("gruzin", 0) + 1
        for h in due_homework(p):
            homework.remove(h)
            rel(h["teacher"], -S)
            if h["known"]:
                day_log.append(gf("Не сдал", "Не сдала") +
                               " домашку по предмету «{}» — прогул пары.".format(p["subj"]))
        ## Не был на семинаре — не знаешь, что задали (study-day.md, раздел 5).
        if p["kind"] == "семинар" and roll(50):
            give_homework(p, known=False)

    def break_people(big):
        n = renpy.random.randint(4, 6) if big else renpy.random.randint(2, 3)
        n = min(n, len(arrived))
        return renpy.random.sample(arrived, n)

    def names(pids):
        return ", ".join(who(p) for p in pids) if pids else "никого"

    def after_night_boredom():
        global boredom
        boredom = {a: boredom.get(a, 0) + 1 for a in today_acts}


label day_loop:
    if day > DAYS_IN_WEEK:
        jump week_end
    $ start_day()
    if is_sunday():
        call sunday
    else:
        call morning
        call classes
        call after_classes
        call evening
    call night
    if gave_up:
        jump ending_gave_up
    $ day += 1
    $ abs_day += 1
    jump day_loop


## ================= Утро =================

label morning:
    scene bg home
    $ now_text = "8:00 · подъём"
    $ roll_attendance()
    $ make_schedule()
    $ wake_hour = 8
    $ forced = False
    call screen day_card

    if weekday_name() == "понедельник":
        $ money_add(1)
        $ day_log.append("Понедельник: +$1 на неделю.")

    if stats["fatigue"] >= 100:
        $ wake_hour = renpy.random.choice([11, 12])
        $ forced = True
        "Будильник звонил. Ты его не {g=слышала}слышал{/g}. Усталость взяла своё."
    elif shown("morale") < 3 and roll({2: 15, 1: 30, 0: 45}[shown("morale")]):
        $ wake_hour = renpy.random.choice([11, 12])
        $ forced = True
        "Будильник звенит, а вставать совсем незачем. Глаза закрываются сами."
    else:
        "Будильник. 8:00."
        menu:
            "Встать":
                pass
            "Поспать ещё":
                $ wake_hour = renpy.random.choice([11, 12])
                $ change("fatigue", -S)
                "Ещё пять минуточек…"

    if forced:
        $ change("morale", -S)
        $ day_log.append(gf("Проспал", "Проспала") + " до {}:00.".format(wake_hour))
    elif wake_hour > 8:
        $ day_log.append(gf("Выспался, встал", "Выспалась, встала") + " в {}:00.".format(wake_hour))

    if wake_hour > 8:
        $ now_text = "{}:00 · {}".format(wake_hour, gf("проспал", "проспала"))
        "Ты открываешь глаза. На часах [wake_hour]:00."

    if gruzin_week:
        $ change("morale", -S)

    call screen schedule_view(morning=True)

    $ ev = take_event("morning")
    if ev:
        call expression ev
    return


## ================= Пары и перерывы =================

label classes:
    ## Сколько пар проспал: 11:00 → 2, 12:00 → 3.
    $ missed = {8: 0, 11: 2, 12: 3}[wake_hour]
    $ pair_i = 0
    while pair_i < 4:
        if pair_i < missed:
            $ skip_effects(schedule[pair_i])
        elif went_home:
            $ skip_effects(schedule[pair_i])
        else:
            call pair_slot(pair_i)
        if pair_i < 3 and pair_i >= missed - 1 and not went_home:
            call break_slot(pair_i)
        $ pair_i += 1
    if missed:
        $ day_log.append("Проспанные пары записаны как прогулы: {}.".format(missed))
    return


label pair_slot(i):
    $ cur_pair = schedule[i]
    $ present = []
    $ now_text = "{} · пара {}".format(PAIR_TIME[i], i + 1)
    if cur_pair["zoom"]:
        scene bg zoom
    elif cur_pair["subj"] == "Физра":
        scene bg gym_hall
    else:
        scene bg aud
    $ plabel = pair_label(cur_pair)
    $ pnum = i + 1
    menu:
        "Пара [pnum]: [plabel]."
        "Пойти":
            $ cur_mode = "normal"
            call attend_pair
        "Зайти и заниматься своим" if cur_pair["zoom"]:
            $ cur_mode = "own"
            call attend_pair
        "Прогулять":
            call skip_pair
    return


label attend_pair:
    $ p = cur_pair
    $ t = p["teacher"]
    $ p["status"] = "своим" if cur_mode == "own" else "был"
    $ skips[t] = 0
    $ renpy.show("plate " + t)

    ## Сдача домашки — в начале пары.
    call submit_homework

    if cur_mode == "own":
        "Камера выключена, микрофон тоже. Грузин что-то чертит на экране. Ты {g=занята}занят{/g} своим."
        if events_today < EVENTS_PER_DAY and roll(40):
            $ mark_event("zoom_hear")
            call ev_zoom_hear
        $ renpy.hide("plate")
        return

    if t == "sakishev":
        "Сакишев монотонно читает про даты и реформы. Веки тяжелеют."
        menu:
            "Слушать":
                pass
            "Поспать":
                $ cur_mode = "sleep"

    if cur_mode == "sleep":
        $ change("fatigue", -S)
        if roll(30):
            sk "{g=Девушка}Молодой человек{/g}! Вот нынешняя молодёжь… В наше время на лекциях не спали."
            "Ты выслушиваешь ещё десять минут о молодёжи."
            $ rel(t, -S)
        else:
            "Ты мирно {g=проспала}проспал{/g} всю лекцию. Никто не заметил."
            $ rel(t, +M)
    elif t == "fizruk":
        fz "Бегом, бегом! Три круга."
        $ change("fatigue", +S)
        $ rel(t, +M)
    elif t == "gruzin" and p["zoom"]:
        "Зум. Грузин говорит коротко, камера у половины группы выключена."
        $ change("know", +M if p["kind"] == "лекция" else +S)
        $ change("fatigue", +M if p["kind"] == "лекция" else +S)
    elif t == "gruzin":
        gr "Садитесь. Начинаем. Телефоны убрать."
        $ change("know", +M if p["kind"] == "лекция" else +S)
        $ change("fatigue", +S)
        if p["kind"] == "семинар":
            $ gruzin_sem_seen += 1
    else:
        if p["kind"] == "лекция":
            $ change("know", +M)
            $ change("fatigue", +M)
        else:
            $ change("know", +S)
            $ change("fatigue", +S)
        $ rel(t, +M)

        if t == "vasily":
            call vasily_anecdote
        elif t == "apai" and p["kind"] == "семинар":
            call apai_question
        elif t in ("akizhan", "bekmag"):
            $ tn = who(t)
            "[p[subj]]. Сегодня ведёт [tn]."

    ## Домашку задают на семинаре с шансом 50%.
    if p["kind"] == "семинар" and roll(50):
        $ give_homework(p)
        "В конце пары задали домашку."

    $ ev = take_event("pair")
    if ev:
        call expression ev
    else:
        "Пара прошла спокойно."
    $ renpy.hide("plate")
    return


label submit_homework:
    $ due = due_homework(cur_pair)
    while due:
        $ h = due.pop(0)
        $ homework.remove(h)
        ## Отношения — с тем, кто задавал (на матане это может быть другой препод).
        if h["known"] and h["done"]:
            if h["cheated"] and roll(30):
                "Препод смотрит в твою тетрадь, потом в чью-то ещё. Одинаковые ошибки."
                $ rel(h["teacher"], -S)
                $ change("rep", -M)
                $ day_log.append("Списанную домашку по предмету «{}» заметили.".format(h["subj"]))
            else:
                "Ты сдаёшь домашку по предмету «[h[subj]]». Приятно."
                $ change("morale", +B)
                $ rel(h["teacher"], +S)
                $ change("rep", +M)
                $ change("know", +S)
                $ day_log.append(gf("Сдал", "Сдала") + " домашку: {}.".format(h["subj"]))
        elif h["known"]:
            "Домашка по предмету «[h[subj]]» не сделана. Препод молча ставит пометку."
            $ rel(h["teacher"], -S)
            $ day_log.append(gf("Не сдал", "Не сдала") + " домашку: {}.".format(h["subj"]))
        else:
            "Оказывается, в прошлый раз задавали домашку. Ты о ней не {g=знала}знал{/g}."
            $ rel(h["teacher"], -S)
            $ day_log.append(gf("Не знал", "Не знала") + " о домашке по предмету «{}».".format(h["subj"]))
    return


label skip_pair:
    $ skip_effects(cur_pair)
    $ present = skip_company()
    "Ты не идёшь на пару."

    if events_today < EVENTS_PER_DAY and roll(5):
        $ mark_event("director")
        call ev_director
        return

    if present:
        $ pnames = names(present)
        "Эту пару прогуливают и другие: [pnames]."

    menu:
        "Куда пойти?"
        "В курилку" if has_smoking:
            call smoke_room(present)
        "В столовую":
            scene bg canteen
            $ change("fatigue", -M)
            "В столовой тихо. Можно посидеть."
            $ ev = take_event("skip")
            if ev:
                call expression ev
        "Уйти домой":
            $ went_home = True
            "Ты уходишь. Остальные пары сегодня — тоже прогул."
    return


## ----- Особые правила преподов -----

label vasily_anecdote:
    $ left = [a for a in range(len(ANECDOTES)) if a not in heard_anecdotes]
    if left:
        $ a = renpy.random.choice(left)
        $ heard_anecdotes.append(a)
        $ persistent_add_anecdote(a)
        va "Прежде чем начнём — анекдот."
        $ atext = ANECDOTES[a]
        va "[atext]"
        $ day_log.append("Новый анекдот Василия (#{}).".format(a + 1))
    else:
        va "Анекдоты у меня на сегодня кончились. Давайте про кольца."
    $ change("morale", +M)
    return


label apai_question:
    $ q = renpy.random.choice(APAI_QUESTIONS)
    ap "[q[0]]"
    $ opts = list(q[1])
    $ renpy.random.shuffle(opts)
    $ ans = renpy.display_menu([(o, o) for o in opts])
    if ans == q[1][0]:
        ap "Правильно! Молодец."
        $ rel("apai", +S)
    else:
        ap "Нет. Правильно — «[q[1][0]]». Повтори дома."
        $ rel("apai", -M)
    return


## ----- Перерыв -----

label break_slot(i):
    $ big = (i == 1)
    $ break_actions = 2 if big else 1
    $ now_text = ["9:50 · перерыв", "11:20 · большой перерыв", "13:30 · перерыв"][i]
    $ present = break_people(big)
    scene bg corridor
    $ pnames = names(present)
    if big:
        "Большой перерыв. Рядом: [pnames]."
    else:
        "Перерыв. Рядом: [pnames]."

    if "n1" in present and n1_step >= 1 and line_ripe("n1"):
        "[n1_name] поглядывает на тебя, будто хочет что-то спросить."

    $ ev = take_event("break")
    if ev:
        call expression ev
        $ break_actions -= 1

    while break_actions > 0:
        menu:
            "Что делать? (действий: [break_actions])"
            "Поговорить" if present:
                call talk_menu(big)
            "Буфет" if money >= 1:
                call buffet
            "В курилку" if has_smoking:
                ## На перерыве курить выходят все курящие, кто сегодня пришёл.
                call smoke_room(arrived)
                scene bg corridor
            "Отдохнуть":
                $ change("fatigue", -M)
                "Ты просто сидишь на подоконнике и смотришь в окно."
        $ break_actions -= 1
    return


label talk_menu(big):
    $ items = []
    python:
        for pid in present:
            n_talks = talks_today.get(pid, 0)
            label_text = "{} — {}".format(who(pid), tier_name(pid))
            if n_talks >= 2:
                items.append((label_text + " (уже наговорились)", None))
            else:
                items.append((label_text, pid))
        items.append(("Передумать и отдохнуть", "rest"))
    $ pid = renpy.display_menu(items)
    if pid == "rest":
        $ change("fatigue", -M)
        "Ты решаешь просто отдохнуть."
        return
    call talk(pid, big)
    return


label talk(pid, big=False):
    $ renpy.show("plate " + pid)
    $ nm = who(pid)
    $ nhint = STUDENTS[pid]["hint"]
    $ talks_today[pid] = talks_today.get(pid, 0) + 1

    ## Созрел шаг линии — он вместо обычного разговора.
    if line_ripe(pid):
        $ line_steps_today += 1
        call expression "line_" + pid + "_step"
        $ renpy.hide("plate")
        return

    if not met(pid):
        $ meet(pid)
        "Новое знакомство: [nm]. Характер: [nhint]."
        $ renpy.hide("plate")
        return

    $ talk_counter += 1
    if talk_counter % 3 == 0:
        ## Выбор реплики: под характер → удача.
        $ good = STUDENTS[pid]["style"]
        $ other = renpy.random.sample([s for s in REPLY_TEXT if s != good], 2)
        $ opts = [good] + other
        $ renpy.random.shuffle(opts)
        "[nm] ([nhint]) ждёт, что ты скажешь."
        $ pick = renpy.display_menu([(REPLY_TEXT[o], o) for o in opts])
        $ ok = (pick == good)
    else:
        $ ok = roll(talk_chance(pid))

    if ok:
        $ rel(pid, +S if big else +M)
        "Разговор клеится. [nm] улыбается."
    else:
        $ rel(pid, -M)
        "Разговор не клеится. Неловкая пауза."
    $ renpy.hide("plate")
    return


label buffet:
    scene bg canteen
    menu:
        "Буфет. У тебя $[money]."
        "Энергетик ($1): −усталость сейчас, но ночью сон хуже":
            $ money_add(-1)
            $ change("fatigue", -S)
            $ energy_drink = True
        "Булочка ($1): +мораль":
            $ money_add(-1)
            $ change("morale", +S)
        "Ничего не брать":
            pass
    scene bg corridor
    return


## pool — кто может оказаться в курилке: на перерыве — все пришедшие,
## на прогуле — только те, кто прогуливает вместе с тобой.
label smoke_room(pool):
    scene bg smoke
    if smoking_fresh():
        "Горько и кашляешь. Удовольствия пока никакого."
        $ change_raw("morale", -0.1)   # −0,01 в шкале игрока; какие статы — ещё не решено
    else:
        $ change("morale", +M)
    $ change("fatigue", +M)

    $ ev = take_event("smoke")
    if ev:
        call expression ev
        return

    $ smokers = [p for p in pool if smokes(p) and talks_today.get(p, 0) < 2]
    if smokers:
        $ items = [("Поговорить: " + who(p), p) for p in smokers] + [("Просто покурить", "none")]
        $ who_pick = renpy.display_menu(items)
        if who_pick != "none":
            call talk(who_pick, False)
    else:
        "В курилке никого из своих."
    return


## ================= После пар =================

label after_classes:
    $ now_text = "15:00 · после пар"
    if went_home:
        scene bg home
        $ where_q = "Ты уже дома. Что дальше?"
        $ home_text = "Остаться дома"
    else:
        scene bg street
        $ where_q = "Пары кончились. Куда?"
        $ home_text = "Домой"
    menu:
        "[where_q]"
        "[home_text]":
            $ change("fatigue", -M)
            scene bg home
            if went_home:
                "Ты валяешься на кровати до вечера."
            else:
                "Ты идёшь домой и валяешься."
        "В качалку" if gym_pass:
            call gym
        "Купить абонемент ($10) и в качалку" if not gym_pass and money >= 10:
            call buy_gym
        "На работу" if has_job:
            call work_shift
    if has_job and not worked:
        $ job_rate = max(1, job_rate - 1)
        $ day_log.append(gf("Пропустил", "Пропустила") + " работу: ставка теперь ${}.".format(job_rate))
    return


label gym:
    scene bg gymnasium
    $ change("att", +M)
    $ change("morale", +S, boredom_factor("gym"))
    $ did_activity("gym")
    $ change("fatigue", +S)
    "Железо, зеркала, чужая музыка из колонки."
    return


label buy_gym:
    $ money_add(-10)
    $ gym_pass = True
    $ day_log.append("Куплен абонемент в качалку.")
    call gym
    return


label work_shift:
    $ worked = True
    $ money_add(job_rate)
    $ change("morale", -B)
    $ change("fatigue", +S)
    scene bg work
    "Четыре часа работы. +$[job_rate]."
    return


## ================= Вечер =================

label evening:
    $ now_text = "19:00 · вечер"
    scene bg home_evening

    $ ev = take_event("evening")
    if ev:
        call expression ev

label evening_choice:
    $ todo = known_todo()
    $ can_meet = [p for p in STUDENT_ORDER if tier(p) >= 2]
    menu:
        "Вечер. Одно занятие."
        "Телефон (не тратит вечер)" if not phone_used:
            call phone_evening
            jump evening_choice
        "Сделать домашку" if todo:
            call do_homework
        "Учиться самому":
            call act_study
        "Поиграть":
            call act_games
        "Позвать кого-то встретиться ($1)" if can_meet and money >= 1 and not meeting_refused:
            call meeting(can_meet)
            if _return == "refused":
                jump evening_choice
        "Лечь пораньше":
            $ change("fatigue", -S)
            "Ты ложишься в девять. Вечер прошёл впустую, зато выспишься."
    return


## ----- Занятия: вечером и в воскресенье -----

label do_homework:
    $ todo = known_todo()
    if len(todo) == 1:
        $ h = todo[0]
    else:
        $ h = renpy.display_menu([(hw_title(x), x) for x in todo])
    $ h["done"] = True
    $ change("morale", -S)
    $ change("fatigue", +S)
    "Домашка по предмету «[h[subj]]» готова. Голова гудит."
    return


label act_study:
    $ change("know", +B)
    $ change("fatigue", +S)
    $ change("morale", -M)
    "Ты сидишь над конспектом, пока буквы не начинают плыть."
    return


label act_games:
    $ change("morale", +S, boredom_factor("games"))
    $ did_activity("games")
    $ change("fatigue", +M)
    if boredom.get("games", 0) >= 2:
        "Опять та же игра. Уже не так весело."
    else:
        "Пара каток — и настроение лучше."
    return


label meeting(can_meet):
    $ pid = renpy.display_menu([("{} — {}".format(who(p), tier_name(p)), p) for p in can_meet])
    $ nm = who(pid)
    $ renpy.show("plate " + pid)
    if pid == "n1" and line_ripe("n1", "evening"):
        $ line_steps_today += 1
        $ money_add(-1)
        call line_n1_step
        $ renpy.hide("plate")
        return "ok"
    $ chance = {2: 70, 3: 85, 4: 100}[tier(pid)]
    if not roll(chance):
        "«Сегодня не могу, извини»."
        $ change("morale", -M)
        $ meeting_refused = True
        $ renpy.hide("plate")
        return "refused"
    $ money_add(-1)
    $ rel(pid, +S)
    $ change("morale", +S, boredom_factor("meet"))
    $ did_activity("meet")
    $ change("fatigue", +M)
    "[nm] соглашается. Вы сидите в кафе и болтаете обо всём."
    $ renpy.hide("plate")
    return "ok"


label phone_evening:
    $ phone_used = True
    $ contacts = [p for p in STUDENT_ORDER if met(p)]
    if not contacts:
        "В телефоне пока нет номеров одногруппников."
        return
    $ pid = renpy.call_screen("phone", contacts=contacts)
    if pid is None:
        return
    $ nm = who(pid)
    if roll(talk_chance(pid)):
        $ rel(pid, +M)
        "[nm] отвечает сразу. Переписываетесь полчаса."
    else:
        $ change("morale", -M)
        "[nm]: «ок». И всё."
    return


## ================= Ночь =================

label night:
    $ now_text = "23:00 · ночь"
    scene bg night

    $ ev = take_event("night")
    if ev:
        call expression ev

    $ change_raw("fatigue", -15 if energy_drink else -20)
    if energy_drink:
        "Энергетик ещё бродит в крови. Сон рваный."

    ## Мораль на нуле: счётчик, предупреждение, «Ушёл сам» (core/endings.rpy).
    call morale_check
    if gave_up:
        return

    $ after_night_boredom()
    call screen day_summary
    return


## ================= Конец недели =================

label week_end:
    $ now_text = "итоги недели"
    scene bg home
    if gruzin_week and gruzin_sem_seen > 0 and not gruzin_sem_missed:
        $ rel("gruzin", +B)
        $ known_rules.add("gruzin_seminars")
        "Ты {g=была}был{/g} на всех семинарах Грузина за неделю. Кажется, он это запомнил."
    call screen week_summary

label week_menu:
    menu:
        "Что дальше?"
        "Прожить ещё неделю (обычную)":
            $ week += 1
            $ gruzin_week = False
        "Прожить ещё неделю (неделя Грузина)":
            $ week += 1
            $ gruzin_week = True
        "Экзамен Грузина (тест, ничего не меняет)":
            call gruzin_exam_test
            jump week_menu
        "В главное меню":
            return
    $ day = 1
    $ gruzin_sem_missed = False
    $ gruzin_sem_seen = 0
    jump day_loop
