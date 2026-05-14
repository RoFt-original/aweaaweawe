# Визуальное программирование

Файл графа: `*.fnvgraph.json`.

Редактор открывается через `run_tools.bat` → Visual Programmer.

Событие в чарте может запускать граф:

```json
{ "t": 3200, "e": "RunGraph", "v": "graphs/intro.fnvgraph.json" }
```

## Узлы

- `Start`
- `ShowText`
- `CameraZoom`
- `ScreenShake`
- `SetScrollSpeed`
- `HealthChange`
- `PlayAnimation`
- `Wait`

Граф исполняется рантаймом как цепочка узлов по `links`. Это сделано специально приземлённо: моддер может собрать рабочую сцену без Python, а движок не превращается в цирк с пятью зависимостями и дымовой машиной.
