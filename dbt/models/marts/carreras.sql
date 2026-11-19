-- Para cada novato: su temporada de novato y lo que pasó en los años 2 a 4.
-- "Titular establecido": al menos dos de los años 2 a 4 con participación de 50 % o más.
with t as (select * from {{ ref('temporadas') }}),
n as (select * from t where novato),
sig as (
  select jugador, count(*) filter (where participacion >= 0.5) temporadas_titular, max(temporada) ultima_vista,
         max(participacion) mejor_participacion
  from t where anio_carrera between 2 and 4 group by all
)
select n.*, coalesce(sig.temporadas_titular, 0) as temporadas_titular_2a4,
       coalesce(sig.temporadas_titular, 0) >= 2 as titular_establecido,
       n.temporada + 3 <= {{ var('ultima_completa') }} as completo
from n left join sig using (jugador)
