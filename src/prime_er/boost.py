from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Stump:
    """A tiny, interpretable weak learner.

    Predicts +1 if feature >= threshold, else -1.
    """
    feature: str
    threshold: float = 1.0
    polarity: int = 1  # +1 for >= threshold, -1 for < threshold

    def predict(self, x: Dict[str, float]) -> int:
        v = float(x.get(self.feature, 0.0))
        pred = 1 if v >= self.threshold else -1
        return self.polarity * pred


@dataclass
class BoostModel:
    """Additive model: score(x) = sum(alpha_t * stump_t(x))."""
    stumps: List[Tuple[float, Stump]]  # (alpha, stump)

    def score(self, x: Dict[str, float]) -> float:
        s = 0.0
        for alpha, stump in self.stumps:
            s += alpha * stump.predict(x)
        return s

    def explain(self, x: Dict[str, float]) -> List[Dict[str, float]]:
        out: List[Dict[str, float]] = []
        for alpha, stump in self.stumps:
            pred = stump.predict(x)
            out.append({
                "feature": stump.feature,
                "threshold": stump.threshold,
                "alpha": alpha,
                "pred": pred,
                "contrib": alpha * pred,
                "value": float(x.get(stump.feature, 0.0)),
            })
        return out


def default_boost_model() -> BoostModel:
    """A conservative default model for toy ER.

    We weight stable identifiers higher.
    """
    stumps: List[Tuple[float, Stump]] = [
        (2.5, Stump("email_j", threshold=1.0)),
        (2.0, Stump("phone_j", threshold=1.0)),
        (1.5, Stump("device_j", threshold=1.0)),
        (1.0, Stump("cookie_j", threshold=1.0)),
        (0.8, Stump("name_eq", threshold=1.0)),
    ]
    return BoostModel(stumps=stumps)
