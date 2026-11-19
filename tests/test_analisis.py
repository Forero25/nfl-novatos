import json
from pathlib import Path

import numpy as np
import pandas as pd

from analisis import contratos, prediccion
from analisis.datos import normalizar
from analisis.mejores import encoger

RES = Path(__file__).resolve().parents[1] / "resultados"


def test_nombres_de_wikipedia_y_nflverse_coinciden():
    assert normalizar("C. J. Stroud") == normalizar("C.J. Stroud")
    assert normalizar("Odell Beckham Jr.") == normalizar("Odell Beckham")
    assert normalizar("Ja'Marr Chase") == normalizar("JaMarr Chase")


def test_encogimiento_pesa_mas_a_quien_tiene_mas_jugadas():
    rng = np.random.default_rng(0)
    filas = []
    for i in range(300):
        n = int(rng.integers(20, 600)); verdad = rng.normal(0.05, 0.1)
        epas = rng.normal(verdad, 1.3, n)
        filas.append({"posicion": "WR", "jugadas": n, "epa": epas.sum(), "epa2": (epas ** 2).sum(), "epa_jugada": epas.mean(), "verdad": verdad})
    t = pd.DataFrame(filas)
    t["enc"] = encoger(t)
    # el encogido se acerca más a la verdad que el promedio crudo
    assert ((t.enc - t.verdad) ** 2).mean() < ((t.epa_jugada - t.verdad) ** 2).mean()
    # y el jugador con pocas jugadas se mueve más hacia la media que el de muchas
    poco, mucho = t.nsmallest(20, "jugadas"), t.nlargest(20, "jugadas")
    assert (poco.enc - poco.epa_jugada).abs().mean() > (mucho.enc - mucho.epa_jugada).abs().mean()


def test_razon_bootstrap():
    d = pd.DataFrame({"jugador": list("aabbcc"), "v": [2, 2, 4, 4, 6, 6], "c": [1, 1, 2, 2, 3, 3]})
    est, lo, hi = contratos.razon_boot(d, "v", "c")
    assert est == 2 and lo == 2 and hi == 2


def test_la_evaluacion_no_mira_el_futuro():
    """Cambiar el resultado de las clases k-2 y k-1 no puede cambiar el pronóstico de la clase k."""
    rng = np.random.default_rng(1)
    n = 120 * 10
    d = pd.DataFrame({"jugador": range(n), "nombre": "x", "temporada": np.repeat(range(2013, 2023), 120), "completo": True,
                      "grupo": rng.choice(prediccion.GRUPOS, n), "pick_ef": rng.integers(1, 300, n)})
    for c in prediccion.DRAFT + prediccion.NOVATO:
        d[c] = rng.normal(size=n)
    d["y"] = (d["participacion"] + rng.normal(size=n) > 0.8).astype(int)
    p1, _ = prediccion.evaluar(d, clases=[2020])
    d2 = d.copy(); m = d2.temporada.isin([2018, 2019]); d2.loc[m, "y"] = 1 - d2.loc[m, "y"]
    p2, _ = prediccion.evaluar(d2, clases=[2020])
    for c in prediccion.modelos():
        assert np.allclose(p1[c], p2[c])


def test_resultados_coherentes():
    m = json.loads((RES / "mejores.json").read_text())
    assert m["ofensivos"][0]["nombre"] == "Robert Griffin III"
    assert m["validacion"]["ofensivo"]["n"] == 16 and m["validacion"]["defensivo"]["n"] == 16
    p = json.loads((RES / "prediccion.json").read_text())
    met = {x["modelo"]: x for x in p["metricas"]}
    assert met["Draft + novato (logística)"]["auc"] > met["Solo draft (logística)"]["auc"]
    assert p["dif_auc_novato_vs_draft"]["ic_bajo"] > 0
