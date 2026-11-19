"""¿Qué dice más de una carrera: el puesto en el draft o la temporada de novato?

Objetivo: "titular establecido" = al menos dos de los años 2 a 4 con 50 % o más de los snaps de su lado.
Evaluación hacia adelante y sin mirar el futuro: para la clase k se entrena solo con clases cuyo resultado
ya se conocía al terminar la temporada k (clases <= k - 3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .datos import grupo, leer, registros

GRUPOS = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB"]
DRAFT = ["log_pick", "no_drafteado", "edad"] + [f"g_{g}" for g in GRUPOS]
NOVATO = ["participacion", "partidos", "valor_partido", "destacado_partido", "titular_novato"]


def datos() -> pd.DataFrame:
    d = leer("select * from marts.carreras where temporada >= 2013 order by temporada, jugador")
    d["grupo"] = grupo(d["posicion"])
    d = d[d.grupo.isin(GRUPOS)].copy()
    d["no_drafteado"] = (~d["drafteado"].fillna(False)).astype(int)
    d["pick_ef"] = np.where(d["no_drafteado"] == 1, 300, d["pick"])
    d["log_pick"] = np.log(d["pick_ef"].astype(float))
    d["edad"] = d["edad"].fillna(d["edad"].median())
    for g in GRUPOS:
        d[f"g_{g}"] = (d["grupo"] == g).astype(int)
    d["participacion"] = d["participacion"].fillna(0)
    d["partidos"] = d["partidos"].fillna(0)
    pj = d["partidos"].clip(lower=1)
    d["valor_partido"] = d["valor_reemplazo"].fillna(0) / pj
    d["destacado_partido"] = d["epa_destacado"].fillna(0) / pj
    d["titular_novato"] = (d["participacion"] >= 0.5).astype(int)
    d["y"] = d["titular_establecido"].astype(int)
    return d


def modelos() -> dict:
    return {
        "Solo draft (logística)": (DRAFT, lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))),
        "Draft + novato (logística)": (DRAFT + NOVATO, lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))),
        "Draft + novato (boosting)": (DRAFT + NOVATO, lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, l2_regularization=1.0, random_state=0)),
        "Solo novato (logística)": (NOVATO + [f"g_{g}" for g in GRUPOS], lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))),
    }


def evaluar(d: pd.DataFrame, clases=range(2017, 2023)) -> tuple[pd.DataFrame, pd.DataFrame]:
    comp = d[d.completo]
    preds = []
    for k in clases:
        tr, te = comp[comp.temporada <= k - 3], comp[comp.temporada == k]
        fila = te[["jugador", "nombre", "temporada", "grupo", "pick_ef", "y"]].copy()
        fila["base"] = tr["y"].mean()
        for nombre, (cols, f) in modelos().items():
            m = f().fit(tr[cols], tr["y"])
            fila[nombre] = m.predict_proba(te[cols])[:, 1]
        preds.append(fila)
    p = pd.concat(preds)
    nombres = ["base"] + list(modelos())
    met = []
    for n in nombres:
        pr = p[n].clip(1e-4, 1 - 1e-4)
        met.append({"modelo": "Tasa base" if n == "base" else n,
                    "auc": roc_auc_score(p.y, pr) if n != "base" else 0.5,
                    "brier": brier_score_loss(p.y, pr), "log_loss": log_loss(p.y, pr)})
    return p, pd.DataFrame(met)


def diferencia_auc(p: pd.DataFrame, a: str, b: str, reps: int = 1000, semilla: int = 5) -> dict:
    rng = np.random.default_rng(semilla)
    y, pa, pb = p.y.to_numpy(), p[a].to_numpy(), p[b].to_numpy()
    est = roc_auc_score(y, pa) - roc_auc_score(y, pb)
    difs = []
    for _ in range(reps):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        difs.append(roc_auc_score(y[i], pa[i]) - roc_auc_score(y[i], pb[i]))
    lo, hi = np.percentile(difs, [2.5, 97.5])
    return {"dif": est, "ic_bajo": lo, "ic_alto": hi}


def calibracion(p: pd.DataFrame, col: str, bins: int = 10) -> list[dict]:
    q = pd.qcut(p[col], bins, duplicates="drop")
    c = p.groupby(q, observed=True).agg(predicho=(col, "mean"), observado=("y", "mean"), n=("y", "size")).reset_index(drop=True)
    return registros(c)


def equivalencia_pick(d: pd.DataFrame) -> list[dict]:
    """Cómo cambia la probabilidad de un WR según su pick y según cuánto jugó de novato (modelo logístico completo)."""
    comp = d[d.completo]
    cols, f = modelos()["Draft + novato (logística)"]
    m = f().fit(comp[cols], comp["y"])
    filas = []
    for g in ["WR", "OL", "DB"]:
        base = comp[comp.grupo == g]
        for pick in [10, 32, 64, 100, 150, 220]:
            for part in [0.1, 0.4, 0.7]:
                x = pd.DataFrame([{**{c: 0 for c in cols}, "log_pick": np.log(pick), "no_drafteado": 0, "edad": base.edad.median(),
                                   f"g_{g}": 1, "participacion": part, "partidos": 16 if part >= 0.4 else 12,
                                   "titular_novato": int(part >= 0.5)}])
                filas.append({"grupo": g, "pick": pick, "participacion": part, "prob": float(m.predict_proba(x[cols])[:, 1][0])})
    return filas


def pronosticos(d: pd.DataFrame) -> pd.DataFrame:
    """Probabilidad de ser titular establecido para las clases 2023 a 2025 (su resultado aún no se conoce del todo)."""
    comp = d[d.completo]
    cols, f = modelos()["Draft + novato (logística)"]
    m = f().fit(comp[cols], comp["y"])
    nuevas = d[(d.temporada >= 2023) & (d.temporada <= 2025)].copy()
    nuevas["prob"] = m.predict_proba(nuevas[cols])[:, 1]
    return nuevas


def correr() -> dict:
    d = datos()
    p, met = evaluar(d)
    pr = pronosticos(d)
    comp = d[d.completo]
    por_ronda = comp.assign(ronda_g=np.where(comp.no_drafteado == 1, "No drafteado", comp["ronda"].fillna(0).astype(int).astype(str))) \
        .groupby("ronda_g").agg(n=("y", "size"), tasa=("y", "mean")).reset_index()
    por_part = comp.assign(tramo=pd.cut(comp.participacion, [-0.01, 0.0001, 0.25, 0.5, 0.75, 2], labels=["No jugó", "0-25 %", "25-50 %", "50-75 %", "75 % o más"])) \
        .groupby("tramo", observed=True).agg(n=("y", "size"), tasa=("y", "mean")).reset_index()
    cols = ["nombre", "temporada", "grupo", "pick_ef", "participacion", "prob"]
    return {
        "n": int(len(comp)), "clases": [int(comp.temporada.min()), int(comp.temporada.max())], "tasa": float(comp.y.mean()),
        "n_evaluados": int(len(p)), "metricas": registros(met),
        "dif_auc_novato_vs_draft": diferencia_auc(p, "Draft + novato (logística)", "Solo draft (logística)"),
        "dif_auc_boosting_vs_logistica": diferencia_auc(p, "Draft + novato (boosting)", "Draft + novato (logística)"),
        "calibracion": calibracion(p, "Draft + novato (logística)"),
        "por_ronda": registros(por_ronda), "por_participacion": registros(por_part),
        "equivalencia": equivalencia_pick(d),
        "pronosticos": {str(c): registros(pr[pr.temporada == c].nlargest(12, "prob")[cols]) for c in [2023, 2024, 2025]},
        "sorpresas_2025": registros(pr[(pr.temporada == 2025) & (pr.pick_ef >= 100)].nlargest(8, "prob")[cols]),
    }
