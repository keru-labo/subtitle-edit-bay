"""Build the seek gate, check its line coverage, and kill targeted mutations."""

import gzip
import json
import re
import resource
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/preview"
TEST = Path(__file__).with_name("seek_gate_test.cpp")
MUTATIONS = {
    "stale generation": (" && generation == generation_", ""),
    "unissued generation": (" && generation == dispatched_", ""),
    "oldest request wins": ("pending_ = Seek", "if (!pending_) pending_ = Seek"),
    "invalidated request dispatches": (
        "++generation_;\n        pending_.reset();",
        "++generation_;",
    ),
}


def build(work: Path, coverage: bool = False) -> None:
    command = ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", ".", str(TEST)]
    if coverage:
        command.append("--coverage")
    subprocess.run([*command, "-o", "seek_gate_test"], cwd=work, check=True)


def main() -> None:
    contract = (ROOT / "docs/PREVIEW_SEEK_CONTRACT.md").read_text(encoding="utf-8")
    for link in re.findall(r"\]\((\.\./[^)]+)\)", contract):
        if not (ROOT / "docs" / link).is_file():
            raise SystemExit(f"Broken contract link: {link}")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    with tempfile.TemporaryDirectory(prefix="seek-gate-") as directory:
        work = Path(directory)
        header = work / "seek_gate.h"
        shutil.copyfile(SOURCE / header.name, header)
        shutil.copyfile(SOURCE / "playback_backend.h", work / "playback_backend.h")
        original = header.read_text(encoding="utf-8")
        build(work, coverage=True)
        subprocess.run([str(work / "seek_gate_test")], cwd=work, check=True)
        subprocess.run(
            ["gcov", "--json-format", next(work.glob("*.gcno")).name],
            cwd=work,
            stdout=subprocess.DEVNULL,
            check=True,
        )
        with gzip.open(next(work.glob("*.gcov.json.gz")), "rt", encoding="utf-8") as report:
            files = json.load(report)["files"]
        lines = next(file["lines"] for file in files if Path(file["file"]).name == header.name)
        coverage = 100 * sum(line["count"] > 0 for line in lines) / len(lines)
        print(f"SeekGate line coverage: {coverage:.1f}%")
        if coverage < 85:
            raise SystemExit("SeekGate line coverage below 85%")

        for name, (old, new) in MUTATIONS.items():
            if original.count(old) != 1:
                raise SystemExit(f"Mutation anchor changed: {name}")
            header.write_text(original.replace(old, new), encoding="utf-8")
            build(work)
            result = subprocess.run([str(work / "seek_gate_test")], capture_output=True, cwd=work)
            if result.returncode != -6:
                raise SystemExit(f"Mutation did not fail an assertion: {name} ({result.returncode})")
            print(f"Killed: {name}")


if __name__ == "__main__":
    main()
