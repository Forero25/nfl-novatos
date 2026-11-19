-- Equipo y temporada: cuántos snaps jugaron los novatos y cómo le fue al equipo.
with s as (
  select s.temporada, s.equipo, s.snaps_of + s.snaps_def as snaps, p.temporada_novato = s.temporada as novato
  from {{ ref('stg_snaps') }} s left join {{ ref('stg_jugadores') }} p on p.pfr_id = s.pfr_id
), r as (
  select temporada, equipo, sum(snaps) filter (where novato) / sum(snaps) as part_novatos from s group by all
), res as (
  select temporada, equipo, count(*) partidos, sum(diferencia) diferencia, sum((diferencia > 0)::int + 0.5 * (diferencia = 0)::int) victorias
  from {{ ref('stg_partidos') }} group by all
)
select res.*, res.victorias / res.partidos as pct_victorias, res.diferencia / res.partidos as dif_por_partido,
       r.part_novatos,
       lag(res.diferencia / res.partidos) over (partition by res.equipo order by res.temporada) as dif_previa
from res left join r using (temporada, equipo)
