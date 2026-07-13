from __future__ import annotations

import abc
import hashlib
from collections.abc import Callable, Mapping
from random import Random

from .types import Proposal


class Policy(abc.ABC):
    @abc.abstractmethod
    def act(self, view: object, rng: Random) -> Proposal | None:
        ...


class RulePolicy(Policy, abc.ABC):
    pass


class LLMReproducibilityError(Exception):
    pass


class Cassette:
    def __init__(self, entries: Mapping[str, object] | None = None):
        self._entries = dict(entries) if entries is not None else {}

    @staticmethod
    def make_key(persona: str, model_id: str, prompt: str) -> str:
        return hashlib.sha256(
            f"{persona}\x00{model_id}\x00{prompt}".encode("utf-8")
        ).hexdigest()

    def has(self, key: str) -> bool:
        return key in self._entries

    def replay(self, key: str) -> object:
        return self._entries[key]

    def record(self, key: str, response: object) -> None:
        self._entries[key] = response


# This class contains zero imports of any concrete model client — the call is injected as a plain callable specifically so the class is trivially stubbable in tests and carries no import-time coupling to any real API.
class LLMPolicy(Policy, abc.ABC):
    def __init__(
        self,
        persona: str,
        model_id: str,
        call_model: Callable[[str], object],
        cassette: Cassette | None,
        reproducible: bool,
    ):
        self.persona = persona
        self.model_id = model_id
        self._call_model = call_model
        self.cassette = cassette
        self.reproducible = reproducible

    @abc.abstractmethod
    def build_prompt(self, view: object) -> str:
        ...

    @abc.abstractmethod
    def parse_response(self, response: object, view: object) -> Proposal | None:
        ...

    def act(self, view: object, rng: Random) -> Proposal | None:
        prompt = self.build_prompt(view)
        key = Cassette.make_key(self.persona, self.model_id, prompt)

        if self.cassette is not None and self.cassette.has(key):
            response = self.cassette.replay(key)
        elif self.reproducible:
            raise LLMReproducibilityError(
                f"Reproducible campaign hit uncached LLM call: persona={self.persona}, model_id={self.model_id}"
            )
        else:
            response = self._call_model(prompt)
            if self.cassette is not None:
                self.cassette.record(key, response)

        return self.parse_response(response, view)
