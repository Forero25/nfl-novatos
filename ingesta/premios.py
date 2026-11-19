"""Ganadores del Novato Ofensivo y Defensivo del Año de la AP, desde Wikipedia (CC BY-SA 4.0).

Se usa solo para validar las métricas: ¿el mejor novato según los datos coincide con el que eligieron los votantes?
Corre en GitHub Actions y guarda entradas/premios.csv.
"""
from __future__ import annotations

import csv
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

PAGINA = "AP NFL Offensive Rookie of the Year"  # una sola página con las secciones ===Offensive=== y ===Defensive===
SECCIONES = {"ofensivo": "Offensive", "defensivo": "Defensive"}
SALIDA = Path(__file__).resolve().parents[1] / "entradas" / "premios.csv"


def wikitexto(titulo: str) -> str:
    q = urllib.parse.urlencode({"action": "parse", "page": titulo, "prop": "wikitext", "format": "json", "formatversion": 2, "redirects": 1})
    req = urllib.request.Request(f"https://en.wikipedia.org/w/api.php?{q}", headers={"User-Agent": "portafolio-nfl-novatos/1.0 (github.com/Forero25/nfl-novatos)"})
    return json.load(urllib.request.urlopen(req, timeout=60))["parse"]["wikitext"]


def ganadores(texto: str, desde: int = 2010) -> list[tuple[int, str]]:
    """Recorre las filas de la tabla: cada fila trae el año de la temporada y luego el enlace al jugador."""
    filas = re.split(r"\n\|-", texto)
    out = []
    for f in filas:
        a = re.search(r"\[\[(\d{4}) NFL season\|", f) or re.search(r"\|\s*(\d{4})\s*\n", f)
        if not a:
            continue
        anio = int(a.group(1))
        resto = f[a.end():]
        j = re.search(r"\{\{sortname\|([^|}]+)\|([^|}]+)", resto) or re.search(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]", resto)
        if not j or anio < desde:
            continue
        nombre = f"{j.group(1)} {j.group(2)}" if "sortname" in j.group(0) else (j.group(2) or j.group(1))
        nombre = re.sub(r"\s*\(.*?\)$", "", nombre).strip()
        out.append((anio, nombre))
    vistos, final = set(), []
    for a, n in out:
        if a not in vistos:
            vistos.add(a); final.append((a, n))
    return final


def main() -> None:
    SALIDA.parent.mkdir(exist_ok=True)
    with open(SALIDA, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["premio", "temporada", "nombre"])
        texto = wikitexto(PAGINA)
        for premio, seccion in SECCIONES.items():
            m = re.search(r"===\s*" + seccion + r"\s*===(.*?)(?=\n===?[^=]|\Z)", texto, re.S)
            if not m:
                raise SystemExit(f"no encontré la sección {seccion}")
            g = ganadores(m.group(1))
            if len(g) < 15:
                raise SystemExit(f"muy pocos ganadores en {seccion}: {g}")
            print(premio, g)
            for a, n in g:
                w.writerow([premio, a, n])


if __name__ == "__main__":
    main()
