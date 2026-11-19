select gsis_id as jugador, display_name as nombre, position as posicion, position_group as grupo,
       pfr_id, rookie_season as temporada_novato, draft_year as anio_draft, draft_round as ronda,
       draft_pick as pick, try_cast(birth_date as date) as nacimiento, height as estatura, weight as peso,
       college_name as universidad
from read_csv('{{ var("raw") }}/players.csv', all_varchar = false, sample_size = -1)
where gsis_id is not null
