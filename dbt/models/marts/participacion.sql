-- Participación por jugador y temporada: snaps propios sobre los snaps de su equipo en los partidos de la temporada.
-- El denominador son todos los partidos del calendario del equipo (17 desde 2021, 16 antes), no solo los que jugó.
with s as (select * from {{ ref('stg_snaps') }}),
eq as (  -- snaps totales de cada equipo por temporada y lado
  select temporada, equipo, sum(equipo_of) of_total, sum(equipo_def) def_total, count(*) partidos
  from (select distinct temporada, partido, equipo, equipo_of, equipo_def from s) group by all
), jt as (  -- un jugador puede pasar por varios equipos
  select temporada, pfr_id, equipo, sum(snaps_of) of_j, sum(snaps_def) def_j, sum(snaps_esp) esp_j, count(*) partidos_j
  from s group by all
), liga as (select temporada, avg(of_total / partidos) of_pp, avg(def_total / partidos) def_pp, max(partidos) partidos from eq group by all)
select jt.temporada, p.jugador, jt.pfr_id, any_value(p.nombre) nombre, any_value(p.posicion) posicion,
       string_agg(jt.equipo, '/' order by jt.partidos_j desc) equipos, arg_max(jt.equipo, jt.partidos_j) equipo_principal,
       sum(partidos_j) partidos, sum(of_j) snaps_of, sum(def_j) snaps_def, sum(esp_j) snaps_esp,
       sum(of_j) / any_value(l.of_pp * l.partidos) as part_of,
       sum(def_j) / any_value(l.def_pp * l.partidos) as part_def,
       greatest(sum(of_j) / any_value(l.of_pp * l.partidos), sum(def_j) / any_value(l.def_pp * l.partidos)) as participacion,
       case when sum(of_j) >= sum(def_j) then 'ofensiva' else 'defensa' end as lado
from jt join liga l using (temporada)
left join {{ ref('stg_jugadores') }} p on p.pfr_id = jt.pfr_id
group by jt.temporada, p.jugador, jt.pfr_id
