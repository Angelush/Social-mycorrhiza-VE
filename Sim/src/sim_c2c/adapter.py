"""Thin, faithful one-to-one wrapper over the real C2C social-protocol system.

The only Sim code that touches the six Capa modules (membrane, legibility, matcher,
assurance, stigmergy, governance). It pins their content hash via SUTAdapter, loads
each real module from source by file path (there is no package install in C2C/, so
this mirrors C2C's own importlib-by-path loading), and forwards every call verbatim.

Unlike B2BAdapter, these six modules are PURE and STATELESS: each takes its full input
envelope per call and discards it. So this adapter holds NO state — all accumulation
lives in C2CWorld, which builds each envelope and passes it in. The adapter's single
job is: load the real function, call it, return exactly what it returns (or let it
raise exactly what it raises). Zero validation, bounds-checking, exception-catching, or
adjudication of its own — a future editor tempted to add a "helpful" check here would be
quietly reintroducing a second copy of a mechanism this wrapper must never become.
"""
from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path

from engine.sut_adapter import SUTAdapter


class C2CAdapter(SUTAdapter):
    # Method names are the verbatim real function names, one-to-one, none invented:
    # admit/query/match/resolve/sense/decide. No method collides across the six modules.

    _MODULES = (
        ("membrane", "partition", "membrane.py"),
        ("legibility", "legibility", "legibility_query.py"),
        ("matcher", "matcher", "matcher.py"),
        ("assurance", "assurance", "assurance_engine.py"),
        ("stigmergy", "stigmergy", "stigmergy.py"),
        ("governance", "governance", "governance.py"),
    )

    def __init__(self, c2c_root: str | Path) -> None:
        root = Path(c2c_root)
        paths = [root / "src" / pkg / fname for (_attr, pkg, fname) in self._MODULES]

        # C2C is not a git repo — repo_dir points there anyway; compute_pin returns
        # git_commit=None gracefully (no .git present). content_hash is the real pin.
        super().__init__(paths, repo_dir=c2c_root)

        self._mods = {}
        for (attr, _pkg, _fname), path in zip(self._MODULES, paths):
            spec = importlib.util.spec_from_file_location(f"c2c_{attr}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._mods[attr] = mod

    # --- Exception types, surfaced from the real modules for callers that catch them.
    @property
    def MembraneBreachError(self) -> type:
        return self._mods["membrane"].MembraneBreachError

    @property
    def LegibilityBreachError(self) -> type:
        return self._mods["legibility"].LegibilityBreachError

    @property
    def MatcherBreachError(self) -> type:
        return self._mods["matcher"].MatcherBreachError

    @property
    def AssuranceInvariantError(self) -> type:
        return self._mods["assurance"].AssuranceInvariantError

    @property
    def StigmergyBreachError(self) -> type:
        return self._mods["stigmergy"].StigmergyBreachError

    @property
    def GovernanceBreachError(self) -> type:
        return self._mods["governance"].GovernanceBreachError

    # --- The six pass-throughs. Each: call the real function, return/raise verbatim.
    def admit(self, interaction: dict) -> dict:
        return self._mods["membrane"].admit(interaction)

    def query(self, request: dict) -> dict:
        return self._mods["legibility"].query(request)

    def match(self, request: dict, propose: Callable) -> dict:
        return self._mods["matcher"].match(request, propose)

    def resolve(self, campaign: dict) -> dict:
        return self._mods["assurance"].resolve(campaign)

    def sense(self, request: dict) -> dict:
        return self._mods["stigmergy"].sense(request)

    def decide(self, request: dict) -> dict:
        return self._mods["governance"].decide(request)
