from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.render_ass import (
    SubtitleEvent,
    build_track_style_overrides,
    infer_style,
    parse_track_color_args,
    render_ass,
    resolve_event_style_override,
    style_name_for_speaker,
    style_name_for_track,
)
from src.subtitle_workflow import build_project_ass
from tests.typed_case import TypedTestCase


class RenderAssExtraTests(TypedTestCase):
    def test_cli_renders_raw_transcript_with_typed_arguments(self) -> None:
        segments: list[dict[str, object]] = [
            {
                "start": 0,
                "end": 1,
                "text": "字幕",
                "speaker": None,
                "source_track": "0:a:1",
                "layout_packed": True,
            }
        ]
        payload: dict[str, object] = {"segments": segments}
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript_path = Path(temp_dir) / "transcript.json"
            ass_path = Path(temp_dir) / "subtitle.ass"
            transcript_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            subprocess.run(
                (
                    sys.executable,
                    "-m",
                    "src.render_ass",
                    "--input",
                    str(transcript_path),
                    "--output",
                    str(ass_path),
                    "--track-color",
                    "0:a:1=#AABBCC",
                ),
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            ass = ass_path.read_text(encoding="utf-8")
            self.assertIn("Style: Track_0_a_1", ass)
            self.assertIn(",None,0,0,", ass)
            self.assertIn("字幕", ass)

    def test_parse_track_color_args_parses_multiple_tracks(self) -> None:
        result = parse_track_color_args(["Track1=#AABBCC", "  Track2 = #DDEEFF "])
        expected = {"Track1": "#AABBCC", "Track2": "#DDEEFF"}
        self.assertEqual(result, expected)

    def test_parse_track_color_args_rejects_missing_equals(self) -> None:
        with self.assertRaises(SystemExit):
            parse_track_color_args(["Track1#AABBCC"])

    def test_style_name_for_track(self) -> None:
        self.assertEqual(style_name_for_track("Track 1"), "Track_Track_1")
        self.assertEqual(style_name_for_track(""), "Track_track")

    def test_style_name_for_track_keeps_non_ascii_craig_tracks_distinct(self) -> None:
        taro_style = style_name_for_track("craig:たろう")
        hanako_style = style_name_for_track("craig:はなこ")
        self.assertNotEqual(taro_style, hanako_style)
        self.assertTrue(taro_style.startswith("Track_craig_たろう_"))
        self.assertTrue(hanako_style.startswith("Track_craig_はなこ_"))

        data: dict[str, object] = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.5,
                    "text": "こんにちは",
                    "speaker": "Oz",
                    "source_speaker": "たろう",
                    "source_track": "craig:たろう",
                },
                {
                    "start": 2.0,
                    "end": 3.5,
                    "text": "よろしく",
                    "speaker": "A",
                    "source_speaker": "はなこ",
                    "source_track": "craig:はなこ",
                },
            ]
        }
        ass = render_ass(
            data,
            speaker_color_map={},
            track_color_map={"craig:たろう": "#FF0000", "craig:はなこ": "#0000FF"},
        )
        self.assertIn(f"Style: {taro_style},", ass)
        self.assertIn(f"Style: {hanako_style},", ass)
        self.assertIn("&H000000FF", ass)
        self.assertIn("&H00FF0000", ass)

        with tempfile.TemporaryDirectory() as tmp:
            project: dict[object, object] = {
                "version": 1,
                "video": {
                    "path": "dummy.mp4",
                    "width": 1920,
                    "height": 1080,
                    "fps": 30.0,
                    "duration": 10.0,
                },
                "speakers": [
                    {
                        "id": "craig:たろう",
                        "name": "たろう",
                        "style": "Oz",
                        "color": "#FF0000",
                        "track_key": "craig:たろう",
                    },
                    {
                        "id": "craig:はなこ",
                        "name": "はなこ",
                        "style": "A",
                        "color": "#0000FF",
                        "track_key": "craig:はなこ",
                    },
                ],
                "segments": data["segments"],
                "settings": {},
            }
            project_path = Path(tmp) / "subtitle_project.json"
            ass_path = Path(tmp) / "out.ass"
            build_project_ass(project_path, output_path=ass_path, _project=project)
            project_ass = ass_path.read_text(encoding="utf-8")
            self.assertIn("&H000000FF", project_ass)
            self.assertIn("&H00FF0000", project_ass)

    def test_style_name_for_speaker_escapes_and_hashes(self) -> None:
        self.assertTrue(style_name_for_speaker("A/B C").startswith("Speaker_A_B_C"))
        special = style_name_for_speaker("🎮")
        self.assertTrue(special.startswith("Speaker_speaker_"))

    def test_resolve_event_style_override_prefers_speaker_file_then_speaker(self) -> None:
        event = SubtitleEvent(
            start=0.0,
            end=1.0,
            text="hi",
            speaker="Oz",
            metadata={
                "source_file": " clip1.mp4 ",
                "source_speaker": "Alice",
                "source_track": "Track1",
            },
        )
        speaker_map = {"clip1.mp4": "#AABBCC", "alice": "#DDEEFF"}
        track_map = {"Track1": "#112233"}
        override = resolve_event_style_override(event, speaker_color_map=speaker_map, track_color_map=track_map)
        self.assertIsNotNone(override)
        if override is None:
            self.fail("話者色の上書きが見つかりませんでした")
        style, color = override
        self.assertEqual(color, "#AABBCC")

    def test_resolve_event_style_override_falls_back_to_track(self) -> None:
        event = SubtitleEvent(
            start=0.0,
            end=1.0,
            text="hi",
            speaker="Oz",
            metadata={"source_track": "Track1"},
        )
        track_map = {"Track1": "#112233"}
        override = resolve_event_style_override(event, track_color_map=track_map)
        self.assertEqual(override, ("Track_Track1", "#112233"))

    def test_resolve_event_style_override_returns_none(self) -> None:
        event = SubtitleEvent(start=0.0, end=1.0, text="hi", speaker="Oz", metadata={})
        self.assertIsNone(resolve_event_style_override(event))

    def test_infer_style_applies_speaker_color_override(self) -> None:
        event = SubtitleEvent(
            start=0.0,
            end=1.0,
            text="hi",
            speaker="Oz",
            metadata={"source_file": "clip1"},
        )
        result = infer_style(event, speaker_color_map={"clip1": "#AABBCC"})
        self.assertEqual(result, "Speaker_clip1")

    def test_infer_style_applies_shout_to_override(self) -> None:
        event = SubtitleEvent(
            start=0.0,
            end=1.0,
            text="hi",
            speaker="Oz",
            emphasis="shout",
            metadata={"source_file": "clip1"},
        )
        result = infer_style(event, speaker_color_map={"clip1": "#AABBCC"})
        self.assertEqual(result, "ShoutSpeaker_clip1")

    def test_build_track_style_overrides_collects_unique_pairs(self) -> None:
        events = [
            SubtitleEvent(
                start=0.0,
                end=1.0,
                text="a",
                speaker="Oz",
                metadata={"source_file": "clip1"},
            ),
            SubtitleEvent(
                start=1.0,
                end=2.0,
                text="b",
                speaker="Oz",
                emphasis="shout",
                metadata={"source_file": "clip1"},
            ),
        ]
        overrides = build_track_style_overrides(events, speaker_color_map={"clip1": "#AABBCC"})
        self.assertEqual(overrides["Speaker_clip1"], ("Oz", "#AABBCC"))
        self.assertEqual(overrides["ShoutSpeaker_clip1"], ("ShoutOz", "#AABBCC"))

    def test_render_ass_applies_speaker_color_map_without_source_speaker(self) -> None:
        data: dict[str, object] = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": "手動追加セリフ",
                    "speaker": "Alice",
                }
            ]
        }
        ass = render_ass(data, speaker_color_map={"alice": "#00FF00"})
        self.assertIn("Style: Speaker_Alice,", ass)
        self.assertIn("&H0000FF00", ass)
        self.assertIn(",Speaker_Alice,Alice,0,0,", ass)

    def test_render_ass_does_not_treat_none_source_speaker_as_literal_none(self) -> None:
        data: dict[str, object] = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": "ホスト発話",
                    "speaker": "Oz",
                    "source_track": "0:a:1",
                    "source_speaker": None,
                }
            ]
        }
        ass = render_ass(data, speaker_color_map={"none": "#FF00FF"})
        self.assertNotIn("Speaker_None", ass)
        self.assertIn(",Oz,Oz,0,0,", ass)

    def test_project_track_color_takes_precedence_over_default_speaker_colors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project: dict[object, object] = {
                "version": 1,
                "video": {
                    "path": "dummy.mp4",
                    "width": 1920,
                    "height": 1080,
                    "fps": 30.0,
                    "duration": 10.0,
                },
                "speakers": [
                    {
                        "id": "craig:alice",
                        "name": "alice",
                        "file_name": "1-alice.aac",
                        "style": "Oz",
                        "color": "#00FF00",
                        "track_key": "craig:alice",
                    }
                ],
                "segments": [
                    {
                        "start": 0.0,
                        "end": 1.5,
                        "text": "テスト",
                        "speaker": "Oz",
                        "source_file": "1-alice.aac",
                        "source_speaker": "alice",
                        "source_track": "craig:alice",
                    }
                ],
                "settings": {},
            }
            project_path = Path(tmp) / "subtitle_project.json"
            ass_path = Path(tmp) / "out.ass"

            def fake_load() -> dict[str, str]:
                return {"1-alice.aac": "#FF0000", "alice": "#FF0000"}

            with mock.patch("src.render_ass.load_speaker_color_map", side_effect=fake_load):
                build_project_ass(project_path, output_path=ass_path, _project=project)
            project_ass = ass_path.read_text(encoding="utf-8")
            self.assertIn("&H0000FF00", project_ass)
            self.assertNotIn("&H000000FF", project_ass)


if __name__ == "__main__":
    unittest.main()
