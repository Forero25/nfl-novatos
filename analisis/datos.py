from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("NFL_DB", RAIZ / "data" / "nfl.duckdb"))
RES = RAIZ / "resultados"
ULTIMA_COMPLETA = 2025
TEMPORADA_ACTUAL = 2026

GRUPOS = {"QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE",
          "T": "OL", "G": "OL", "C": "OL", "OT": "OL", "OG": "OL", "OL": "OL",
          "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL",
          "OLB": "LB", "ILB": "LB", "MLB": "LB", "LB": "LB",
          "CB": "DB", "S": "DB", "FS": "DB", "SS": "DB", "DB": "DB", "SAF": "DB",
          "K": "ST", "P": "ST", "LS": "ST"}


def leer(sql: str) -> pd.DataFrame:
    with duckdb.connect(str(DB), read_only=True) as c:
        return c.sql(sql).df()


def grupo(pos: pd.Series) -> pd.Series:
    return pos.map(GRUPOS).fillna("otro")


def normalizar(nombre: str) -> str:
    s = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", s.lower())
    return re.sub(r"[^a-z]", "", s)


def limpio(o):
    if isinstance(o, dict):
        return {str(k): limpio(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpio(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if (math.isnan(o) or math.isinf(o)) else round(float(o), 4)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    return o


def registros(df: pd.DataFrame) -> list[dict]:
    return limpio(df.to_dict(orient="records"))


def guardar(nombre: str, obj) -> None:
    RES.mkdir(exist_ok=True)
    with open(RES / f"{nombre}.json", "w", encoding="utf-8") as f:
        json.dump(limpio(obj), f, ensure_ascii=False, indent=1, allow_nan=False)
