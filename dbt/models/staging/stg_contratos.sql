-- Peso en el tope salarial (cap) de cada jugador por temporada, desde el historial de OverTheCap vía nflverse.
with h as (
  select gsis_id as jugador, unnest(season_history) as h
  from read_parquet('{{ var("raw") }}/contratos.parquet') where gsis_id is not null
)
select jugador, try_cast(h.year as integer) as temporada, max(h.cap_percent) as pct_cap, max(h.cap_number) as cap_usd
from h where h.cap_percent is not null group by all
