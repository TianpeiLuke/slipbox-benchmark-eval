"""The run registry — a result names what produced it.

This layer did not exist. Run outputs live in fifteen directories, `runs2`
through `runs16`, keyed by ad-hoc filenames (`chunks_bm25.json`,
`chunks_bm25_evid.json`, `fair_questions.json`) and referenced from the docs only
by number. Nothing records which code, config, or dataset checksum produced any
of them, so cross-benchmark comparison is impossible and "which run was that?"
is answerable only by git archaeology.

Two symptoms this fixes, both visible in the repo today:

- `execute_v2.py`, `execute_v3.py`, `execute_v3c.py`, `execute_v4.py`,
  `execute_v41.py` exist because there was nowhere to record which config a run
  used, so it went in the filename.
- `docs/BASELINES.md` points at `experiments/runs11/hippo_slice` and
  `experiments/runs9/fair_questions.json`. Those paths are the only surviving
  statement of what runs 9 and 11 were for.

A manifest is written beside every run. `run_id` is a content hash of the
provenance block rather than a timestamp, so it is stable and re-derivable: the
same code, config and data always produce the same id, and a changed input always
produces a different one.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CodeProvenance:
    """Which code ran. `dirty` matters more than `sha`.

    A result produced from a dirty tree is not reproducible, and recording that
    is the difference between a result and an anecdote.
    """

    git_sha: str
    dirty: bool
    repo: str = "slipbox-benchmark-eval"


@dataclass(frozen=True)
class DataProvenance:
    """Which bytes were scored. Checksums come from the fetch manifest."""

    benchmark: str
    file_sha256: Mapping[str, str]
    gold_form: str
    """Copied from the BenchmarkSpec so a manifest is self-describing --
    the reporting layer refuses to compare across gold_form, and it must be
    able to do that from the manifest alone."""


@dataclass(frozen=True)
class EnvProvenance:
    python: str
    platform: str
    packages: Mapping[str, str] = field(default_factory=dict)
    nondeterministic_components: tuple[str, ...] = ()
    """Anything in the DECISION path that is not byte-reproducible.

    Not a footnote. A sentence encoder in this stack gives different vectors for
    the same sentence encoded alone versus in a batch, and the result moves with
    thread count -- so a threshold near a boundary can flip on a machine change,
    silently. If a component like that is in the path, the run is not replayable
    and the manifest must say so.
    """


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    schema_version: int
    system: str
    """Arm identity, e.g. `tessellum@<sha>`, `chunks-recursive-400`, `hipporag`."""
    arm_config: Mapping[str, Any]
    metric_set: tuple[str, ...]
    code: CodeProvenance
    data: DataProvenance
    env: EnvProvenance
    created_at: str
    provenance: str = "first_class"
    """`first_class` when written by the harness; `reconstructed` when backfilled
    from git history and directory layout. Reconstructed manifests are guesses
    about the past and must never be mistaken for records."""
    notes: str = ""


# ── Identity ──────────────────────────────────────────────────────────────────


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def compute_run_id(
    system: str,
    arm_config: Mapping[str, Any],
    code: CodeProvenance,
    data: DataProvenance,
) -> str:
    """A stable content hash over what actually determines the result.

    Deliberately excludes `created_at` and the environment: re-running identical
    code on identical data with an identical config should collide, because that
    is the same experiment. Environment differences are recorded but do not
    change identity -- if they changed the answer, that is a finding, and a
    collision is how you notice.
    """
    payload = _canonical(
        {
            "system": system,
            "arm_config": arm_config,
            "git_sha": code.git_sha,
            "dirty": code.dirty,
            "benchmark": data.benchmark,
            "file_sha256": dict(sorted(data.file_sha256.items())),
        }
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ── Capture ───────────────────────────────────────────────────────────────────


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001 -- absent git is not fatal to a run
        return ""


def current_code() -> CodeProvenance:
    sha = _git("rev-parse", "HEAD") or "unknown"
    dirty = bool(_git("status", "--porcelain"))
    return CodeProvenance(git_sha=sha, dirty=dirty)


def current_env(
    packages: Mapping[str, str] | None = None,
    nondeterministic: tuple[str, ...] = (),
) -> EnvProvenance:
    return EnvProvenance(
        python=sys.version.split()[0],
        platform=platform.platform(),
        packages=dict(packages or {}),
        nondeterministic_components=nondeterministic,
    )


def make_manifest(
    system: str,
    benchmark: str,
    gold_form: str,
    arm_config: Mapping[str, Any],
    metric_set: tuple[str, ...],
    file_sha256: Mapping[str, str],
    nondeterministic: tuple[str, ...] = (),
    packages: Mapping[str, str] | None = None,
    notes: str = "",
    provenance: str = "first_class",
) -> RunManifest:
    code = current_code()
    data = DataProvenance(
        benchmark=benchmark, file_sha256=dict(file_sha256), gold_form=gold_form
    )
    return RunManifest(
        run_id=compute_run_id(system, arm_config, code, data),
        schema_version=SCHEMA_VERSION,
        system=system,
        arm_config=dict(arm_config),
        metric_set=metric_set,
        code=code,
        data=data,
        env=current_env(packages, nondeterministic),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        provenance=provenance,
        notes=notes,
    )


# ── Storage ───────────────────────────────────────────────────────────────────


def run_dir(m: RunManifest) -> Path:
    return RUNS / m.data.benchmark / m.system.replace("/", "_") / m.run_id


def write_manifest(m: RunManifest, base: Path | None = None) -> Path:
    d = base or run_dir(m)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "manifest.json"
    p.write_text(json.dumps(asdict(m), indent=1, default=str) + "\n")
    return p


def read_manifest(path: Path) -> RunManifest:
    d = json.loads(Path(path).read_text())
    return RunManifest(
        run_id=d["run_id"],
        schema_version=d.get("schema_version", 1),
        system=d["system"],
        arm_config=d.get("arm_config", {}),
        metric_set=tuple(d.get("metric_set", ())),
        code=CodeProvenance(**d["code"]),
        data=DataProvenance(**d["data"]),
        env=EnvProvenance(
            python=d["env"]["python"],
            platform=d["env"]["platform"],
            packages=d["env"].get("packages", {}),
            nondeterministic_components=tuple(
                d["env"].get("nondeterministic_components", ())
            ),
        ),
        created_at=d["created_at"],
        provenance=d.get("provenance", "first_class"),
        notes=d.get("notes", ""),
    )


def discover(base: Path | None = None) -> list[RunManifest]:
    """Every manifest under the runs tree, sorted for stable reporting."""
    root = base or RUNS
    if not root.exists():
        return []
    found = [read_manifest(p) for p in sorted(root.rglob("manifest.json"))]
    return sorted(found, key=lambda m: (m.data.benchmark, m.system, m.run_id))


def comparable(a: RunManifest, b: RunManifest) -> tuple[bool, str]:
    """May these two runs be put in the same table?

    The gold_form guard is the enforcement point for the credit error: comparing
    a document_set result against a span result is the mistake that inflated a
    note arm about ten times more than a chunk arm, and it is invisible once both
    are rendered as a number called "recall".
    """
    if a.data.benchmark != b.data.benchmark:
        return False, (
            f"different benchmarks: {a.data.benchmark} vs {b.data.benchmark}"
        )
    if a.data.gold_form != b.data.gold_form:
        return False, (
            f"different gold_form: {a.data.gold_form} vs {b.data.gold_form} -- "
            "credit granularity differs, so the numbers are not on one scale"
        )
    if a.data.file_sha256 != b.data.file_sha256:
        return False, "different dataset bytes (file_sha256 mismatch)"
    sub_a = a.arm_config.get("subset")
    sub_b = b.arm_config.get("subset")
    if sub_a != sub_b:
        return False, (
            f"different corpus subset: {sub_a} vs {sub_b} -- a slice result is "
            "not on the same scale as a full-corpus result"
        )
    return True, "comparable"
