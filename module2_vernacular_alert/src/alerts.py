"""Templated vernacular alert generation from Module 1's structured output.

Deliberately templated, not free-generating: zero hallucination risk on a
safety-relevant "reject this part" message matters more than generative
flexibility here (see project spec, Module 2).
"""
import json
from functools import lru_cache
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@lru_cache(maxsize=None)
def _load_templates(language: str) -> dict:
    path = TEMPLATES_DIR / f"alerts_{language}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data[language]


def generate_alert(
    defect_code: str,
    confidence: float,
    part_id: str | None = None,
    language: str = "hi",
) -> str:
    """Build a worker-facing alert string from a defect code and confidence.

    Args:
        defect_code: one of Module 1's output classes (e.g. "ok_front",
            "def_front"), or a multi-class defect type once Module 1 is
            extended (e.g. "scratches", "crazing"). Falls back to the
            "unknown" template for any unrecognized code.
        confidence: 0.0-1.0 model confidence.
        part_id: optional part/batch identifier to prefix the alert with.
        language: template language key (only "hi" is populated today; add
            more by dropping an `alerts_<lang>.json` file in templates/).

    Returns:
        A plain-language alert string combining the message and the
        corrective action.
    """
    templates = _load_templates(language)
    entry = templates.get(defect_code, templates["unknown"])

    confidence_pct = round(confidence * 100)
    message = entry["message"].format(confidence=confidence_pct)
    action = entry["action"]

    alert = f"{message} {action}"
    if part_id:
        alert = f"[{part_id}] {alert}"
    return alert


if __name__ == "__main__":
    print(generate_alert("def_front", 0.9986, part_id="P-1042"))
    print(generate_alert("ok_front", 1.0))
    print(generate_alert("scratches", 0.87))
