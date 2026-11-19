# Novatos de la NFL desde 2010

¿Quién fue el mejor novato de la NFL desde 2010, cuánto valen los novatos para sus equipos y qué anticipa su primera temporada?
Este repositorio responde con datos públicos jugada a jugada, un pipeline reproducible y una app interactiva.

- **Artículo:** [nicolasforero.pages.dev/escritos/nfl-novatos](https://nicolasforero.pages.dev/escritos/nfl-novatos/)
- **App interactiva** (Shiny for Python): `app.py`, publicada en Posit Connect Cloud.
- **Método detallado:** [METODO.md](METODO.md)

## Lo que encontré

Las cifras salen de `resultados/*.json`, que el pipeline vuelve a calcular cada martes durante la temporada.

- **La mejor temporada de novato en ataque fue la de Robert Griffin III en 2012**, por valor sobre reemplazo (EPA producido por encima de un suplente típico). La siguen Dak Prescott (2016) y Russell Wilson (2012). El podio no cambia si el nivel de reemplazo se define con más o menos titulares.
- **Las métricas coinciden con los votantes:** en 9 de 16 temporadas el Novato Ofensivo del Año de la AP fue el n.º 1 de los datos, y en defensa 11 de 16 ganadores quedan entre los tres primeros.
- **El contrato de novato es una ganga:** un QB en sus años 2 a 4 produce cerca de 19 puntos de EPA sobre reemplazo por cada 1 % del tope salarial; un veterano, cerca de 7.
- **La temporada de novato dice más que el puesto en el draft:** para anticipar si un jugador será titular establecido, un modelo solo con lo que jugó de novato (AUC 0,87) supera a uno solo con el draft (0,84), y los dos juntos llegan a 0,89.
- **Los equipos que más juegan con novatos pierden más ese año**, pero eso no anticipa que mejoren el siguiente.

## Arquitectura

```
nflverse (releases de GitHub) ──> ingesta/descargar.py ──> data/raw (parquet, csv)
                                                               │
                         dbt + DuckDB: staging.* (jugadas, snaps, jugadores, contratos, posiciones)
                                       marts.*   (valor_ofensivo, valor_defensivo, participacion,
                                                  temporadas, carreras, equipos) + 22 pruebas
                                                               │
                         analisis/ (mejores, contratos, prediccion, equipos) ──> resultados/*.json, publicado/*.csv ──> app.py
```

Todo corre dentro de Docker (`Dockerfile`, `correr.sh`) en GitHub Actions (`.github/workflows/analisis.yml`), cada martes.

```bash
docker build -t nfl-novatos .
docker run --rm -v "$PWD/data:/app/data" -v "$PWD/resultados:/app/resultados" -v "$PWD/publicado:/app/publicado" nfl-novatos
shiny run app.py
```

## Lo que no hace

- No mide a la línea ofensiva jugada a jugada: para ella solo hay participación (snaps).
- La defensa solo se ve en jugadas destacadas (sacks, intercepciones, pases defendidos, balones forzados, tacleadas para pérdida); la cobertura que evita un pase no aparece.
- El EPA de un jugador depende de su sistema y sus compañeros: un receptor brilla más con un buen QB.
- Los snaps empiezan en 2013, así que la participación y el modelo de carreras usan las clases 2013 en adelante.
- Nada aquí es causal: el análisis de equipos muestra asociaciones.

## Datos y licencias

- [nflverse](https://github.com/nflverse/nflverse-data) (CC BY 4.0): jugada a jugada, snaps, draft, jugadores, contratos (de OverTheCap) y estadísticas avanzadas de PFR.
- Premios a novatos: [Wikipedia](https://en.wikipedia.org/wiki/AP_NFL_Offensive_Rookie_of_the_Year) (CC BY-SA 4.0), solo para validar.

Código bajo licencia MIT. José Nicolás Forero Urrego · [nicolasforero.pages.dev](https://nicolasforero.pages.dev)
