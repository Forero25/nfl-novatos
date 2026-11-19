-- EPA y valor sobre reemplazo por jugador ofensivo y temporada.
-- QB: todas sus jugadas de pase (incluye scrambles y sacks) con qb_epa, más sus carreras diseñadas.
-- RB/WR/TE: carreras con epa y pases dirigidos a él (objetivos) con epa.
with q as (
  select temporada, passer_id as jugador, count(*) jugadas, sum(qb_epa) epa, sum(exito) exitos from {{ ref('stg_jugadas') }}
  where dropback and passer_id is not null group by all
), r as (
  select temporada, rusher_id, count(*), sum(epa), sum(exito) from {{ ref('stg_jugadas') }}
  where tipo = 'run' and not dropback and rusher_id is not null group by all
), t as (
  select temporada, receiver_id, count(*), sum(epa), sum(exito) from {{ ref('stg_jugadas') }}
  where tipo = 'pass' and receiver_id is not null group by all
), u as (select * from q union all select * from r union all select * from t),
j as (
  select u.temporada, u.jugador, p.nombre, p.posicion, sum(jugadas) jugadas, sum(epa) epa, sum(exitos) exitos
  from u join {{ ref('stg_jugadores') }} p using (jugador)
  where p.posicion in ('QB', 'RB', 'WR', 'TE') group by all
),
r2 as (  -- nivel de reemplazo: EPA por jugada de quienes quedan por fuera de los titulares de la liga
  select temporada, posicion, sum(epa) / sum(jugadas) as epa_reemplazo
  from (select *, row_number() over (partition by temporada, posicion order by jugadas desc, jugador) rk from j)
  where jugadas >= 20 and rk > case posicion when 'QB' then 32 when 'RB' then 48 when 'WR' then 96 else 48 end
  group by all
)
select j.*, j.epa / j.jugadas as epa_jugada, j.exitos / j.jugadas as tasa_exito, r2.epa_reemplazo,
       j.epa - j.jugadas * r2.epa_reemplazo as valor_reemplazo
from j join r2 using (temporada, posicion)
