#!/usr/bin/env bash
# Pipeline completo: descarga → DuckDB con dbt (modelos y pruebas) → análisis → pruebas de Python.
set -euo pipefail
python -m ingesta.descargar
(cd dbt && dbt build --profiles-dir . --target local)
python -W ignore -m analisis.correr
python -m pytest -q tests
