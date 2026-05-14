# Раскладка ассетов

Движок смотрит файлы в таком порядке:

1. `mods/<enabled_mod>/assets/`
2. `mods/<enabled_mod>/`
3. `data/`

Это значит: мод может переопределить любой файл из `/data`, положив файл по тому же относительному пути.

## Ожидаемая структура для funkin.assets

```text
data/
  preload/data/songs/<song>/<song>-metadata.json
  preload/data/songs/<song>/<song>-chart.json
  preload/data/characters/<character>.json
  preload/data/stages/<stage>.json
  shared/images/
  shared/sounds/
  shared/music/
  songs/<song>/Inst.ogg
  songs/<song>/Voices-bf.ogg
  songs/<song>/Voices-dad.ogg
```

Поддерживаются `.ogg`, `.mp3`, `.wav`.

## Имена assetPath

`shared:characters/gf` превращается в поиски:

```text
shared/images/characters/gf/spritemap1.png
shared/images/characters/gf/spritemap1.json
shared/images/characters/gf/Animation.json
shared/images/characters/gf.png
shared/images/characters/gf.xml
```

Sparrow XML и простой Animate Atlas JSON читаются частично: достаточно для отображения персонажа и смены анимаций по событиям. Для идеально точных Animate-анимаций нужен следующий слой совместимости.
