-- Snaps por jugador y partido (desde 2013). El total del equipo en un partido es el máximo individual.
with s as (
  select season as temporada, week as semana, game_id as partido, pfr_player_id as pfr_id, team as equipo, position as pos_snap,
         coalesce(offense_snaps, 0) as snaps_of, coalesce(defense_snaps, 0) as snaps_def, coalesce(st_snaps, 0) as snaps_esp
  from read_parquet('{{ var("raw") }}/snaps/*.parquet', union_by_name = true)
  where game_type = 'REG'
)
select *, max(snaps_of) over (partition by partido, equipo) as equipo_of,
          max(snaps_def) over (partition by partido, equipo) as equipo_def
from s
