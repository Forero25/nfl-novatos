-- Una fila por jugador y temporada con todo lo que se sabe de él: experiencia, participación, valor y salario.
with base as (
  select p.jugador, s.temporada from {{ ref('stg_jugadores') }} p
  join (select jugador, temporada from {{ ref('valor_ofensivo') }}
        union select jugador, temporada from {{ ref('valor_defensivo') }}
        union select jugador, temporada from {{ ref('participacion') }} where jugador is not null) s using (jugador)
)
select b.temporada, b.jugador, p.nombre, coalesce(pt.posicion, p.posicion) as posicion, p.posicion as posicion_actual, p.temporada_novato,
       b.temporada - p.temporada_novato + 1 as anio_carrera, b.temporada = p.temporada_novato as novato,
       p.ronda, p.pick, p.anio_draft = p.temporada_novato and p.pick is not null as drafteado,
       date_diff('day', p.nacimiento, make_date(b.temporada, 9, 1)) / 365.25 as edad,
       pa.equipo_principal as equipo, pa.partidos, pa.participacion, pa.part_of, pa.part_def, pa.lado,
       vo.jugadas, vo.epa, vo.epa2, vo.epa_jugada, vo.tasa_exito, vo.valor_reemplazo,
       vd.jugadas_destacadas, vd.epa_destacado, c.pct_cap, c.cap_usd
from base b join {{ ref('stg_jugadores') }} p using (jugador)
left join {{ ref('participacion') }} pa on pa.jugador = b.jugador and pa.temporada = b.temporada
left join {{ ref('valor_ofensivo') }} vo on vo.jugador = b.jugador and vo.temporada = b.temporada
left join {{ ref('valor_defensivo') }} vd on vd.jugador = b.jugador and vd.temporada = b.temporada
left join {{ ref('stg_posicion_temporada') }} pt on pt.jugador = b.jugador and pt.temporada = b.temporada
left join {{ ref('stg_contratos') }} c on c.jugador = b.jugador and c.temporada = b.temporada
where p.temporada_novato is not null and b.temporada >= p.temporada_novato
