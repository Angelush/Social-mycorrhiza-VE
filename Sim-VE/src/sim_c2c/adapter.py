"""Envoltorio fino y fiel, uno-a-uno, sobre el sistema real C2C-VE (protocolo social).

The only Sim code that touches the six Capa modules (membrana, legibilidad, emparejador,
aseguramiento, estigmergia, gobernanza). It pins their content hash via SUTAdapter, loads
each real module from source by file path (there is no package install in C2C-VE/, so
this mirrors C2C-VE's own importlib-by-path loading), and forwards every call verbatim.

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
    # admitir/consultar/emparejar/resolver/sentir/decidir. No method collides across
    # the six modules. (TS.1: the VE contract renamed the functions — the adapter's
    # surface follows the SUT, never the other way around.)

    _MODULES = (
        ("membrana", "partition", "membrana.py"),
        ("legibilidad", "legibility", "legibilidad.py"),
        ("emparejador", "matcher", "emparejador.py"),
        ("aseguramiento", "assurance", "aseguramiento.py"),
        ("estigmergia", "stigmergy", "estigmergia.py"),
        ("gobernanza", "governance", "gobernanza.py"),
    )

    def __init__(self, c2c_root: str | Path) -> None:
        root = Path(c2c_root)
        paths = [root / "src" / pkg / fname for (_attr, pkg, fname) in self._MODULES]

        # C2C-VE lives inside this repo — repo_dir points there; compute_pin records
        # the enclosing repo's HEAD as supplementary metadata. content_hash is the real pin.
        super().__init__(paths, repo_dir=c2c_root)

        self._mods = {}
        for (attr, _pkg, _fname), path in zip(self._MODULES, paths):
            spec = importlib.util.spec_from_file_location(f"c2c_{attr}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._mods[attr] = mod

    # --- Exception types, surfaced from the real modules for callers that catch them.
    # Property names keep the harness-side English (they are Sim identifiers, not the wire);
    # each returns the REAL VE exception type, verbatim.
    @property
    def MembraneBreachError(self) -> type:
        return self._mods["membrana"].ErrorDeBrechaMembrana

    @property
    def LegibilityBreachError(self) -> type:
        return self._mods["legibilidad"].ErrorDeBrechaLegibilidad

    @property
    def MatcherBreachError(self) -> type:
        return self._mods["emparejador"].ErrorDeBrechaEmparejador

    @property
    def AssuranceInvariantError(self) -> type:
        return self._mods["aseguramiento"].ErrorDeInvarianteAseguramiento

    @property
    def StigmergyBreachError(self) -> type:
        return self._mods["estigmergia"].ErrorDeBrechaEstigmergia

    @property
    def GovernanceBreachError(self) -> type:
        return self._mods["gobernanza"].ErrorDeBrechaGobernanza

    # --- The six pass-throughs. Each: call the real function, return/raise verbatim.
    def admitir(self, interaccion: dict) -> dict:
        return self._mods["membrana"].admitir(interaccion)

    def consultar(self, request: dict) -> dict:
        return self._mods["legibilidad"].consultar(request)

    def emparejar(self, solicitud: dict, proponer: Callable) -> dict:
        return self._mods["emparejador"].emparejar(solicitud, proponer)

    def resolver(self, campana: dict) -> dict:
        return self._mods["aseguramiento"].resolver(campana)

    def sentir(self, request: dict) -> dict:
        return self._mods["estigmergia"].sentir(request)

    def decidir(self, request: dict) -> dict:
        return self._mods["gobernanza"].decidir(request)
