# Roadmap полной совместимости

Уже есть:
- меню, freeplay, gameplay loop;
- внешняя папка `/data`;
- моды;
- FNF v2 chart/metadata loader;
- legacy chart loader;
- audio Inst + Voices;
- scoring/combo/accuracy/health;
- event dispatcher;
- визуальные графы событий;
- Tk chart editor;
- Tk mod wizard;
- проверка ассетов;
- PyInstaller build.

Следующий слой, если доводить до уровня “почти как официальный рантайм”:

1. Полная Animate Atlas анимация
   - читать `Animation.json`;
   - учитывать матрицы, symbols, frame scripts;
   - делать frame-perfect offsets.

2. Полная stage-система
   - все props из stage JSON;
   - parallax;
   - animated props;
   - camera beat zoom.

3. Cutscene runtime
   - диалоги;
   - scripted cameras;
   - video playback.

4. Shader compatibility
   - GLSL-пайплайн через OpenGL;
   - fallback для слабых машин.

5. Song variations
   - `erect`, `pico`, alt instrumentals;
   - автоматический выбор vocal stems.

6. Packaging
   - отдельный launcher;
   - мод-паки `.ffmod`;
   - marketplace-like index без чужих ассетов.
