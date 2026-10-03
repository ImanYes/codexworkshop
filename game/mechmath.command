#!/bin/bash
# Мехмат: первый курс — бета-тест. Двойной клик по файлу = игра запускается.
# Первый раз скачает Ren'Py (движок) и игру, дальше только обновляет игру.
# Всё лежит в ~/.mechmath — в систему ничего не ставится. Сохранения Ren'Py хранит отдельно
# (~/Library/RenPy/), обновление игры их не стирает.

REPO="ImanYes/codexworkshop"
BRANCH="${MECHMATH_BRANCH:-claude/quirky-knuth-fmz9wh}"
BASE="$HOME/.mechmath"
GAME="$BASE/game"
SDK="$BASE/renpy-sdk"

say() { printf '\n== %s\n' "$*"; }
die() { printf '\n!! %s\n\nНажми Enter, чтобы закрыть окно.\n' "$*"; read -r _; exit 1; }

find_sdk() {
  local d
  for d in "$SDK" "$HOME"/renpy-*-sdk "$HOME"/Downloads/renpy-*-sdk /Applications/renpy-*-sdk; do
    if [ -x "$d/renpy.sh" ]; then echo "$d"; return 0; fi
  done
  return 1
}

download_sdk() {
  local v best="" versions
  versions=$(curl -fsSL https://www.renpy.org/dl/ | grep -oE 'href="8\.[0-9]+\.[0-9]+/"' \
    | grep -oE '8\.[0-9]+\.[0-9]+' | sort -u -t. -k1,1n -k2,2n -k3,3n | tail -5)
  for v in $versions; do   # по возрастанию: последняя найденная и есть самая новая
    curl -fs -r 0-0 -o /dev/null "https://www.renpy.org/dl/$v/renpy-$v-sdk.tar.bz2" && best="$v"
  done
  [ -n "$best" ] || return 1
  say "Скачиваю Ren'Py $best (движок игры), один раз, около 200 МБ"
  curl -fL --progress-bar -o "$BASE/renpy.tar.bz2" "https://www.renpy.org/dl/$best/renpy-$best-sdk.tar.bz2" || return 1
  rm -rf "$SDK" "$BASE/renpy-tmp"; mkdir -p "$BASE/renpy-tmp"
  tar -xjf "$BASE/renpy.tar.bz2" -C "$BASE/renpy-tmp" || return 1
  mv "$BASE"/renpy-tmp/renpy-* "$SDK" || return 1
  rm -rf "$BASE/renpy-tmp" "$BASE/renpy.tar.bz2"
}

fetch_game() {
  local tmp="$BASE/tmp-game" src
  rm -rf "$tmp"; mkdir -p "$tmp"
  curl -fsSL -o "$tmp/g.zip" "https://codeload.github.com/$REPO/zip/refs/heads/$BRANCH" || return 1
  unzip -q "$tmp/g.zip" -d "$tmp" || return 1
  src=$(ls -d "$tmp"/*/game/mehmat 2>/dev/null | head -1)
  [ -f "$src/game/script.rpy" ] || return 1
  rm -rf "$GAME"; mv "$src" "$GAME"; rm -rf "$tmp"
}

mkdir -p "$BASE"

say "Ren'Py (движок)"
RENPY_DIR=$(find_sdk)
if [ -z "$RENPY_DIR" ]; then
  download_sdk || die "Не получилось скачать Ren'Py. Скачай Ren'Py 8 вручную с renpy.org, распакуй в папку $SDK (внутри должен лежать файл renpy.sh) и запусти это ещё раз."
  RENPY_DIR="$SDK"
fi
echo "Нашёл: $RENPY_DIR"

say "Игра (ветка $BRANCH)"
if fetch_game; then
  echo "Обновил: $GAME"
elif [ -f "$GAME/game/script.rpy" ]; then
  echo "Нет интернета или GitHub не отвечает — запускаю ту версию, что уже скачана."
else
  die "Не получилось скачать игру, и старой копии нет. Проверь интернет и запусти ещё раз."
fi

say "Проверка кода (lint) — подробности в $BASE/lint.log"
"$RENPY_DIR/renpy.sh" "$GAME" lint > "$BASE/lint.log" 2>&1
tail -n 3 "$BASE/lint.log"

say "Запускаю игру"
"$RENPY_DIR/renpy.sh" "$GAME"

if [ -s "$GAME/traceback.txt" ]; then
  cp "$GAME/traceback.txt" "$BASE/last-traceback.txt"
  printf '\nИгра упала с ошибкой. Пришли файл: %s\n' "$BASE/last-traceback.txt"
  echo "Нажми Enter, чтобы закрыть окно."; read -r _
fi
