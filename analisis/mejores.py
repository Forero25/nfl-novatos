"""¿Quién fue el mejor novato? Valor sobre reemplazo (ataque), jugadas destacadas (defensa) y validación con los premios."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .datos import RAIZ, TEMPORADA_ACTUAL, ULTIMA_COMPLETA, grupo, leer, normalizar, registros

COLS = ["temporada", "nombre", "posicion", "equipo", "pick", "ronda", "jugadas", "epa", "epa_jugada", "tasa_exito",
        "valor_reemplazo", "participacion", "jugadas_destacadas", "epa_destacado", "snaps_def", "pct_cap"]


def temporadas() -> pd.DataFrame:
    t = leer("""select t.*, p.snaps_def from marts.temporadas t
                left join marts.participacion p using (temporada, jugador)""")
    t["grupo"] = grupo(t["posicion"])
    return t


def encoger(t: pd.DataFrame, minimo: int = 50, detalle: dict | None = None) -> pd.Series:
    """EPA por jugada encogido hacia la media de su posición (Bayes empírico, método de momentos).

    Con pocas jugadas el promedio es ruido; el encogimiento pesa cada jugador por n / (n + k),
    donde k = varianza de una jugada / varianza real entre jugadores.
    """
    out = pd.Series(np.nan, index=t.index)
    for pos, g in t[t["jugadas"] >= 1].groupby("posicion"):
        base = g[g["jugadas"] >= minimo]
        mu = np.average(base["epa_jugada"], weights=base["jugadas"])
        var_obs = np.average((base["epa_jugada"] - mu) ** 2, weights=base["jugadas"])
        # varianza de una jugada dentro de un mismo jugador (agrupada): cuánto ruido trae cada jugada
        var_jugada = (base["epa2"] - base["epa"] ** 2 / base["jugadas"]).sum() / (base["jugadas"] - 1).sum()
        var_ruido = var_jugada / base["jugadas"].mean()
        tau2 = max(var_obs - var_ruido, 1e-6)
        k = var_jugada / tau2
        if detalle is not None:
            detalle[pos] = {"media": mu, "sd_jugada": var_jugada ** 0.5, "sd_real": tau2 ** 0.5, "k": k}
        out.loc[g.index] = mu + (g["epa_jugada"] - mu) * g["jugadas"] / (g["jugadas"] + k)
    return out


def sd_jugada() -> dict:
    """Desviación típica real del EPA de una jugada, para justificar las constantes de encoger()."""
    d = leer("""select case when dropback then 'pase' else 'carrera' end tipo, stddev(epa) sd from staging.stg_jugadas group by 1""")
    return dict(zip(d["tipo"], d["sd"]))


def validar(t: pd.DataFrame, premios: pd.DataFrame) -> dict:
    out = {}
    for premio, col, lado in [("ofensivo", "valor_reemplazo", ["QB", "RB", "WR", "TE"]), ("defensivo", "epa_destacado", ["DL", "LB", "DB"])]:
        filas = []
        for _, p in premios[premios.premio == premio].iterrows():
            n = t[(t.novato) & (t.temporada == p.temporada) & (t.grupo.isin(lado)) & t[col].notna()].copy()
            n = n.sort_values(col, ascending=False).reset_index(drop=True)
            n["clave"] = n["nombre"].map(normalizar)
            pos = n.index[n["clave"] == normalizar(p.nombre)]
            filas.append({"temporada": int(p.temporada), "ganador": p.nombre,
                          "puesto": int(pos[0]) + 1 if len(pos) else None,
                          "lider_datos": n.loc[0, "nombre"] if len(n) else None})
        f = pd.DataFrame(filas)
        ok = f["puesto"].dropna()
        out[premio] = {"filas": registros(f), "primero": int((ok == 1).sum()), "top3": int((ok <= 3).sum()),
                       "top10": int((ok <= 10).sum()), "n": int(len(f)), "mediana_puesto": float(ok.median()) if len(ok) else None}
    return out


def correr() -> dict:
    t = temporadas()
    det: dict = {}
    t["epa_jugada_enc"] = encoger(t, detalle=det)
    nov = t[t.novato & (t.temporada <= ULTIMA_COMPLETA)]
    of = nov[nov.grupo.isin(["QB", "RB", "WR", "TE"]) & nov.valor_reemplazo.notna()]
    de = nov[nov.grupo.isin(["DL", "LB", "DB"]) & nov.epa_destacado.notna()].copy()
    de["destacado_100"] = 100 * de["epa_destacado"] / de["snaps_def"].where(de["snaps_def"] >= 300)
    premios = pd.read_csv(RAIZ / "entradas" / "premios.csv")
    cols = COLS + ["epa_jugada_enc", "grupo"]

    # contexto: dónde queda un novato frente a todos los jugadores (no solo novatos)
    todos = t[t.grupo.isin(["QB", "RB", "WR", "TE"]) & t.valor_reemplazo.notna() & (t.temporada <= ULTIMA_COMPLETA)]
    pct = lambda r: float((todos[(todos.temporada == r.temporada) & (todos.grupo == r.grupo)].valor_reemplazo < r.valor_reemplazo).mean())
    top_of = of.sort_values("valor_reemplazo", ascending=False).head(25).copy()
    top_of["percentil_temporada"] = top_of.apply(pct, axis=1)

    porjugada = of[((of.grupo == "QB") & (of.jugadas >= 250)) | ((of.grupo != "QB") & (of.jugadas >= 80))]
    actual = t[t.novato & (t.temporada == TEMPORADA_ACTUAL)]
    partidos = leer(f"select max(n) n from (select equipo, count(*) n from staging.stg_partidos where temporada = {TEMPORADA_ACTUAL} group by 1)")["n"].iloc[0]
    of26 = actual[actual.grupo.isin(["QB", "RB", "WR", "TE"]) & actual.valor_reemplazo.notna()].copy()
    of26["ritmo_17"] = of26["valor_reemplazo"] * 17 / partidos
    de26 = actual[actual.grupo.isin(["DL", "LB", "DB"]) & actual.epa_destacado.notna()].copy()
    de26["ritmo_17"] = de26["epa_destacado"] * 17 / partidos

    res = {
        "ofensivos": registros(top_of[cols + ["percentil_temporada"]]),
        "por_posicion": {g: registros(of[of.grupo == g].nlargest(8, "valor_reemplazo")[cols]) for g in ["QB", "RB", "WR", "TE"]},
        "por_jugada": {g: registros(porjugada[porjugada.grupo == g].nlargest(8, "epa_jugada_enc")[cols]) for g in ["QB", "RB", "WR", "TE"]},
        "defensivos": registros(de.nlargest(25, "epa_destacado")[cols + ["destacado_100"]]),
        "defensivos_por_grupo": {g: registros(de[de.grupo == g].nlargest(8, "epa_destacado")[cols + ["destacado_100"]]) for g in ["DL", "LB", "DB"]},
        "validacion": validar(t, premios),
        "clase_2026": {"partidos_jugados": int(partidos),
                       "ofensivos": registros(of26.nlargest(10, "valor_reemplazo")[cols + ["ritmo_17"]]),
                       "defensivos": registros(de26.nlargest(10, "epa_destacado")[cols + ["ritmo_17"]])},
        "encogimiento": det,
        "robustez": robustez(),
    }
    return res


def robustez(umbrales=((24, 36, 72, 36), (32, 48, 96, 48), (40, 64, 128, 64))) -> list[dict]:
    """¿Cambia el podio si el nivel de reemplazo se define con más o menos titulares por posición?"""
    v = leer(f"select * from marts.valor_ofensivo where temporada <= {ULTIMA_COMPLETA}")
    nov = leer("select jugador, temporada from marts.temporadas where novato")
    out, base = [], None
    for u in umbrales:
        n = dict(zip(["QB", "RB", "WR", "TE"], u))
        v["rk"] = v.groupby(["temporada", "posicion"])["jugadas"].rank(ascending=False, method="first")
        fuera = v[(v.jugadas >= 20) & (v.rk > v.posicion.map(n))]
        r = fuera.groupby(["temporada", "posicion"]).apply(lambda g: g.epa.sum() / g.jugadas.sum(), include_groups=False).rename("rep").reset_index()
        x = v.merge(r, on=["temporada", "posicion"]).merge(nov, on=["jugador", "temporada"])
        x["valor"] = x.epa - x.jugadas * x.rep
        x = x.sort_values("valor", ascending=False).reset_index(drop=True)
        top = x.head(10)[["nombre", "temporada"]].apply(tuple, axis=1).tolist()
        if base is None:
            base = top if u == (32, 48, 96, 48) else None
        out.append({"titulares": n, "top5": [f"{a} ({b})" for a, b in top[:5]], "top10": top})
    ref = [o for o in out if o["titulares"]["QB"] == 32][0]["top10"]
    for o in out:
        o["coinciden_top10"] = len(set(o.pop("top10")) & set(ref))
    return out
