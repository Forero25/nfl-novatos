"""El contrato de novato como ganga: valor producido por cada 1 % del tope salarial, según la etapa de la carrera."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .datos import ULTIMA_COMPLETA, grupo, leer, registros

ETAPAS = [(1, 1, "Novato"), (2, 4, "Años 2 a 4"), (5, 99, "Año 5 en adelante")]


def etapa(a: pd.Series) -> pd.Series:
    out = pd.Series(index=a.index, dtype=object)
    for lo, hi, n in ETAPAS:
        out[(a >= lo) & (a <= hi)] = n
    return out


def razon_boot(d: pd.DataFrame, num: str, den: str, reps: int = 1000, semilla: int = 11) -> tuple[float, float, float]:
    """Razón de sumas con intervalo bootstrap remuestreando jugadores (no temporadas), porque un jugador aporta varias."""
    rng = np.random.default_rng(semilla)
    g = d.groupby("jugador")[[num, den]].sum()
    v = g.to_numpy()
    est = v[:, 0].sum() / v[:, 1].sum()
    idx = rng.integers(0, len(v), size=(reps, len(v)))
    b = v[idx, 0].sum(1) / v[idx, 1].sum(1)
    return est, *np.percentile(b, [2.5, 97.5])


def correr() -> dict:
    t = leer(f"""select * from marts.temporadas where temporada between 2013 and {ULTIMA_COMPLETA}
                 and pct_cap > 0 and anio_carrera >= 1""")
    t["grupo"] = grupo(t["posicion"])
    t["etapa"] = etapa(t["anio_carrera"])
    t["pct"] = 100 * t["pct_cap"]
    # titular-equivalente: una temporada completa de snaps (participación 1,0)
    t["titular_eq"] = t["participacion"].fillna(0).clip(upper=1)

    filas = []
    for (g, e), d in t[t.grupo.isin(["QB", "RB", "WR", "TE"]) & t.valor_reemplazo.notna()].groupby(["grupo", "etapa"]):
        est, lo, hi = razon_boot(d, "valor_reemplazo", "pct")
        filas.append({"grupo": g, "etapa": e, "valor_por_pct": est, "ic_bajo": lo, "ic_alto": hi,
                      "temporadas": len(d), "jugadores": d.jugador.nunique(), "pct_cap_mediano": d["pct"].median()})
    valor = pd.DataFrame(filas)

    filas = []
    for (g, e), d in t[t.grupo.isin(["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB"]) & t.participacion.notna()].groupby(["grupo", "etapa"]):
        est, lo, hi = razon_boot(d, "titular_eq", "pct")
        filas.append({"grupo": g, "etapa": e, "titular_por_pct": est, "ic_bajo": lo, "ic_alto": hi, "temporadas": len(d)})
    snaps = pd.DataFrame(filas)

    # los ejemplos más extremos: grandes temporadas con contrato de novato
    ej = t[t.grupo.eq("QB") & t.valor_reemplazo.notna() & t.anio_carrera.le(4)].nlargest(10, "valor_reemplazo")
    return {"valor": registros(valor), "snaps": registros(snaps),
            "ejemplos_qb": registros(ej[["temporada", "nombre", "anio_carrera", "valor_reemplazo", "pct", "cap_usd"]])}
