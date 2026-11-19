"""Novatos de la NFL desde 2010: quién fue el mejor, cuánto valen y qué anticipa su primera temporada.

App en Shiny for Python. Lee los resultados del pipeline (nflverse → DuckDB + dbt → Python) de este repositorio.
José Nicolás Forero Urrego · https://nicolasforero.pages.dev
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_plotly

AQUI = Path(__file__).parent
R = {f.stem: json.load(open(f, encoding="utf-8")) for f in (AQUI / "resultados").glob("*.json")}
T = pd.read_csv(AQUI / "publicado" / "temporadas.csv")
EQ = pd.read_csv(AQUI / "publicado" / "equipos.csv")
PR = pd.read_csv(AQUI / "publicado" / "pronosticos.csv")
M, CO, P, E = R["mejores"], R["contratos"], R["prediccion"], R["equipos"]
NOV = T[T.anio_carrera == 1].copy()
AZUL, ROSA, MENTA, AMBAR, LAVANDA, TINTA, GRIS = "#4F6BD8", "#EBA3B0", "#8CCFB8", "#F5B482", "#B9A7E8", "#1F2430", "#C9CED6"
COL_GRUPO = {"QB": AZUL, "RB": AMBAR, "WR": MENTA, "TE": LAVANDA, "OL": GRIS, "DL": ROSA, "LB": "#7C93E8", "DB": "#F2C46D"}
ETAPAS = ["Novato", "Años 2 a 4", "Año 5 en adelante"]
COL_ETAPA = dict(zip(ETAPAS, [ROSA, AZUL, GRIS]))
ULTIMA = 2025


def num(x, d=1):
    if x is None or x != x:
        return "–"
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x, d=0):
    return "–" if x is None or x != x else num(100 * x, d) + " %"


def figura(fig, alto=380):
    fig.update_layout(height=alto, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, system-ui", color=TINTA, size=12), legend=dict(orientation="h", y=-0.2),
                      hoverlabel=dict(bgcolor="white"), separators=",.",
                      modebar=dict(bgcolor="rgba(0,0,0,0)", color="#9CA3AF", activecolor=TINTA))
    fig.update_xaxes(gridcolor="#ECE8E0", zeroline=False)
    fig.update_yaxes(gridcolor="#ECE8E0", zeroline=False)
    return fig


def tabla(df, cols, fmts):
    cab = "".join(f"<th class='{'n' if c in fmts else ''}'>{t}</th>" for c, t in cols)
    filas = "".join("<tr>" + "".join(f"<td class='{'n' if c in fmts else ''}'>{fmts[c](r[c]) if c in fmts else r[c]}</td>" for c, _ in cols) + "</tr>"
                    for _, r in df.iterrows())
    return ui.HTML(f"<div style='overflow-x:auto'><table class='tabla'><thead><tr>{cab}</tr></thead><tbody>{filas}</tbody></table></div>")


def pick(x):
    return "No drafteado" if x is None or x != x or x >= 300 else str(int(x))


CSS = """
:root { --bs-body-bg: #F6F4EF; --bs-body-color: #1F2430; --bs-primary: #4F6BD8; --bs-border-color: #ECE8E0;
        --bs-body-font-family: Inter, system-ui, -apple-system, 'Segoe UI', sans-serif; }
body { background: #F6F4EF; } .navbar { background: #F6F4EF !important; border-bottom: 1px solid #ECE8E0; }
.navbar-brand { font-family: Georgia, serif; font-size: 1.3rem; }
.card { border: 1px solid #ECE8E0; box-shadow: none; border-radius: 14px; }
.card-header { background: transparent; font-weight: 600; border-bottom: 1px solid #ECE8E0; }
.bslib-value-box { border: 1px solid #ECE8E0 !important; border-radius: 14px; }
.bslib-value-box .value-box-title { color: #6B7280; font-size: .85rem; } .bslib-value-box .value-box-value { font-family: Georgia, serif; font-size: 1.8rem; }
.lead { font-size: 1.05rem; max-width: 62rem; color: #374151; } .nota { color: #6B7280; font-size: .85rem; }
table.tabla { width: 100%; font-size: .9rem; } table.tabla td, table.tabla th { padding: .38rem .5rem; border-bottom: 1px solid #ECE8E0; white-space: nowrap; }
table.tabla th { color: #6B7280; font-weight: 600; font-size: .8rem; } table.tabla td.n, table.tabla th.n { text-align: right; font-variant-numeric: tabular-nums; }
footer.pie { color: #6B7280; font-size: .8rem; margin: 1.5rem 0 1rem; }
"""
pie = ui.tags.footer({"class": "pie"}, "Datos: nflverse (CC BY 4.0), que reúne jugadas, snaps, draft y contratos (OverTheCap); premios: Wikipedia (CC BY-SA 4.0). ",
                     "Código: ", ui.a("github.com/Forero25/nfl-novatos", href="https://github.com/Forero25/nfl-novatos"), " · ",
                     ui.a("José Nicolás Forero Urrego", href="https://nicolasforero.pages.dev"))


def tarjeta(t, *c, **kw):
    return ui.card(ui.card_header(t), *c, **kw)


top = M["ofensivos"][0]
met = {m["modelo"]: m for m in P["metricas"]}
qb_eta = {(r["grupo"], r["etapa"]): r for r in CO["valor"]}
c26 = M["clase_2026"]
app_ui = ui.page_navbar(
    ui.nav_panel("Mejores novatos",
        ui.p({"class": "lead mt-3"}, "El valor sobre reemplazo mide cuánto EPA (puntos esperados agregados) produjo un jugador por encima de lo que habría dado "
             "un suplente típico de su posición en las mismas jugadas. En ataque se calcula jugada a jugada; en defensa se cuentan las jugadas destacadas "
             "(sacks, intercepciones, pases defendidos, balones forzados y tacleadas para pérdida)."),
        ui.layout_columns(
            ui.value_box("Mejor temporada de novato en ataque", f"{top['nombre']} ({top['temporada']})", f"{num(top['valor_reemplazo'])} puntos sobre reemplazo"),
            ui.value_box("El ganador del premio ofensivo es el n.º 1 de los datos", f"{M['validacion']['ofensivo']['primero']} de {M['validacion']['ofensivo']['n']}", "temporadas, 2010-2025"),
            ui.value_box("En defensa", f"{M['validacion']['defensivo']['top3']} de {M['validacion']['defensivo']['n']}", "ganadores quedan entre los 3 primeros"),
            fill=False),
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_radio_buttons("lado", "Lado", {"ataque": "Ataque", "defensa": "Defensa"}, selected="ataque"),
                ui.input_checkbox_group("grupos", "Posiciones", ["QB", "RB", "WR", "TE", "DL", "LB", "DB"], selected=["QB", "RB", "WR", "TE", "DL", "LB", "DB"]),
                ui.input_slider("anios", "Temporadas", 2010, ULTIMA, (2010, ULTIMA), sep=""),
                ui.input_numeric("n", "Cuántos mostrar", 20, min=5, max=60),
                width=260),
            tarjeta("Ranking de temporadas de novato", output_widget("g_mejores")),
            tarjeta("Detalle", ui.output_ui("t_mejores"))),
    ),
    ui.nav_panel("Clase 2026",
        ui.p({"class": "lead mt-3"}, f"La temporada 2026 va por la semana {c26['partidos_jugados']}. El ritmo proyecta el valor de cada novato a 17 partidos, "
             "si siguiera produciendo igual. Se actualiza cada martes."),
        ui.layout_columns(
            tarjeta("Ataque: valor sobre reemplazo", ui.output_ui("t_26_of")),
            tarjeta("Defensa: EPA de jugadas destacadas", ui.output_ui("t_26_de"))),
    ),
    ui.nav_panel("El contrato de novato",
        ui.p({"class": "lead mt-3"}, "Desde el convenio colectivo de 2011 el salario de los novatos sigue una escala fija según el pick. "
             "¿Cuánto rinde cada 1 % del tope salarial según la etapa de la carrera? Intervalos del 95 % por bootstrap, remuestreando jugadores."),
        ui.layout_columns(
            ui.value_box("QB en años 2 a 4: valor por cada 1 % del cap", num(qb_eta[("QB", "Años 2 a 4")]["valor_por_pct"]), "puntos de EPA sobre reemplazo"),
            ui.value_box("QB veterano (año 5+)", num(qb_eta[("QB", "Año 5 en adelante")]["valor_por_pct"]), "puntos por cada 1 % del cap"),
            ui.value_box("Ejemplo", "Mahomes 2018", f"{num(CO['ejemplos_qb'][1]['valor_reemplazo'])} puntos con {num(CO['ejemplos_qb'][1]['pct'])} % del cap"),
            fill=False),
        ui.layout_columns(
            tarjeta("Ataque: EPA sobre reemplazo por cada 1 % del cap", output_widget("g_valor")),
            tarjeta("Todas las posiciones: temporadas de titular por cada 1 % del cap", output_widget("g_snaps"))),
    ),
    ui.nav_panel("¿Será titular?",
        ui.p({"class": "lead mt-3"}, "¿Qué anticipa mejor si un novato será titular establecido (50 % o más de los snaps en al menos dos de sus años 2 a 4): "
             "su puesto en el draft o lo que jugó de novato? Evaluación hacia adelante: cada clase se pronostica solo con clases cuyo resultado ya se conocía."),
        ui.layout_columns(
            ui.value_box("AUC solo con el draft", num(met["Solo draft (logística)"]["auc"], 3), "1 = perfecto, 0,5 = azar"),
            ui.value_box("AUC con draft y temporada de novato", num(met["Draft + novato (logística)"]["auc"], 3),
                         f"mejora de {num(P['dif_auc_novato_vs_draft']['dif'], 3)} (IC {num(P['dif_auc_novato_vs_draft']['ic_bajo'], 3)} a {num(P['dif_auc_novato_vs_draft']['ic_alto'], 3)})"),
            ui.value_box("AUC solo con la temporada de novato", num(met["Solo novato (logística)"]["auc"], 3), "sin saber el pick"),
            fill=False),
        ui.layout_columns(
            tarjeta("Probabilidad según pick y participación de novato", ui.input_select("g_eq", None, {"WR": "WR", "OL": "Línea ofensiva", "DB": "Secundaria"}), output_widget("g_equiv")),
            tarjeta("Calibración: lo que dijo el modelo y lo que pasó", output_widget("g_calib"))),
        tarjeta("Pronóstico para las clases 2023-2025",
            ui.layout_columns(ui.input_select("clase", "Clase", ["2025", "2024", "2023"]),
                              ui.input_select("g_pr", "Posición", ["Todas", "QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB"]), fill=False),
            ui.output_ui("t_pron")),
    ),
    ui.nav_panel("Equipos",
        ui.p({"class": "lead mt-3"}, "Los equipos que más juegan con novatos pierden más ese año (son los que se están reconstruyendo y tenían picks altos), "
             "pero eso no anticipa que mejoren al año siguiente."),
        ui.layout_columns(
            tarjeta("Participación de novatos y diferencia de puntos por partido", ui.input_slider("t_eq", "Temporada", 2013, ULTIMA, ULTIMA, sep=""), output_widget("g_equipos")),
            tarjeta("Snaps de novatos en la liga y partidos con QB novato titular", output_widget("g_liga"))),
    ),
    ui.nav_panel("Método",
        ui.div({"class": "mt-3", "style": "max-width: 62rem"},
            ui.markdown("""
**Datos.** Jugada a jugada de nflverse (temporada regular, 2010-2026), snaps por partido (desde 2013), draft, catálogo de jugadores
y contratos de OverTheCap. Todo es público (CC BY 4.0). Los premios a novatos salen de Wikipedia y solo se usan para validar.

**Valor sobre reemplazo (ataque).** Para cada jugador se suma el EPA de sus jugadas: los QB, todos sus pases (con sacks y scrambles) y sus carreras
diseñadas; los RB, WR y TE, sus carreras y los pases dirigidos a ellos. El nivel de reemplazo es el EPA por jugada de quienes quedan por fuera
de los titulares de la liga en esa temporada (32 QB, 48 RB, 96 WR y 48 TE). El valor es EPA − jugadas × reemplazo.

**Defensa.** El EPA de cada jugada negativa para el ataque se reparte entre los defensores acreditados en sacks, intercepciones, pases defendidos,
balones forzados y tacleadas para pérdida. Mide jugadas destacadas, no la cobertura ni el trabajo que no queda en la planilla.

**Contratos.** Se divide el valor (o las temporadas de titular) entre el porcentaje del tope salarial que costó el jugador.

**Predicción.** Regresión logística y gradient boosting. Para la clase *k* se entrena con las clases hasta *k − 3*, que eran las únicas con
resultado conocido al terminar la temporada *k*.

**Arquitectura.** Python baja los datos, dbt los transforma en DuckDB con pruebas, Python hace el análisis, todo dentro de Docker;
GitHub Actions lo corre cada martes. Código en [GitHub](https://github.com/Forero25/nfl-novatos).

**Lo que no hace.** No mide a la línea ofensiva por jugada; la defensa solo se ve en jugadas destacadas; el valor depende del
sistema y de los compañeros; no es causal.
"""))),
    title="Novatos de la NFL", header=ui.tags.style(CSS), footer=pie, fillable=False, lang="es",
)


def server(input, output, session):
    @reactive.calc
    def mejores():
        d = NOV[NOV.temporada.between(*input.anios()) & NOV.grupo.isin(input.grupos())]
        col = "valor_reemplazo" if input.lado() == "ataque" else "epa_destacado"
        lado = ["QB", "RB", "WR", "TE"] if input.lado() == "ataque" else ["DL", "LB", "DB"]
        d = d[d.grupo.isin(lado) & d[col].notna()].nlargest(int(input.n() or 20), col)
        return d.assign(valor=d[col], etiqueta=d.nombre + " (" + d.temporada.astype(str) + ")")

    @render_plotly
    def g_mejores():
        d = mejores().iloc[::-1]
        fig = go.Figure(go.Bar(x=d.valor, y=d.etiqueta, orientation="h", marker_color=[COL_GRUPO.get(g, GRIS) for g in d.grupo],
                               hovertemplate="%{y}<br>%{x:,.1f}<extra></extra>"))
        fig.update_xaxes(title="Valor sobre reemplazo (EPA)" if input.lado() == "ataque" else "EPA de jugadas destacadas")
        return figura(fig, alto=max(360, 22 * len(d)))

    @render.ui
    def t_mejores():
        d = mejores()
        cols = [("temporada", "Temporada"), ("nombre", "Jugador"), ("posicion", "Pos."), ("equipo", "Equipo"), ("pick", "Pick"),
                ("participacion", "Snaps"), ("valor", "Valor")]
        return tabla(d.assign(equipo=d.equipo.fillna("–")), cols, {"temporada": str, "pick": pick, "participacion": pct, "valor": num})

    @render.ui
    def t_26_of():
        d = pd.DataFrame(c26["ofensivos"])
        return tabla(d, [("nombre", "Jugador"), ("posicion", "Pos."), ("equipo", "Equipo"), ("pick", "Pick"), ("valor_reemplazo", "Valor"), ("ritmo_17", "Ritmo a 17")],
                     {"pick": pick, "valor_reemplazo": num, "ritmo_17": num})

    @render.ui
    def t_26_de():
        d = pd.DataFrame(c26["defensivos"])
        return tabla(d, [("nombre", "Jugador"), ("posicion", "Pos."), ("equipo", "Equipo"), ("pick", "Pick"), ("epa_destacado", "EPA"), ("ritmo_17", "Ritmo a 17")],
                     {"pick": pick, "epa_destacado": num, "ritmo_17": num})

    def barras_etapa(d, col, titulo):
        fig = go.Figure()
        for e in ETAPAS:
            x = d[d.etapa == e]
            fig.add_bar(name=e, x=x.grupo, y=x[col], marker_color=COL_ETAPA[e],
                        error_y=dict(type="data", symmetric=False, array=x.ic_alto - x[col], arrayminus=x[col] - x.ic_bajo, color="#9CA3AF"))
        fig.update_layout(barmode="group"); fig.update_yaxes(title=titulo)
        return figura(fig)

    @render_plotly
    def g_valor():
        return barras_etapa(pd.DataFrame(CO["valor"]), "valor_por_pct", "EPA sobre reemplazo por 1 % del cap")

    @render_plotly
    def g_snaps():
        d = pd.DataFrame(CO["snaps"])
        d["grupo"] = pd.Categorical(d.grupo, ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB"]); d = d.sort_values("grupo")
        return barras_etapa(d, "titular_por_pct", "Temporadas de titular por 1 % del cap")

    @render_plotly
    def g_equiv():
        d = pd.DataFrame(P["equivalencia"]); d = d[d.grupo == input.g_eq()]
        fig = go.Figure()
        for p_, c in zip([0.1, 0.4, 0.7], [GRIS, AZUL, ROSA]):
            x = d[d.participacion == p_]
            fig.add_scatter(x=x.pick, y=x.prob, mode="lines+markers", name=f"Jugó {pct(p_)} de los snaps", line=dict(color=c, width=3))
        fig.update_xaxes(title="Pick del draft", type="log", tickvals=[10, 32, 64, 100, 150, 220], ticktext=["10", "32", "64", "100", "150", "220"]); fig.update_yaxes(title="Probabilidad de ser titular", tickformat=".0%", range=[0, 1])
        return figura(fig)

    @render_plotly
    def g_calib():
        d = pd.DataFrame(P["calibracion"])
        fig = go.Figure()
        fig.add_scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=GRIS, dash="dot"), showlegend=False, hoverinfo="skip")
        fig.add_scatter(x=d.predicho, y=d.observado, mode="markers+lines", marker=dict(size=9, color=AZUL), line=dict(color=AZUL), name="Deciles",
                        hovertemplate="Predicho %{x:.0%}<br>Observado %{y:.0%}<extra></extra>")
        fig.update_xaxes(title="Probabilidad pronosticada", tickformat=".0%"); fig.update_yaxes(title="Proporción que fue titular", tickformat=".0%")
        return figura(fig)

    @render.ui
    def t_pron():
        d = PR[PR.temporada == int(input.clase())]
        if input.g_pr() != "Todas":
            d = d[d.grupo == input.g_pr()]
        d = d.nlargest(25, "prob")
        return tabla(d, [("nombre", "Jugador"), ("grupo", "Pos."), ("pick_ef", "Pick"), ("participacion", "Snaps de novato"), ("prob", "Prob. titular")],
                     {"pick_ef": pick, "participacion": pct, "prob": pct})

    @render_plotly
    def g_equipos():
        d = EQ[EQ.temporada == input.t_eq()].dropna(subset=["part_novatos"])
        fig = go.Figure(go.Scatter(x=d.part_novatos, y=d.dif_por_partido, mode="markers+text", text=d.equipo, textposition="top center",
                                   marker=dict(size=10, color=AZUL, opacity=.75), textfont=dict(size=10, color="#6B7280"),
                                   hovertemplate="%{text}<br>Novatos: %{x:.0%}<br>Diferencia: %{y:,.1f}<extra></extra>"))
        fig.update_xaxes(title="Snaps jugados por novatos", tickformat=".0%"); fig.update_yaxes(title="Diferencia de puntos por partido")
        return figura(fig)

    @render_plotly
    def g_liga():
        l = pd.DataFrame(E["panorama"]["liga"]); q = pd.DataFrame(E["panorama"]["qb_titular"])
        fig = go.Figure()
        fig.add_scatter(x=l.temporada, y=l.ataque, name="Snaps de ataque", line=dict(color=AZUL, width=3))
        fig.add_scatter(x=l.temporada, y=l.defensa, name="Snaps de defensa", line=dict(color=ROSA, width=3))
        fig.add_bar(x=q.temporada, y=q.pct, name="Partidos con QB novato titular", marker_color=AMBAR, opacity=.6)
        fig.update_yaxes(tickformat=".0%"); fig.update_xaxes(dtick=1)
        return figura(fig)


app = App(app_ui, server)
