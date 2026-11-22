"""The protocol's sanity baselines: single-feature threshold rules (no fitted model) and the lexical probe."""

import re
from itertools import permutations
from statistics import quantiles

WORD = re.compile(r"[A-Za-z']+")


def features(row: dict) -> dict:
    text = row["text"]
    words = WORD.findall(text)
    sentences = [s for s in re.split(r"[.!?]+\s", text) if s.strip()]
    return {
        "chars": len(text),
        "words": len(words),
        "words_per_sentence": len(words) / max(1, len(sentences)),
        "em_dashes_per_1k_words": 1000 * text.count("—") / max(1, len(words)),
        "bullets": text.count("•") + len(re.findall(r"^- ", text, re.M)),
        "layout": row["made"]["layout"],
        "font": row["made"]["font"],
    }


def _accuracy(xs: list[float], ys: list[str], t1: float, t2: float, order: tuple[str, ...]) -> float:
    hits = sum(order[0 if x <= t1 else 1 if x <= t2 else 2] == y for x, y in zip(xs, ys, strict=True))
    return hits / len(ys)


def threshold_rule(xs: list[float], ys: list[str], classes: tuple[str, ...]) -> tuple[float, float, tuple]:
    """The best 'two thresholds, three classes in some order' rule on the given (train) values."""
    cuts = sorted(set(quantiles(xs, n=26)))
    best = (-1.0, 0.0, 0.0, classes)
    for order in permutations(classes):
        for i, t1 in enumerate(cuts):
            for t2 in cuts[i:]:
                acc = _accuracy(xs, ys, t1, t2, order)
                if acc > best[0]:
                    best = (acc, t1, t2, order)
    return best[1], best[2], best[3]


def category_rule(xs: list[str], ys: list[str]) -> dict[str, str]:
    """Each category's most common label on train."""
    counts: dict[str, dict[str, int]] = {}
    for x, y in zip(xs, ys, strict=True):
        counts.setdefault(x, {}).setdefault(y, 0)
        counts[x][y] += 1
    return {x: max(c, key=c.get) for x, c in counts.items()}


def single_feature(train: list[dict], test: list[dict], label: str, classes: tuple[str, ...]) -> dict[str, float]:
    """Test accuracy of the best single-feature rule per feature, chosen on train."""
    ftr, fte = [features(r) for r in train], [features(r) for r in test]
    ytr, yte = [r[label] for r in train], [r[label] for r in test]
    out: dict[str, float] = {}
    for name in ftr[0]:
        xtr, xte = [f[name] for f in ftr], [f[name] for f in fte]
        if isinstance(xtr[0], str):
            rule = category_rule(xtr, ytr)
            pred = [rule.get(x, classes[0]) for x in xte]
            out[name] = sum(p == y for p, y in zip(pred, yte, strict=True)) / len(yte)
        else:
            t1, t2, order = threshold_rule(xtr, ytr, classes)
            out[name] = _accuracy(xte, yte, t1, t2, order)
    return out


def _words(text: str) -> set[str]:
    return {w.lower() for w in WORD.findall(text)}


def probe(train: list[dict], test: list[dict]) -> dict[str, float]:
    """Nearest-train-precedent word-set overlap (Jaccard) for each held-out applicant: the lexical stand-in."""
    pool = [_words(r["text"]) for r in train]
    near = []
    for r in test:
        w = _words(r["text"])
        near.append(max(len(w & p) / len(w | p) for p in pool))
    q = quantiles(near, n=20)
    return {"p5": q[0], "p25": q[4], "p50": q[9], "p75": q[14], "p95": q[18]}
