"""C2CWorld — owns ALL accumulation (the six SUT modules are pure/stateless) and runs the two
clocks coherently. Each tick, every actor observes an asker-relative view, proposes, and the world
either accumulates into its graph/declarations/traces/pledges/dispositions or builds the exact
module envelope from accumulated state and forwards it to the real adapter.

TS.1 (VE): the ENVELOPES speak the VE contract — castellano keys per the M7 rename table
(C2C/workflows/micorriza-politica-ve/area-b-castellanizacion/rename-table.md) — and every
module call carries `modo` (cfg.modo, TA.4 surface), plus `moneda` where Capa 4 requires it
(TA.6). Harness-side identifiers (dataclass fields, method arg names) stay English: they are
Sim's own, not the wire.

The world NEVER re-implements adjudication: a module-call proposal's verdict is whatever the real
module returns (or a Rejected wrapping the real module's own raise). The world's only power is which
accumulated slice it hands in — and it hands in the WHOLE relevant set (all vouches/facts/etc.),
letting the real module do its own cell-scoping and expiry-forgetting, exactly as in production.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from random import Random

from engine.types import Proposal
from engine.world import World

from .adapter import C2CAdapter
from .config import C2CView
from .proposals import (
    CastDisposition, DecideProposal, Declare, EmitTrace, Interact,
    LegibilityQuery, MatchRequest, Pledge, RecordFact, RecordVouch,
    ResolveCampaign, SenseRequest,
)


@dataclasses.dataclass(frozen=True)
class Rejected:
    reason: str


@dataclasses.dataclass(frozen=True)
class ModuleCall:
    # Carries BOTH the exact request the world built (from accumulated state) and the real module's
    # output, so Track A/B can independently verify input->output without trusting a single side --
    # the C2C analogue of B2B's ClearingOutcome(proposal, applied_event).
    method: str
    request: dict
    output: object  # module output dict, or Rejected


@dataclasses.dataclass(frozen=True)
class Accumulated:
    kind: str
    record: dict


def _iso(tick: int) -> str:
    # A synthetic but strictly monotone, fixed-width ISO-surrogate: the five string-clock modules
    # only ever compare timestamps lexicographically, so zero-padding gives correct ordering while
    # advancing in lockstep with the integer stigmergy clock (world.tick).
    return "T%08d" % tick


class C2CWorld(World):
    def __init__(
        self,
        sut_adapter: "C2CAdapter",
        actors: Mapping[str, "Policy"],
        cfg: "RoundConfig",
        cell_of: Mapping[str, str],
        mode_of: Mapping[str, str],
        rng: "Random",
    ) -> None:
        super().__init__(sut_adapter, actors, env=None, rng=rng)
        self.cfg = cfg
        self.cell_of = dict(cell_of)
        self.mode_of = dict(mode_of)

        # Accumulated state (all caller-supplied-then-discarded from the modules' POV).
        self.vouches: list[dict] = []
        self.facts: list[dict] = []
        self.declarations: dict[str, dict] = {}
        self.traces: list[dict] = []
        self.pledges: dict[str, list[dict]] = {}
        self.dispositions: dict[tuple[str, str], list[dict]] = {}
        self._pledge_seq = 0

        self._members_by_cell: dict[str, list[str]] = {}
        for tok, cell in self.cell_of.items():
            self._members_by_cell.setdefault(cell, []).append(tok)
        for cell in self._members_by_cell:
            self._members_by_cell[cell].sort()

    # --- views -------------------------------------------------------------------------------
    def observe(self, actor_id: str) -> object:
        cell = self.cell_of.get(actor_id, "cell-gift")
        return C2CView(
            token=actor_id,
            cell_id=cell,
            cell_mode=self.mode_of.get(cell, "don_comunal"),
            tick=self.tick,
            iso_now=_iso(self.tick),
            cell_members=tuple(m for m in self._members_by_cell.get(cell, ()) if m != actor_id),
            is_harness_role=actor_id.startswith("__"),
        )

    # --- injected deterministic proposer for the matcher -------------------------------------
    def _make_propose(self, self_decl: dict, poison: str | None):
        def proponer(contexto):
            needs = set(self_decl.get("necesidades", ()))
            goals = set(self_decl.get("metas", ()))
            out = []
            for cand in contexto["candidatos"]:
                if set(cand.get("ofertas", ())) & needs:
                    out.append({"ficha": cand["ficha"], "tipo": "oferta_cubre_necesidad",
                                "razon": "una oferta declarada cubre tu necesidad declarada"})
                elif set(cand.get("metas", ())) & goals:
                    out.append({"ficha": cand["ficha"], "tipo": "meta_compartida",
                                "razon": "una meta declarada compartida"})
            if poison == "engagement":
                # Simulate a prompt-injected / engagement-optimizing model: attach a click signal.
                # The matcher must DROP the whole proposal (descartadas_forma_vigilancia), never strip.
                bait = {"ficha": (out[0]["ficha"] if out else "__bait__"),
                        "tipo": "oferta_cubre_necesidad", "razon": "you'll love this",
                        "click_through_rate": 0.9}
                out = [bait] + out
            elif poison == "surveillance":
                bait = {"ficha": (out[0]["ficha"] if out else "__bait__"),
                        "tipo": "oferta_cubre_necesidad", "razon": "trusted",
                        "reputation": 0.95}
                out = [bait] + out
            return out
        return proponer

    # --- adjudication ------------------------------------------------------------------------
    def adjudicate(self, actor_id: str, proposal: "Proposal") -> object:
        a = self.sut_adapter
        breaches = (
            a.MembraneBreachError, a.LegibilityBreachError, a.MatcherBreachError,
            a.StigmergyBreachError, a.GovernanceBreachError, ValueError,
        )
        # AssuranceInvariantError is NOT in `breaches` (it is not a ValueError, by design): an
        # internal no-loss/conservation abort must propagate, never be softened into a Rejected.

        # ---- accumulation proposals ----
        if isinstance(proposal, RecordVouch):
            rec = {"de": proposal.frm, "a": proposal.to,
                   "celula_id": self.cell_of.get(actor_id, "cell-gift"),
                   "expira_en": _iso(self.tick + proposal.ttl)}
            self.vouches.append(rec)
            return Accumulated("vouch", rec)
        if isinstance(proposal, RecordFact):
            rec = {"sobre": proposal.about, "afirmacion": proposal.statement,
                   "celula_id": self.cell_of.get(actor_id, "cell-gift"),
                   "expira_en": _iso(self.tick + proposal.ttl)}
            self.facts.append(rec)
            return Accumulated("fact", rec)
        if isinstance(proposal, Declare):
            rec = {"ficha": proposal.token, "celula_id": self.cell_of.get(actor_id, "cell-gift"),
                   "ofertas": list(proposal.offers), "necesidades": list(proposal.needs),
                   "metas": list(proposal.goals),
                   "consentimiento": {"mostrable": bool(proposal.surfaceable)},
                   "expira_en": _iso(self.tick + proposal.ttl)}
            self.declarations[proposal.token] = rec
            return Accumulated("declaration", rec)
        if isinstance(proposal, EmitTrace):
            # NB: estigmergia VE keeps 'about' in _TRACE_KEYS (the code is the truth the rename
            # table defers to — TA.7 reconciliation); hechos in legibilidad DO use 'sobre'.
            rec = {"about": proposal.about, "senal": proposal.signal,
                   "fuerza": proposal.strength, "creado_en": self.tick,
                   "celula_id": self.cell_of.get(actor_id, "cell-gift"),
                   "contexto": proposal.context}
            self.traces.append(rec)
            return Accumulated("trace", rec)
        if isinstance(proposal, Pledge):
            self._pledge_seq += 1
            rec = {"compromiso_id": f"pl-{self._pledge_seq}",
                   "ficha_participante": proposal.participant_token}
            if proposal.kind == "monetario":
                rec["monto_centavos"] = proposal.amount_cents
            self.pledges.setdefault(proposal.campaign_id, []).append(rec)
            return Accumulated("pledge", rec)
        if isinstance(proposal, CastDisposition):
            rec = {"ficha": proposal.token, "postura": proposal.disposition,
                   "circulo_id": proposal.circle_id,
                   "expira_en": _iso(self.tick + proposal.ttl)}
            if proposal.disposition == "objetar":
                rec["objecion"] = {"primordial": bool(proposal.paramount),
                                   "razon": proposal.reason or "sin especificar"}
            self.dispositions.setdefault((proposal.circle_id, proposal.proposal_id), []).append(rec)
            return Accumulated("disposition", rec)

        # ---- module-call proposals ----
        if isinstance(proposal, Interact):
            request = {
                "sala": proposal.mode, "celula_id": proposal.cell_id,
                "interaccion_id": proposal.interaction_id,
                "participantes": list(proposal.participants),
                "carga": dict(proposal.payload),
                "modo": self.cfg.modo,
            }
            if proposal.ttl is not None:
                request["expira_en"] = _iso(self.tick + proposal.ttl)
            return self._call("admitir", request, lambda: a.admitir(request), breaches)

        if isinstance(proposal, LegibilityQuery):
            request = {
                "consultante": proposal.asker, "objetivo": proposal.target,
                "celula_id": proposal.cell_id, "ahora": _iso(self.tick),
                "saltos_max": proposal.max_hops,
                "grafo": {"avales": [dict(v) for v in self.vouches],
                          "hechos": [dict(f) for f in self.facts]},
                "modo": self.cfg.modo,
            }
            return self._call("consultar", request, lambda: a.consultar(request), breaches)

        if isinstance(proposal, MatchRequest):
            self_decl = self.declarations.get(proposal.asker, {})
            candidates = [
                {k: c[k] for k in ("ficha", "celula_id", "ofertas", "necesidades", "metas",
                                   "consentimiento", "expira_en") if k in c}
                for tok, c in sorted(self.declarations.items())
                if tok != proposal.asker
            ]
            request = {
                "consultante": proposal.asker, "celulas_ids": [proposal.cell_id],
                "ahora": _iso(self.tick), "expira_en": _iso(self.tick + proposal.ttl),
                "propuestas_max": proposal.max_proposals,
                "propio": {k: self_decl.get(k, []) for k in ("ofertas", "necesidades", "metas")},
                "candidatos": candidates,
                "modo": self.cfg.modo,
            }
            proponer = self._make_propose(request["propio"], proposal.poison)
            return self._call("emparejar", request, lambda: a.emparejar(request, proponer), breaches)

        if isinstance(proposal, SenseRequest):
            request = {
                "celula_id": proposal.cell_id, "ahora": self.tick,
                "ventana": proposal.window, "tope_velocidad": proposal.velocity_cap,
                "vida_media": proposal.half_life, "fuerza_min": proposal.min_strength,
                "trazas": [dict(t) for t in self.traces],
                "modo": self.cfg.modo,
            }
            return self._call("sentir", request, lambda: a.sentir(request), breaches)

        if isinstance(proposal, ResolveCampaign):
            request = {
                "campana_id": proposal.campaign_id, "celula_id": proposal.cell_id,
                "tipo": proposal.kind, "umbral": proposal.threshold,
                "expira_en": _iso(self.tick + proposal.ttl),
                "compromisos": [dict(p) for p in self.pledges.get(proposal.campaign_id, ())],
                "moneda": self.cfg.moneda,
                "modo": self.cfg.modo,
            }
            if proposal.sponsor_bonus_cents:
                request["bono_patrocinador_centavos"] = proposal.sponsor_bonus_cents
            return self._call("resolver", request, lambda: a.resolver(request), breaches)

        if isinstance(proposal, DecideProposal):
            request = {
                "circulo_id": proposal.circle_id, "propuesta_id": proposal.proposal_id,
                "ahora": _iso(self.tick), "expira_en": _iso(self.tick + proposal.ttl),
                "posturas": [dict(d) for d in
                             self.dispositions.get((proposal.circle_id, proposal.proposal_id), ())],
                "modo": self.cfg.modo,
            }
            return self._call("decidir", request, lambda: a.decidir(request), breaches)

        raise TypeError(f"unhandled proposal type: {type(proposal).__name__}")

    def _call(self, method: str, request: dict, thunk, breaches) -> ModuleCall:
        try:
            output = thunk()
        except breaches as exc:
            output = Rejected(reason=f"{type(exc).__name__}: {exc}")
        return ModuleCall(method=method, request=request, output=output)

    def apply(self, actor_id: str, proposal: "Proposal", result: object) -> None:
        # Accumulation already happened in adjudicate (state is the source of truth); module calls
        # persist nothing. Nothing to do here — mirrors B2BWorld.apply.
        pass
