"""Named places (config "places") and weather written by code (cos/weather_answer.py).
Synthetic forecast data only (evals/fixtures/default/weather.json, a Thursday at 2:30 PM)."""
from __future__ import annotations

import contextlib
import io
import json
import os
from unittest import mock

from support import REPO_ROOT, StateDirTest

from cos import cli, fixture
from cos.config import ConfigError, Place, load_config, resolve_places
from cos.model import ModelClient
from cos.weather_answer import parse, render, unknown_place_answer

FIXTURES = REPO_ROOT / "evals" / "fixtures" / "default"
SIMS = Place("home", "Sims, NC", 35.76, -78.06)
CLAYTON = Place("work", "Clayton, NC", 35.65, -78.46)
PLACES = {"home": SIMS, "work": CLAYTON}
# The exact lines Owen adds to config.json (CHIEF-OF-STAFF.md "Weather places").
OWEN_PLACES = {"home": {"name": "Sims, NC", "latitude": 35.76, "longitude": -78.06},
               "work": {"name": "Clayton, NC", "latitude": 35.65, "longitude": -78.46}}


class PlacesConfigTests(StateDirTest):
    def load(self, data):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "config.json").write_text(json.dumps(data))
        return load_config()

    def test_new_install_defaults(self):
        self.assertEqual(load_config().places, PLACES)

    def test_owens_current_config_migrates_without_inventing_a_city(self):
        cfg = self.load({"latitude": 35.76, "longitude": -78.06})
        self.assertEqual(cfg.places["home"], Place("home", "Home", 35.76, -78.06))
        self.assertEqual(cfg.places["work"], CLAYTON)

    def test_owens_documented_lines(self):
        self.assertEqual(self.load({"latitude": 35.76, "longitude": -78.06, "places": OWEN_PLACES}).places, PLACES)
        self.assertEqual(self.load({"places": OWEN_PLACES}).places, PLACES)

    def test_written_home_is_used_as_written(self):
        places = self.load({"latitude": 1, "longitude": 2,
                            "places": {"home": {"name": "Test Town A", "latitude": 10, "longitude": 20}}}).places
        self.assertEqual(places, {"home": Place("home", "Test Town A", 10.0, 20.0)})  # no default work either

    def test_places_without_home_use_the_legacy_coordinates(self):
        places = resolve_places({"work": OWEN_PLACES["work"]}, 35.76, -78.06)
        self.assertEqual(list(places), ["home", "work"])
        self.assertEqual(places["home"].name, "Home")

    def test_bad_places_are_refused(self):
        bad = ({"places": []}, {"places": {"Home": OWEN_PLACES["home"]}},
               {"places": {"home": {**OWEN_PLACES["home"], "zip": "27591"}}},
               {"places": {"home": {"name": "Sims, NC", "latitude": 95, "longitude": 0}}},
               {"places": {"home": {"name": "", "latitude": 1, "longitude": 1}}},
               {"places": {"home": {"name": "Sims, NC", "latitude": 1}}},
               {"place": OWEN_PLACES})
        for data in bad:
            with self.subTest(data=data), self.assertRaises(ConfigError):
                self.load(data)

    def test_weather_tool_offers_the_place_keys(self):
        cfg = self.config(fixture_dir=FIXTURES, places=PLACES)
        reg = fixture.build_fixture_registry(fixture.fixture_context(cfg))
        tool = reg.get("weather.today")
        self.assertEqual(tool.parameters["properties"]["place"]["enum"], ["home", "work"])
        self.assertEqual({k: tool.func({"place": "work"})[k] for k in ("place", "place_key")},
                         {"place": "Clayton, NC", "place_key": "work"})
        self.assertEqual(tool.func({})["place"], "Sims, NC")


class WeatherAnswerTests(StateDirTest):
    def setUp(self):
        super().setUp()
        cfg = self.config(fixture_dir=FIXTURES, places=PLACES)
        self.tool = fixture.build_fixture_registry(fixture.fixture_context(cfg)).get("weather.today")

    def say(self, question, previous=None):
        req = parse(question, PLACES, previous)
        if req is None:
            return unknown_place_answer(PLACES)
        return render(req, self.tool.func({"place": req.place.key}), PLACES)[0]

    def test_now_begins_with_the_place(self):
        for q in ("weather", "what's the weather like today?", "make sure you tell me the city", "do that for me"):
            with self.subTest(q=q):
                self.assertTrue(self.say(q).startswith("Sims, NC — 68°F, partly cloudy. High 74° · Low 55° · Rain 20%."))

    def test_spans(self):
        cases = {
            "what about tomorrow": "Sims, NC — Tomorrow (Friday): high 66°, low 48°, light rain. Rain 60%.",
            "will it rain on saturday": "Sims, NC — Saturday: high 70°, low 50°, partly cloudy. Rain 30%.",
            "how's the weather this weekend": ("Sims, NC — This weekend: Saturday: high 70°, low 50°, partly cloudy. "
                                               "Rain 30%. · Sunday: high 72°, low 53°, mostly clear. Rain 10%."),
            "a week from saturday?": ("Sims, NC — I only have a 7-day forecast, through Wednesday, October 7. "
                                      "There's no forecast beyond that."),
            "what was the weather yesterday": "Sims, NC — I don't have past weather, only today and the next 6 days.",
            "hourly weather": "Sims, NC — Next 12 hours: 2 PM 68° · 5 PM 68° · 8 PM 61° · 11 PM 58°. Rain up to 25%.",
            "how cold will it get tonight": "Sims, NC — Tonight: low 55°.",
        }
        for q, want in cases.items():
            with self.subTest(q=q):
                self.assertTrue(self.say(q).startswith(want), self.say(q))
        five = self.say("5 day forecast")
        self.assertTrue(five.startswith("Sims, NC — 5-day forecast:\nToday: high 74°, low 55°, overcast. Rain 20%.\n"
                                        "Tomorrow: high 66°, low 48°, light rain. Rain 60%.\nSaturday:"), five)
        self.assertEqual(five.count("\n"), 5)
        nxt = self.say("what's the weather going to be next week")
        self.assertIn("I only have a forecast through Wednesday, October 7. Monday:", nxt)

    def test_places(self):
        self.assertTrue(self.say("weather at work").startswith("Clayton, NC — 68°F"))
        self.assertTrue(self.say("is it raining at school?").startswith("Clayton, NC — "))
        self.assertTrue(self.say("clayton weather tomorrow").startswith("Clayton, NC — Tomorrow"))
        self.assertTrue(self.say("and tomorrow?", previous="weather at work").startswith("Clayton, NC — Tomorrow"))
        for q in ("weather in raleigh", "what's the weather in Test City Z", "forecast for paris"):
            with self.subTest(q=q):
                self.assertEqual(self.say(q), "I only know Sims (home) and Clayton (work) so far.")
        for q in ("weather for saturday's field trip", "rain at recess tomorrow", "weather in the morning"):
            with self.subTest(q=q):
                self.assertTrue(self.say(q).startswith("Sims, NC — "), q)

    def test_city_and_location_notes(self):
        city = self.say("what city is that")
        self.assertIn("That's Sims, NC, your saved home place.", city)
        loc = self.say("use my location")
        self.assertTrue(loc.startswith("Sims, NC — "))
        self.assertIn("not your Mac's location: Sims (home) and Clayton (work)", loc)
        self.assertIn("config.json", loc)
        for text in (city, loc):
            self.assertNotRegex(text.lower(), r"settings (?:screen|>|→)|open settings|preferences")

    def test_jacket_and_umbrella(self):
        self.assertIn("No jacket needed: it feels like 67°F.", self.say("do the kids need jackets for recess?"))
        self.assertIn("Jacket weather in the morning (low 48°).", self.say("will it be cold tomorrow morning?"))
        self.assertIn("Bring an umbrella.", self.say("do I need an umbrella tomorrow"))

    def test_tool_error(self):
        req = parse("weather", PLACES)
        self.assertEqual(render(req, {"error": "fixture weather.json not present"}, PLACES)[0],
                         "Weather is unavailable for Sims, NC: fixture weather.json not present.")


class WeatherPathTests(StateDirTest):
    def ask(self, *questions, session=True):
        os.environ["COS_FIXTURE_DIR"] = str(FIXTURES)
        self.addCleanup(os.environ.pop, "COS_FIXTURE_DIR", None)
        out = []
        with mock.patch.object(ModelClient, "chat", side_effect=AssertionError("no model on weather turns")):
            for q in questions:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    argv = ["ask"] + (["--session", "wx"] if session else []) + ["--json", "--", q]
                    self.assertEqual(cli.main(argv), 0)
                out.append(json.loads(buf.getvalue()))
        return out

    def test_owens_transcript_names_sims_with_no_model(self):
        answers = self.ask("weather", "make sure you tell me the city", "use my location", "do that for me")
        for res in answers:
            self.assertTrue(res["answer"].startswith("Sims, NC — "), res["answer"])
            self.assertEqual((res["intent"], res["tools_used"], res["fast_path"], res["model"]),
                             ("weather", ["weather.today"], True, None))
            self.assertNotIn("settings screen", res["answer"])

    def test_unknown_place_runs_no_tool(self):
        res = self.ask("weather in raleigh", session=False)[0]
        self.assertEqual((res["answer"], res["tools_used"]), ("I only know Sims (home) and Clayton (work) so far.", []))
