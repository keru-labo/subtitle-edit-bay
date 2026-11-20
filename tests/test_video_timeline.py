from __future__ import annotations

import unittest
import tempfile
import json
from itertools import combinations_with_replacement
from pathlib import Path
from unittest.mock import patch

from src.data_boundary import is_object_list, is_object_mapping
from src.subtitle_project import SubtitleProjectError, create_project, load_project, save_project
from src.video_timeline import (
    VideoTimeline,
    VideoTimelineError,
    timeline_from_project,
)
from tests.typed_case import TypedTestCase


class VideoTimelineTests(TypedTestCase):
    def test_small_tick_cut_pairs_match_independent_bitmap_oracle(self) -> None:
        """Bounded reference check; endpoints are intentionally excluded.

        At cut boundaries the forward mapping collapses removed points to the
        seam, while the inverse mapping selects the next keep range.
        """
        tick = 0.1
        cell_count = 6
        duration = round(tick * cell_count, 3)
        intervals = [
            (start, end)
            for start in range(cell_count)
            for end in range(start + 1, cell_count + 1)
            if end - start < cell_count
        ]

        def seconds(value: int) -> float:
            return round(value * tick, 3)

        def bitmap_ranges(mask: list[bool], removed: bool) -> list[tuple[float, float]]:
            ranges: list[tuple[float, float]] = []
            index = 0
            while index < cell_count:
                if mask[index] != removed:
                    index += 1
                    continue
                start = index
                while index < cell_count and mask[index] == removed:
                    index += 1
                ranges.append((seconds(start), seconds(index)))
            return ranges

        for (first_start, first_end), (second_start, second_end) in combinations_with_replacement(intervals, 2):
            cut_mask = [
                first_start <= index < first_end or second_start <= index < second_end
                for index in range(cell_count)
            ]
            timeline = VideoTimeline(source_duration=duration).add_cut(
                seconds(first_start), seconds(first_end), cut_id="first"
            )
            if all(cut_mask):
                with self.assertRaisesRegex(VideoTimelineError, "entire video"):
                    timeline.add_cut(
                        seconds(second_start), seconds(second_end), cut_id="second"
                    )
                continue
            timeline = timeline.add_cut(
                seconds(second_start), seconds(second_end), cut_id="second"
            )

            expected_cuts = bitmap_ranges(cut_mask, True)
            expected_keeps = bitmap_ranges(cut_mask, False)
            actual_cuts = [(cut.source_start, cut.source_end) for cut in timeline.cuts]
            self.assertEqual(actual_cuts, expected_cuts)
            self.assertEqual(timeline.keep_ranges, expected_keeps)
            expected_output_duration = (cell_count - sum(cut_mask)) * tick
            self.assertAlmostEqual(timeline.removed_duration, sum(cut_mask) * tick, places=3)
            self.assertAlmostEqual(timeline.output_duration, expected_output_duration, places=3)

            # Sample strictly inside source cells, not at cut or keep endpoints.
            for cell, is_cut in enumerate(cut_mask):
                for fraction in (0.2, 0.5, 0.8):
                    source_point = seconds(cell) + tick * fraction
                    output_cells_before = sum(not cut_mask[index] for index in range(cell))
                    offset = tick * fraction
                    expected_output = output_cells_before * tick + (0.0 if is_cut else offset)
                    self.assertAlmostEqual(
                        timeline.source_to_output_seconds(source_point), expected_output, places=3
                    )
                    self.assertEqual(timeline.contains_source_seconds(source_point), is_cut)

            # Output samples are interior to keep cells; inverse mapping is unique there.
            output_cell = 0
            for source_cell, is_cut in enumerate(cut_mask):
                if is_cut:
                    continue
                for fraction in (0.2, 0.5, 0.8):
                    output_point = output_cell * tick + tick * fraction
                    expected_source = source_cell * tick + tick * fraction
                    self.assertAlmostEqual(
                        timeline.output_to_source_seconds(output_point), expected_source, places=3
                    )
                output_cell += 1

    def test_cut_pairs_cannot_remove_all_media(self) -> None:
        timeline = VideoTimeline(source_duration=0.6).add_cut(0.0, 0.3, cut_id="left")
        with self.assertRaisesRegex(VideoTimelineError, "entire video"):
            timeline.add_cut(0.3, 0.6, cut_id="right")
        with self.assertRaisesRegex(VideoTimelineError, "entire video"):
            VideoTimeline(source_duration=0.6).add_cut(0.0, 0.6, cut_id="whole")

    def test_mapping_endpoint_seams_head_tail_cuts_and_out_of_bounds_clamping(self) -> None:
        timeline = VideoTimeline.from_json(
            {
                "cuts": [
                    {"id": "head", "source_start": 0.0, "source_end": 1.0},
                    {"id": "middle", "source_start": 3.0, "source_end": 4.0},
                    {"id": "tail", "source_start": 8.0, "source_end": 10.0},
                ]
            },
            source_duration=10.0,
        )

        # Both endpoints of each cut collapse to its output seam.
        self.assertEqual(timeline.source_to_output_seconds(0.0), 0.0)
        self.assertEqual(timeline.source_to_output_seconds(1.0), 0.0)
        self.assertEqual(timeline.source_to_output_seconds(3.0), 2.0)
        self.assertEqual(timeline.source_to_output_seconds(4.0), 2.0)
        self.assertEqual(timeline.source_to_output_seconds(8.0), 6.0)
        self.assertEqual(timeline.source_to_output_seconds(10.0), 6.0)

        # At an interior output seam, inverse mapping chooses the next kept source range.
        self.assertEqual(timeline.output_to_source_seconds(0.0), 1.0)
        self.assertEqual(timeline.output_to_source_seconds(2.0), 4.0)
        self.assertEqual(timeline.output_to_source_seconds(6.0), 10.0)

        # Mappings clamp positions outside their source/output domains.
        self.assertEqual(timeline.source_to_output_seconds(-1.0), 0.0)
        self.assertEqual(timeline.source_to_output_seconds(11.0), 6.0)
        self.assertEqual(timeline.output_to_source_seconds(-1.0), 1.0)
        self.assertEqual(timeline.output_to_source_seconds(7.0), 10.0)

    def test_unknown_media_duration_does_not_use_last_subtitle_as_video_end(self) -> None:
        project = create_project(
            video_path="source.mp4",
            output_dir=".",
            segments=[{"start": 0.0, "end": 2.0, "text": "early caption"}],
        )
        timeline = timeline_from_project(project)

        self.assertEqual(timeline.source_duration, 0.0)
        with self.assertRaisesRegex(VideoTimelineError, "duration is required"):
            timeline.add_cut(0.5, 1.0)

    def test_load_resolves_missing_duration_before_validating_existing_cuts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "source.mp4"
            video.touch()
            project = create_project(
                video_path=video,
                output_dir=root,
                segments=[{"start": 0.0, "end": 2.0, "text": "early caption"}],
            )
            # Also recover files written by the old subtitle-duration fallback.
            project["timeline"] = {"cuts": [{"id": "cut", "source_start": 0.5, "source_end": 1.0}]}
            path = root / "legacy.json"
            path.write_text(json.dumps(project), encoding="utf-8")
            with patch("src.subtitle_project.probe_media_duration", return_value=5.0) as probe:
                loaded = load_project(path, resolve_video_duration=True)
            probe.assert_called_once_with(str(video))
            self.assertEqual(timeline_from_project(loaded).keep_ranges, [(0.0, 0.5), (1.0, 5.0)])
            self.assertEqual(loaded["segments"], project["segments"])

            with patch("src.subtitle_project.probe_media_duration", side_effect=OSError("unavailable")):
                with self.assertRaisesRegex(SubtitleProjectError, "duration is required"):
                    load_project(path, resolve_video_duration=True)

    def test_project_round_trip_persists_timeline_and_migrates_legacy_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            video = root / "video.mp4"
            video.write_bytes(b"video")
            project = create_project(
                video_path=video,
                output_dir=root,
                segments=[],
                duration_seconds=10.0,
                timeline={"cuts": [{"id": "saved-cut", "source_start": 2.0, "source_end": 4.0}]},
            )
            path = save_project(root / "project.json", project)

            loaded = load_project(path)

            timeline_data = loaded["timeline"]
            assert is_object_mapping(timeline_data)
            cuts = timeline_data["cuts"]
            assert is_object_list(cuts)
            first_cut = cuts[0]
            assert is_object_mapping(first_cut)
            self.assertEqual(first_cut["id"], "saved-cut")
            legacy = dict(loaded)
            legacy.pop("timeline")
            legacy_path = root / "legacy.json"
            legacy_path.write_text("{}", encoding="utf-8")
            save_project(legacy_path, legacy)
            legacy_timeline = load_project(legacy_path)["timeline"]
            assert is_object_mapping(legacy_timeline)
            self.assertEqual(legacy_timeline["cuts"], [])


if __name__ == "__main__":
    unittest.main()
