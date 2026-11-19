"""Panorama de cuánto juegan los novatos y qué tiene que ver con los resultados del equipo."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from .datos import ULTIMA_COMPLETA, grupo, leer, registros


def panorama() -> dict:
    s = leer("""select s.temporada, s.equipo, s.partido, s.pos_snap, s.snaps_of, s.snaps_def, s.equipo_of,
                       p.temporada_novato = s.temporada as novato
                from staging.stg_snaps s left join staging.stg_jugadores p on p.pfr_id = s.pfr_id
                order by s.partido, s.equipo, s.pfr_id""")
    s["novato"] = s["novato"].fillna(False).astype(bool)
    liga = s.groupby("temporada").apply(lambda d: pd.Series({
        "ataque": d.loc[d.novato, "snaps_of"].sum() / d["snaps_of"].sum(),
        "defensa": d.loc[d.novato, "snaps_def"].sum() / d["snaps_def"].sum()}), include_groups=False).reset_index()
    # quarterback titular de cada partido: el QB con más snaps ofensivos de su equipo
    qb = s[s.pos_snap == "QB"].sort_values(["snaps_of", "novato"], ascending=False, kind="stable").drop_duplicates(["partido", "equipo"])
    qbs = qb.groupby("temporada").agg(partidos=("novato", "size"), con_qb_novato=("novato", "sum")).reset_index()
    qbs["pct"] = qbs["con_qb_novato"] / qbs["partidos"]
    return {"liga": registros(liga), "qb_titular": registros(qbs)}


def resultados() -> dict:
    e = leer(f"select * from marts.equipos where temporada between 2013 and {ULTIMA_COMPLETA} and part_novatos is not null")
    e = e.sort_values(["equipo", "temporada"])
    e["dif_siguiente"] = e.groupby("equipo")["dif_por_partido"].shift(-1)
    e["pn10"] = 10 * e["part_novatos"]  # coeficiente por cada 10 puntos porcentuales de snaps de novatos
    out = {}
    especs = {
        "mismo_anio_simple": ("dif_por_partido ~ pn10", e),
        "mismo_anio_controles": ("dif_por_partido ~ pn10 + dif_previa + C(temporada) + C(equipo)", e.dropna(subset=["dif_previa"])),
        "anio_siguiente": ("dif_siguiente ~ pn10 + dif_por_partido + C(temporada) + C(equipo)", e.dropna(subset=["dif_siguiente"])),
    }
    for k, (f, d) in especs.items():
        m = smf.ols(f, data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["equipo"])[0]})
        out[k] = {"coef": m.params["pn10"], "ee": m.bse["pn10"], "p": m.pvalues["pn10"],
                  "ic_bajo": m.conf_int().loc["pn10", 0], "ic_alto": m.conf_int().loc["pn10", 1], "n": int(m.nobs)}
    out["descriptivo"] = {"media_part": e.part_novatos.mean(), "min": e.part_novatos.min(), "max": e.part_novatos.max()}
    out["extremos"] = registros(e.nlargest(5, "part_novatos")[["temporada", "equipo", "part_novatos", "victorias", "dif_por_partido"]])
    return out


def correr() -> dict:
    return {"panorama": panorama(), "resultados": resultados()}
