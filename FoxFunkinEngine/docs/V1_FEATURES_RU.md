# FoxFunkin Engine v1

## Что входит

- ПК-рантайм на Python/Pygame с Freeplay, Story Mode, Mods, Options, Results и Asset Check.
- Загрузка FNF v2 song metadata/chart JSON, legacy/Psych-like chart JSON, song variations (`pico`, `erect`) и локальных аудио stems.
- Поддержка локальной папки `data/` и overlay модов: `mods/<enabled>/assets`, затем `mods/<enabled>`, затем `data/`.
- Моддинг v1 через `manifest.json`: `id`, `title`, `version`, `author`, `description`, `dependencies`, `priority`, `entryGraphs`.
- Визуальные графы `*.fnvgraph.json` с узлами `Start`, `OnBeat`, `OnStep`, `OnNoteHit`, `ShowText`, `CameraZoom`, `ScreenShake`, `SetScrollSpeed`, `HealthChange`, `PlayAnimation`, `SetVariable`, `Branch`, `PlaySound`, `StageProp`, `Wait`.
- Чарт-редактор с выбором сложности, note lanes, event lane, sustain editing, быстрым metadata scratchpad и аудио-превью.
- Mod Wizard для создания рабочего мини-мода с оригинальным placeholder audio.
- `.ffmod.zip` упаковка через `python -m foxfunkin.tools.pack_mod <mod_id>`.
- Локальный импорт funkin.assets через `import_assets.bat <path-to-funkin.assets>`.
- Сборка публичного релиза через `build_release.bat`; локальная приватная сборка с ассетами через `build_release.bat --with-local-data`.

## Важно про ассеты

Публичный релиз не копирует `data/`, потому что оригинальные `funkin.assets` нельзя свободно распространять от имени проекта. Для себя можно держать их локально в `data/` или импортировать из локального checkout.

## Быстрая проверка

```bat
run_tests.bat
check_assets.bat
run.bat
run_tools.bat
build_release.bat
```

Мини-мод создается через `create_mod.bat` или вкладку Mod Wizard в `run_tools.bat`.
