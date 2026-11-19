"""Descarga los datos de nflverse (CC BY 4.0) a data/raw.

Fuente: https://github.com/nflverse/nflverse-data (releases). Todo es público; no hay datos personales
más allá de nombres y estadísticas deportivas de jugadores profesionales.
"""
from __future__ import annotations

import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://github.com/nflverse/nflverse-data/releases/download"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
PRIMERA, ULTIMA = 2010, 2026


def archivos(ultima: int = ULTIMA) -> dict[str, str]:
    a = {
        "players.csv": "players/players.csv",
        "draft_picks.csv": "draft_picks/draft_picks.csv",
        "contratos.parquet": "contracts/historical_contracts.parquet",
        "pfr_def.csv": "pfr_advstats/advstats_season_def.csv",
    }
    for y in range(PRIMERA, ultima + 1):
        a[f"pbp/{y}.parquet"] = f"pbp/play_by_play_{y}.parquet"
        if y >= 2013:  # los snaps de nflverse empiezan en 2013 (2012 viene vacío)
            a[f"snaps/{y}.parquet"] = f"snap_counts/snap_counts_{y}.parquet"
    return a


def bajar(url: str, destino: Path, intentos: int = 4) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    for i in range(intentos):
        try:
            tmp = destino.with_suffix(destino.suffix + ".tmp")
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                f.write(r.read())
            tmp.replace(destino)
            return
        except Exception as e:  # red inestable: reintenta con espera
            if i == intentos - 1:
                raise RuntimeError(f"no se pudo bajar {url}: {e}") from e
            time.sleep(5 * (i + 1))


def main(forzar: bool = False) -> None:
    for local, remoto in archivos().items():
        destino = RAW / local
        # la temporada en curso y los catálogos cambian cada semana: siempre se vuelven a bajar
        fijo = destino.exists() and not forzar and any(f"/{y}." in "/" + local for y in range(PRIMERA, ULTIMA))
        if fijo:
            continue
        bajar(f"{BASE}/{remoto}", destino)
        print("ok", local)


if __name__ == "__main__":
    main(forzar="--forzar" in sys.argv)
