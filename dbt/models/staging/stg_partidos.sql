-- Un registro por equipo y partido de temporada regular, con el resultado.
with p as (
  select distinct season as temporada, week as semana, game_id as partido, home_team, away_team, home_score, away_score
  from read_parquet('{{ var("raw") }}/pbp/*.parquet', union_by_name = true)
  where season_type = 'REG' and home_score is not null
)
select temporada, semana, partido, home_team as equipo, home_score - away_score as diferencia from p
union all
select temporada, semana, partido, away_team, away_score - home_score from p
