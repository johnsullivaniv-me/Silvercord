"""Write journal entries with the Claude API."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MIN_WORDS, MAX_WORDS = 150, 250
# Accept small misses rather than paying for a retry over three words.
SOFT_MIN, SOFT_MAX = 140, 270

SYSTEM_PROMPT = """\
You are the Chronicler of Silvercord: a court historian who records one adventurer's \
deeds in World of Warcraft as journal entries. Your voice is epic but wry, like a \
grand saga written by someone who has noticed that the hero just died to a boar. \
Lofty phrasing, dry asides, warmth toward the hero. Never mean, never meta.

Hard rules:
1. Use ONLY the facts provided. Do not invent people, places, items, quests, \
creatures, dialogue, motives, weather, or events. You may add colour (tone, \
metaphor, the chronicler's opinions) but never new facts. If something is not \
in the facts, it did not happen as far as the chronicle knows.
2. Facts marked "possibly", "inferred", or "a guess" must be told with clear \
hedging ("it is said", "by most accounts", "the record is unclear"). Never \
state them as certain.
3. Every one of the adventurer's own /chron notes must appear in the entry, \
quoted exactly or very nearly so, attributed to the adventurer.
4. Use names exactly as written in the facts. Items in [brackets] may keep \
their brackets or drop them, but keep the spelling.
5. Length: {min_words} to {max_words} words of prose. No headings, no bullet \
lists, no title, no sign-off. Start directly with the entry.
6. Write in the third person about the adventurer, past tense.
7. You do not need to mention every fact. Choose the ones that make the best \
story, but include all /chron notes, any level gained, deaths, and bosses.
""".format(min_words=MIN_WORDS, max_words=MAX_WORDS)

USER_TEMPLATE = """\
Write the chronicle entry for this session. These are all the facts that exist:

<facts>
{facts}
</facts>
"""

# Models that accept server-side refusal fallbacks ("default" mode).
_FALLBACK_MODELS = ("claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-1")
_FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Models that accept output_config.effort.
_EFFORT_RE = re.compile(r"^claude-(opus|sonnet|haiku|fable|mythos)-(5|4-[5-8])")


class WriterError(RuntimeError):
    def __init__(self, msg: str, fatal: bool = False):
        super().__init__(msg)
        self.fatal = fatal  # True: stop the whole run (bad key, bad model...)


def _classify(exc: Exception) -> WriterError:
    """Turn SDK errors into WriterErrors, marking ones no retry will fix."""
    name = type(exc).__name__
    msg = str(exc)
    if name == "AuthenticationError" or "authentication" in msg.lower():
        return WriterError("No valid Claude API credentials. Set ANTHROPIC_API_KEY "
                           "(see README) and run again.", fatal=True)
    if name == "PermissionDeniedError":
        return WriterError(f"The API key isn't allowed to do this: {msg}", fatal=True)
    if name == "NotFoundError":
        return WriterError(f"Model not found. Check --model / SILVERCORD_MODEL. ({msg})", fatal=True)
    if name == "BadRequestError":
        return WriterError(f"The API rejected the request: {msg}", fatal=True)
    return WriterError(f"{name}: {msg}")


@dataclass
class Entry:
    text: str
    words: int
    model: str
    attempts: int


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9'’-]+", text))


class Chronicler:
    def __init__(self, model: str, client: Any | None = None, effort: str = "medium"):
        self.model = model
        self.effort = effort
        self.use_fallbacks = model in _FALLBACK_MODELS
        if client is None:
            import anthropic  # deferred so dry-run works without the SDK
            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self.client = client

    def _request(self, messages: list[dict]) -> Any:
        try:
            return self._send(messages)
        except Exception as exc:  # SDK errors; the SDK already retried 429/5xx
            # Refusal fallbacks are a beta. If this account or model rejects
            # them, drop the feature rather than failing every entry.
            if (self.use_fallbacks and type(exc).__name__ == "BadRequestError"
                    and "fallback" in str(exc).lower()):
                self.use_fallbacks = False
                try:
                    return self._send(messages)
                except Exception as exc2:
                    raise _classify(exc2) from exc2
            raise _classify(exc) from exc

    def _send(self, messages: list[dict]) -> Any:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        if _EFFORT_RE.match(self.model):
            kwargs["output_config"] = {"effort": self.effort}
        if self.use_fallbacks:
            return self.client.beta.messages.create(
                betas=[_FALLBACK_BETA], fallbacks="default", **kwargs
            )
        return self.client.messages.create(**kwargs)

    @staticmethod
    def _text(resp: Any) -> str:
        if getattr(resp, "stop_reason", None) == "refusal":
            raise WriterError("The model declined to write this entry (stop_reason=refusal).")
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        text = "\n\n".join(p.strip() for p in parts if p and p.strip()).strip()
        if not text:
            raise WriterError(f"Empty response (stop_reason={getattr(resp, 'stop_reason', None)}).")
        return text

    def write(self, facts: str) -> Entry:
        messages: list[dict] = [{"role": "user", "content": USER_TEMPLATE.format(facts=facts)}]
        resp = self._request(messages)
        text = self._text(resp)
        n = word_count(text)
        attempts = 1
        if not (SOFT_MIN <= n <= SOFT_MAX):
            messages += [
                {"role": "assistant", "content": resp.content},
                {"role": "user", "content": (
                    f"That draft is {n} words. Rewrite it to between {MIN_WORDS} and "
                    f"{MAX_WORDS} words, same rules, same facts. Reply with only the entry."
                )},
            ]
            retry = self._text(self._request(messages))
            attempts = 2
            rn = word_count(retry)
            # keep whichever is closer to the target band
            if abs(rn - 200) < abs(n - 200):
                text, n = retry, rn
        return Entry(text=text, words=n, model=getattr(resp, "model", None) or self.model, attempts=attempts)
