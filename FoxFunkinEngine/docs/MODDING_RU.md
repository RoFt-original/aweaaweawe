# Моддинг

Минимальный мод:

```text
mods/my_mod/
  manifest.json
  preload/data/songs/test/test-metadata.json
  preload/data/songs/test/test-chart.json
  songs/test/Inst.ogg
```

`manifest.json`:

```json
{
  "id": "my_mod",
  "title": "My Mod",
  "version": "1.0.0",
  "author": "me",
  "enabled": true,
  "description": "tiny test"
}
```

Чтобы мод появился, включи его в меню Mods или добавь ID в `settings.json`:

```json
"mods": { "enabled": ["my_mod"] }
```

## Формат чарта v2

```json
{
  "version": "2.0.0",
  "scrollSpeed": { "normal": 1.6 },
  "events": [
    { "t": 0, "e": "FocusCamera", "v": 1 }
  ],
  "notes": {
    "normal": [
      { "t": 1200, "d": 4 },
      { "t": 1600, "d": 5, "l": 300 }
    ]
  }
}
```

`d`:
- 0-3 — opponent lanes;
- 4-7 — player lanes;
- `d % 4` даёт направление: left/down/up/right.

## Метаданные песни

```json
{
  "version": "2.2.4",
  "songName": "Test",
  "artist": "You",
  "charter": "You",
  "playData": {
    "difficulties": ["normal"],
    "characters": {
      "player": "bf",
      "girlfriend": "gf",
      "opponent": "dad"
    },
    "stage": "mainStage",
    "noteStyle": "funkin"
  },
  "timeChanges": [{ "t": 0, "b": 0, "bpm": 120, "bt": [4, 4, 4, 4] }]
}
```
