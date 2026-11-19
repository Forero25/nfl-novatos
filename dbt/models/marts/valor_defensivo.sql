-- "EPA de jugadas destacadas" de cada defensor: sacks, intercepciones, pases defendidos, balones forzados
-- (perdidos) y tacleadas para pérdida. Cada jugada con EPA negativo para la ofensiva se reparte en partes
-- iguales entre los defensores acreditados. No mide cobertura ni defensa contra la carrera fuera de esas jugadas.
with c as (
  select temporada, partido, play_id, epa, unnest([
    sack_player_id, half_sack_1_player_id, half_sack_2_player_id, interception_player_id,
    case when not completo then pass_defense_1_player_id end, case when not completo then pass_defense_2_player_id end,
    case when fumble_perdido then forced_fumble_player_1_player_id end,
    tackle_for_loss_1_player_id, tackle_for_loss_2_player_id]) as jugador
  from {{ ref('stg_jugadas') }} where epa < 0
), d as (select distinct temporada, partido, play_id, epa, jugador from c where jugador is not null),
w as (select *, count(*) over (partition by partido, play_id) n from d)
select temporada, jugador, count(*) jugadas_destacadas, sum(-epa / n) as epa_destacado
from w group by all
