-- Estadísticas avanzadas de defensa de Pro Football Reference (desde 2018).
select season as temporada, pfr_id, tm as equipo, pos, g as partidos, prss as presiones, sk as sacks, hrry as apuros,
       qbkd as derribos, comb as tacleadas, m_tkl as tacleadas_falladas, tgt as objetivos, cmp as completos_permitidos,
       yds as yardas_permitidas, rat as rating_permitido
from read_csv('{{ var("raw") }}/pfr_def.csv', sample_size = -1)
