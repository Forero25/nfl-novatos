-- Posición del jugador en cada temporada: la más frecuente en sus partidos (snaps, desde 2013).
-- El catálogo de jugadores trae solo la posición más reciente (p. ej., un WR que terminó como TE).
select s.temporada, p.jugador, mode(s.pos_snap) as posicion
from {{ ref('stg_snaps') }} s join {{ ref('stg_jugadores') }} p on p.pfr_id = s.pfr_id
where s.pos_snap is not null group by all
