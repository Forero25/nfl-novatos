-- Jugadas de temporada regular con EPA, sin intentos de dos puntos ni jugadas abortadas.
select
  season as temporada, week as semana, game_id as partido, play_id, posteam as ofensiva, defteam as defensiva,
  play_type as tipo, coalesce(qb_dropback, 0) = 1 as dropback, coalesce(qb_scramble, 0) = 1 as scramble,
  epa, qb_epa, coalesce(success, 0) as exito, cpoe,
  passer_id, rusher_id, receiver_id,
  sack_player_id, half_sack_1_player_id, half_sack_2_player_id,
  interception_player_id, pass_defense_1_player_id, pass_defense_2_player_id,
  forced_fumble_player_1_player_id, tackle_for_loss_1_player_id, tackle_for_loss_2_player_id,
  qb_hit_1_player_id, qb_hit_2_player_id,
  coalesce(sack, 0) = 1 as es_sack, coalesce(interception, 0) = 1 as es_int,
  coalesce(fumble_lost, 0) = 1 as fumble_perdido, coalesce(complete_pass, 0) = 1 as completo
from read_parquet('{{ var("raw") }}/pbp/*.parquet', union_by_name = true)
where season_type = 'REG' and epa is not null and play_type in ('pass', 'run')
  and coalesce(two_point_attempt, 0) = 0 and coalesce(aborted_play, 0) = 0
