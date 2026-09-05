"""Métricas de consistencia entre varias respuestas a la misma pregunta.

Dos medidas complementarias, y la diferencia entre ellas es el punto pedagógico:

  1. Divergencia léxica. Cuánto cambia el vocabulario entre respuestas.
     Un modelo puede reformular lo mismo de veinte maneras y dar 60% aquí
     sin que ningún hecho cambie.

  2. Divergencia en datos clave. Cuánto cambian los números, años y cifras.
     Esta es la que importa. Si el año de respuesta cambia entre ejecuciones,
     el sistema no es confiable, por muy bien redactado que esté.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*%?")


def normalize(text: str) -> list[str]:
    """Minúsculas, sin acentos, sin puntuación, partido en palabras."""
    lowered = text.lower()
    stripped = "".join(
        c for c in unicodedata.normalize("NFD", lowered)
        if unicodedata.category(c) != "Mn"
    )
    return _PUNCT.sub(" ", stripped).split()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def lexical_divergence(texts: list[str]) -> int:
    """0 = vocabulario idéntico. 100 = sin una sola palabra en común."""
    sets = [set(normalize(t)) for t in texts]
    if len(sets) < 2:
        return 0
    scores = [
        _jaccard(sets[i], sets[j])
        for i in range(len(sets))
        for j in range(i + 1, len(sets))
    ]
    return round((1 - sum(scores) / len(scores)) * 100)


def extract_key_facts(text: str) -> set[str]:
    """Números, años, porcentajes y cifras. El dato que sí debe ser estable."""
    return {m.group().rstrip(".,") for m in _NUMBER.finditer(text)}


def key_fact_divergence(texts: list[str]) -> tuple[int, list[str]]:
    """Divergencia sobre los datos duros, más el listado de los que aparecen.

    Devuelve el porcentaje y los datos ordenados por frecuencia, de forma que
    en pantalla se vea si el modelo dijo 1968 quince veces y 1969 cinco veces.
    """
    fact_sets = [extract_key_facts(t) for t in texts]
    counter: Counter[str] = Counter()
    for facts in fact_sets:
        counter.update(facts)

    ranked = [
        f"{fact} ({count}/{len(texts)})"
        for fact, count in counter.most_common(12)
    ]

    non_empty = [f for f in fact_sets if f]
    if len(non_empty) < 2:
        return 0, ranked

    scores = [
        _jaccard(non_empty[i], non_empty[j])
        for i in range(len(non_empty))
        for j in range(i + 1, len(non_empty))
    ]
    return round((1 - sum(scores) / len(scores)) * 100), ranked


def volatile_tokens(texts: list[str], limit: int = 400) -> list[str]:
    """Palabras que no aparecen en todas las respuestas.

    El frontend las resalta en rojo para que la audiencia vea de un vistazo
    dónde el modelo se movió.
    """
    sets = [set(normalize(t)) for t in texts]
    if not sets:
        return []
    everywhere = set.intersection(*sets) if len(sets) > 1 else sets[0]
    anywhere = set.union(*sets)
    return sorted(anywhere - everywhere)[:limit]


def unique_responses(texts: list[str]) -> int:
    """Cuántos textos distintos hay tras normalizar."""
    return len({" ".join(normalize(t)) for t in texts})


def summarize(texts: list[str]) -> dict:
    """Todas las métricas en un solo diccionario."""
    if not texts:
        return {
            "lexical_divergence": 0,
            "unique_responses": 0,
            "key_facts": [],
            "key_fact_divergence": 0,
            "word_count_min": 0,
            "word_count_max": 0,
            "volatile_tokens": [],
        }

    lengths = [len(normalize(t)) for t in texts]
    fact_div, facts = key_fact_divergence(texts)

    return {
        "lexical_divergence": lexical_divergence(texts),
        "unique_responses": unique_responses(texts),
        "key_facts": facts,
        "key_fact_divergence": fact_div,
        "word_count_min": min(lengths),
        "word_count_max": max(lengths),
        "volatile_tokens": volatile_tokens(texts),
    }
