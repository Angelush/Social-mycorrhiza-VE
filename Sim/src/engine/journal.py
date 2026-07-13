from __future__ import annotations

import collections.abc
import dataclasses
import enum
import hashlib
import json

from .measurement import IntegrityReport, WelfareReport
from .types import WorldDiff


def _to_jsonable(obj: object) -> object:
    # Sort mappings and sets explicitly before serializing to ensure cross-run byte reproducibility.
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, enum.Enum):
        return obj.name
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            "__type__": type(obj).__name__,
            **{f.name: _to_jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
        }
    if isinstance(obj, collections.abc.Mapping):
        return {
            (str(k) if not isinstance(k, str) else k): _to_jsonable(v)
            for k, v in sorted(obj.items(), key=lambda kv: kv[0])
        }
    if isinstance(obj, (set, frozenset)):
        return sorted(str(_to_jsonable(x)) for x in obj)
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    return str(obj)


def canonical_hash(obj: object) -> str:
    serialized = json.dumps(
        _to_jsonable(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


@dataclasses.dataclass(frozen=True)
class JournalEntry:
    round: int
    config_hash: str
    integrity_report: IntegrityReport
    welfare_report: WelfareReport
    hypothesis: str | None
    diff: WorldDiff | None
    prev_hash: str
    entry_hash: str


class Journal:
    def __init__(self) -> None:
        self.entries: list[JournalEntry] = []

    def append(
        self,
        round: int,
        config_hash: str,
        integrity_report: IntegrityReport,
        welfare_report: WelfareReport,
        hypothesis: str | None,
        diff: WorldDiff | None,
    ) -> JournalEntry:
        prev_hash = self.entries[-1].entry_hash if self.entries else ""
        content = {
            "round": round,
            "config_hash": config_hash,
            "integrity_report": integrity_report,
            "welfare_report": welfare_report,
            "hypothesis": hypothesis,
            "diff": diff,
            "prev_hash": prev_hash,
        }
        entry_hash = canonical_hash(content)
        entry = JournalEntry(
            round=round,
            config_hash=config_hash,
            integrity_report=integrity_report,
            welfare_report=welfare_report,
            hypothesis=hypothesis,
            diff=diff,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        for i, entry in enumerate(self.entries):
            if i > 0:
                if entry.prev_hash != self.entries[i - 1].entry_hash:
                    return False
            content = {
                "round": entry.round,
                "config_hash": entry.config_hash,
                "integrity_report": entry.integrity_report,
                "welfare_report": entry.welfare_report,
                "hypothesis": entry.hypothesis,
                "diff": entry.diff,
                "prev_hash": entry.prev_hash,
            }
            if canonical_hash(content) != entry.entry_hash:
                return False
        return True
