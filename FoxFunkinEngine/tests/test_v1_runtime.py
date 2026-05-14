from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from foxfunkin.core.asset_manager import AssetManager
from foxfunkin.core.config import load_config
from foxfunkin.core.jsonx import save_json
from foxfunkin.core.paths import PathResolver, project_root
from foxfunkin.game.chart import load_chart
from foxfunkin.game.gameplay import GameplayState
from foxfunkin.game.song import discover_songs
from foxfunkin.game.visual_script import VisualGraphExecutor
from foxfunkin.tools.pack_mod import proprietary_hits


class V1RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((640, 480))
        cls.root = project_root()
        cls.config = load_config(cls.root)
        cls.resolver = PathResolver(cls.root, cls.config)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_song_discovery_and_variation_chart(self):
        songs = discover_songs(self.resolver)
        ids = {song.id for song in songs}
        self.assertIn("bopeebo", ids)
        chart = load_chart(self.resolver, "bopeebo", "normal")
        self.assertGreater(len(chart.notes), 20)
        self.assertIn("erect", chart.song.variations)
        variant = load_chart(self.resolver, "bopeebo", "erect", "erect")
        self.assertEqual(variant.variation, "erect")
        self.assertGreater(len(variant.notes), 20)

    def test_visual_graph_branch_and_variables(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph = root / "graphs" / "branch.fnvgraph.json"
            save_json(graph, {
                "nodes": [
                    {"id": "start", "type": "Start", "props": {}},
                    {"id": "set", "type": "SetVariable", "props": {"name": "flag", "value": True}},
                    {"id": "branch", "type": "Branch", "props": {"name": "flag", "op": "==", "value": True}},
                    {"id": "text", "type": "ShowText", "props": {"text": "ok", "duration": 1}},
                ],
                "links": [
                    {"from": "start", "to": "set"},
                    {"from": "set", "to": "branch"},
                    {"from": "branch", "fromPort": "true", "to": "text"},
                ],
            })
            resolver = SimpleNamespace(resolve=lambda p: (root / p) if (root / p).exists() else None)
            context = SimpleNamespace(script_variables={}, spawned=[], spawn_text=lambda text, duration=1: context.spawned.append(text))
            VisualGraphExecutor(resolver).run("graphs/branch.fnvgraph.json", context)
            self.assertEqual(context.spawned, ["ok"])

    def test_proprietary_path_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp) / "bad_mod"
            (mod / "songs" / "bopeebo").mkdir(parents=True)
            (mod / "songs" / "bopeebo" / "Inst.ogg").write_bytes(b"fake")
            self.assertTrue(proprietary_hits(mod))

    def test_gameplay_smoke_instantiates_example_mod(self):
        app = SimpleNamespace()
        app.root = self.root
        app.config = self.config
        app.resolver = self.resolver
        app.assets = AssetManager(self.resolver)
        app.input = SimpleNamespace(action_for_key=lambda key: None, lane_for_key=lambda key: None)
        app.screen = pygame.display.get_surface()
        app.states = SimpleNamespace(change=lambda *args, **kwargs: None)
        state = GameplayState(app)
        state.enter(song_id="fox-test", difficulty="normal")
        self.assertFalse(state.countdown_done)
        state.update(0.1)
        self.assertEqual(state.song_id, "fox-test")


if __name__ == "__main__":
    unittest.main()
