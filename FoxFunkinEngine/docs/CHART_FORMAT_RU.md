# Форматы чартов

Поддерживаются:

1. FNF v2:
   - `preload/data/songs/<song>/<song>-chart.json`
   - `preload/data/songs/<song>/<song>-metadata.json`

2. Legacy/Psych-like:
   - JSON с корневым ключом `song`;
   - секции `notes`;
   - `sectionNotes`.

Конвертер встроен в `foxfunkin.game.chart.LegacyChartAdapter`.

Точное правило:
- FNF v2 хранит абсолютное время в миллисекундах (`t`);
- `l` — длина sustain-ноты;
- `d` 0-7, где 4-7 — сторона игрока.
