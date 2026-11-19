"""Corre todos los análisis y escribe resultados/*.json y publicado/*.csv (lo que lee la app)."""
from __future__ import annotations

import pandas as pd

from . import contratos, equipos, mejores, prediccion
from .datos import RAIZ, grupo, guardar, leer


def publicar() -> None:
    pub = RAIZ / "publicado"
    pub.mkdir(exist_ok=True)
    t = leer("""select temporada, jugador, nombre, posicion, equipo, ronda, pick, drafteado, anio_carrera, partidos,
                       participacion, jugadas, epa, epa_jugada, tasa_exito, valor_reemplazo, jugadas_destacadas,
                       epa_destacado, pct_cap from marts.temporadas where temporada >= 2010 order by temporada, jugador""")
    t["grupo"] = grupo(t["posicion"])
    t.round(4).to_csv(pub / "temporadas.csv", index=False)
    leer("select * from marts.equipos order by temporada, equipo").round(4).to_csv(pub / "equipos.csv", index=False)
    d = prediccion.datos()
    p = prediccion.pronosticos(d)
    p[["jugador", "nombre", "temporada", "grupo", "pick_ef", "participacion", "prob"]].round(4).to_csv(pub / "pronosticos.csv", index=False)


def main() -> None:
    guardar("mejores", mejores.correr()); print("mejores")
    guardar("contratos", contratos.correr()); print("contratos")
    guardar("prediccion", prediccion.correr()); print("prediccion")
    guardar("equipos", equipos.correr()); print("equipos")
    publicar(); print("publicado")


if __name__ == "__main__":
    main()
