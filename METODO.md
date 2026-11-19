# Método

## 1. Datos

| Fuente | Qué trae | Desde |
|---|---|---|
| nflverse `pbp` | Cada jugada con EPA, quién pasó, corrió o recibió, y quién hizo la jugada defensiva | 2010 |
| nflverse `snap_counts` | Snaps de cada jugador por partido | 2013 (2012 viene vacío) |
| nflverse `players`, `draft_picks` | Temporada de novato, pick, posición, nacimiento | — |
| nflverse `contracts` (OverTheCap) | Peso de cada jugador en el tope salarial por temporada | — |
| Wikipedia | Ganadores de los premios a Novato Ofensivo y Defensivo del Año (AP) | 2010 |

Se usa solo la temporada regular. Se excluyen intentos de dos puntos y jugadas abortadas. La temporada 2026 está en curso.

**Posición por temporada.** El catálogo de jugadores trae la posición más reciente; un WR que terminó como TE aparecería como TE en su año de
novato. Por eso la posición de cada temporada es la que más se repite en sus partidos según los snaps (desde 2013); antes se usa el catálogo.

**Participación.** Snaps propios sobre los snaps de su equipo en todos los partidos del calendario (no solo los que jugó), con el promedio de
la liga como denominador y recortada en 1.

## 2. Valor sobre reemplazo (ataque)

EPA (puntos esperados agregados) es cuánto cambia, en puntos, lo que se espera que anote el ataque antes y después de una jugada.

- **QB:** todas sus jugadas de pase (incluidos sacks y scrambles) con `qb_epa` (que no le carga los balones sueltos de sus receptores) y sus carreras diseñadas.
- **RB, WR, TE:** carreras y pases dirigidos a ellos.

**Nivel de reemplazo.** En cada temporada y posición se ordenan los jugadores por jugadas; los titulares de la liga son los primeros 32 QB,
48 RB, 96 WR y 48 TE. El nivel de reemplazo es el EPA por jugada de los demás (con al menos 20 jugadas). Valor = EPA − jugadas × reemplazo.

*Ejemplo:* un QB con 500 jugadas y +60 de EPA, en un año en que el reemplazo produce −0,06 por jugada, vale 60 − 500 × (−0,06) = 90 puntos.

**Robustez:** con 24/36/72/36 o 40/64/128/64 titulares el primero sigue siendo el mismo y el top 10 coincide en 10 y 8 de 10.

**EPA por jugada encogido.** Con pocas jugadas el promedio es ruido. Se encoge hacia la media de la posición con Bayes empírico: el peso es
n / (n + k), con k = varianza de una jugada / varianza real entre jugadores, ambas estimadas con los datos (`resultados/mejores.json`, campo `encogimiento`).

## 3. Defensa: jugadas destacadas

En cada jugada con EPA negativo para el ataque, ese EPA se reparte en partes iguales entre los defensores acreditados en sacks (enteros y medios),
intercepciones, pases defendidos en pases incompletos, balones forzados que el ataque perdió y tacleadas para pérdida.

## 4. Validación con los premios

Para cada temporada se ordena a los novatos por valor (ataque) o por EPA de jugadas destacadas (defensa) y se busca el puesto del ganador del
premio de la AP. Los nombres se comparan sin tildes, puntos ni sufijos.

## 5. Contratos

Valor sobre reemplazo (o temporadas de titular, participación recortada en 1) dividido entre el porcentaje del tope salarial, sumado por etapa:
novato, años 2 a 4 (todavía con contrato de novato para casi todos) y año 5 en adelante. Intervalos del 95 % por bootstrap con 1.000 réplicas
que remuestrean jugadores, porque un jugador aporta varias temporadas.

## 6. Predicción de carreras

**Objetivo:** titular establecido = al menos dos de los años 2 a 4 con participación de 50 % o más.
**Variables de draft:** log del pick (300 para no drafteados), si fue drafteado, edad y grupo de posición.
**Variables de la temporada de novato:** participación, partidos, valor sobre reemplazo por partido, EPA destacado por partido y si fue titular.

**Evaluación hacia adelante:** la clase *k* (2017 a 2022) se pronostica con un modelo entrenado solo con las clases hasta *k − 3*, porque al
terminar la temporada *k* solo esas clases tenían su resultado completo. Una prueba verifica que cambiar el resultado de las clases *k − 2* y
*k − 1* no cambia el pronóstico de *k*.

Modelos: logística con estandarización y gradient boosting. Métricas: AUC, Brier, log loss y calibración por deciles. La diferencia de AUC
tiene intervalo bootstrap.

## 7. Equipos

Panel de equipos 2013-2025 con la participación de novatos en los snaps. Regresiones de la diferencia de puntos por partido del mismo año y del
siguiente, con efectos fijos de equipo y de temporada, controlando por la diferencia previa, y errores agrupados por equipo.

## 8. Arquitectura y reproducibilidad

Python descarga, dbt transforma en DuckDB (22 pruebas: unicidad y rangos), Python analiza (pytest: 5 pruebas). Todo en Docker, corrido por
GitHub Actions cada martes. Los resultados son deterministas: consultas con orden explícito, semillas fijas y redondeo.
