# FoxFunkin Engine

Фан-движок в стиле Friday Night Funkin’ для Windows/ПК: отдельный рантайм, внешний `/data`, моды в `/mods`, визуальные события, редактор чартов и `.bat` для сборки `.exe`.

Важный момент, без канцелярского душа, но всё же: я не вшивал оригинальные ассеты FNF. Репозиторий `FunkinCrew/funkin.assets` сам говорит, что это содержимое папки `assets` игры, а лицензия у этих файлов отдельная. Ассеты кладутся пользователем локально в `/data`, а в GitHub-проект коммитится только код движка и твои собственные моды.

## Быстрый запуск

1. Установи Python 3.11+ на Windows.
2. Запусти `run.bat`.
3. Движок создаст `.venv`, поставит `pygame` и откроется.
4. Без внешних ассетов он запустит плейсхолдеры и примерный `example_10min_mod`.

## Подключить ассеты из funkin.assets

Содержимое репозитория ассетов надо положить так:

```text
FoxFunkinEngine/
  data/
    preload/
    shared/
    songs/
    fonts/
    tutorial/
    week1/
    week2/
    week3/
    ...
```

После копирования запусти `check_assets.bat`. Он проверит, что есть `preload/data/songs`, `preload/data/characters`, `shared/images`, `songs`.

## Сборка exe

Запусти:

```bat
build_exe.bat
```

Получишь:

```text
dist/FoxFunkinEngine.exe
dist/data/
dist/mods/
```

Потом внешние ассеты кладёшь в `dist/data/`, а моды — в `dist/mods/`.

## Моддинг за 10 минут

Запусти `create_mod.bat` или `run_tools.bat`.

Что уже есть:
- мастер создания мода;
- чарт-редактор на сетке;
- визуальное программирование событий;
- поддержка `manifest.json`;
- приоритет модов над `/data`;
- JSON-чарты формата FNF v2 (`*-chart.json`, `*-metadata.json`);
- базовая поддержка legacy/Psych-like chart JSON;
- внешняя папка `/songs/<song>/Inst.ogg|mp3|wav`;
- player/opponent lanes, hit windows, score/combo/accuracy/health;
- events: `FocusCamera`, `PlayAnimation`, `CameraZoom`, `ScreenShake`, `SetScrollSpeed`, `SpawnText`, `RunGraph`.

## Управление

- Меню: стрелки/WASD, Enter, Esc.
- Игра: A/S/W/D или стрелки.
- Pause: Enter.
- Back: Esc.

## Структура мода

```text
mods/my_mod/
  manifest.json
  preload/data/songs/my-song/my-song-metadata.json
  preload/data/songs/my-song/my-song-chart.json
  songs/my-song/Inst.ogg
  songs/my-song/Voices-bf.ogg
  graphs/intro.fnvgraph.json
```

## Честная техническая грань

Это не форк официального исходника и не запакованная копия FNF. Это самостоятельный Python/Pygame-рантайм, настроенный на структуру `funkin.assets` и на моддинг. Физика тайминга, FNF v2 chart data, внешние ассеты, меню, freeplay, моды и визуальные события уже собраны в рабочий проект. Некоторые точные штуки оригинала вроде полного Haxe/Flixel-пайплайна, всех шейдеров, Animate Atlas fidelity до пикселя и сложных cutscene-сценариев вынесены в `docs/ROADMAP_FULL_COMPAT_RU.md`, потому что иначе мы бы притворялись, что за один удар молотком построили собор. Милый самообман, но всё-таки самообман.
