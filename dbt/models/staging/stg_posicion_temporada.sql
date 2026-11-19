-- Posición del jugador en cada temporada: la más frecuente en sus partidos (snaps, desde 2013).
-- El catálogo de jugadores trae solo la posición más reciente (p. ej., un WR que terminó como TE).
-- Empates: gana la posición alfabéticamente primera, para que el resultado sea siempre el mismo.
with c as (
  select s.temporada, p.jugador, s.pos_snap as posicion, count(*) n
  from {{ ref('stg_snaps') }} s join {{ ref('stg_jugadores') }} p on p.pfr_id = s.pfr_id
  where s.pos_snap is not null group by all
)
select temporada, jugador, posicion from c
qualify row_number() over (partition by temporada, jugador order by n desc, posicion) = 1
