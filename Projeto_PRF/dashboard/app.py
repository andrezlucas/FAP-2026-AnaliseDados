"""Dashboard interativo dos acidentes registrados pela PRF."""

from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "dados_brutos"


def load_data() -> pd.DataFrame:
    """Carrega as bases disponíveis e padroniza as colunas usadas no painel."""
    frames = []
    for path in sorted(DATA_DIR.glob("acidentes*.csv")):
        frame = pd.read_csv(path, sep=";", encoding="latin1", low_memory=False)
        frame["ano"] = int(path.stem[-4:])
        frames.append(frame)

    if not frames:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {DATA_DIR}")

    accidents = pd.concat(frames, ignore_index=True)
    accidents["data_inversa"] = pd.to_datetime(
        accidents["data_inversa"], dayfirst=True, errors="coerce"
    )
    accidents["mes"] = accidents["data_inversa"].dt.month.fillna(0).astype(int)
    numeric_columns = [
        "mortos",
        "feridos",
        "feridos_graves",
        "latitude",
        "longitude",
    ]
    for column in numeric_columns:
        accidents[column] = pd.to_numeric(
            accidents[column].astype(str).str.replace(",", ".", regex=False),
            errors="coerce",
        ).fillna(0)
    accidents["acidente_fatal"] = accidents["mortos"].gt(0)
    accidents["uf"] = accidents["uf"].fillna("Não informado")
    accidents["causa_acidente"] = accidents["causa_acidente"].fillna(
        "Não informado"
    )
    accidents["tipo_acidente"] = accidents["tipo_acidente"].fillna(
        "Não informado"
    )
    return accidents


DATA = load_data()
YEARS = sorted(DATA["ano"].unique())
UFS = sorted(DATA["uf"].unique())


def metric_card(title: str, value_id: str) -> html.Div:
    return html.Div(
        [html.P(title, className="metric-title"), html.H2(id=value_id)],
        className="metric-card",
    )


app = Dash(__name__, title="Acidentes nas Rodovias Brasileiras")
app.layout = html.Div(
    [
        html.Header(
            [
                html.Div(
                    [
                        html.P("DADOS ABERTOS DA PRF", className="eyebrow"),
                        html.H1("ACIDENTES NAS RODOVIAS BRASILEIRAS"),
                        html.P(
                            "Indicadores e fatores associados aos acidentes "
                            "registrados pela Polícia Rodoviária Federal.",
                            className="subtitle",
                        ),
                    ],
                    className="header-content",
                )
            ],
            className="dashboard-header",
        ),
        html.Main(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Ano", htmlFor="year-filter"),
                                dcc.Dropdown(
                                    YEARS,
                                    YEARS,
                                    id="year-filter",
                                    multi=True,
                                    clearable=False,
                                ),
                            ],
                            className="filter",
                        ),
                        html.Div(
                            [
                                html.Label("UF", htmlFor="uf-filter"),
                                dcc.Dropdown(
                                    UFS,
                                    id="uf-filter",
                                    multi=True,
                                    placeholder="Todas as UFs",
                                ),
                            ],
                            className="filter",
                        ),
                    ],
                    className="filters",
                ),
                html.Div(
                    [
                        metric_card("TOTAL DE ACIDENTES", "accident-total"),
                        metric_card("TOTAL DE VÍTIMAS", "victim-total"),
                        metric_card("TOTAL DE MORTOS", "death-total"),
                        metric_card("ACIDENTES FATAIS", "fatal-total"),
                        metric_card("FERIDOS GRAVES", "serious-total"),
                    ],
                    className="metrics",
                ),
                html.Div(
                    [
                        html.Section(
                            [
                                html.H3("Classificação do acidente"),
                                dcc.Graph(
                                    id="classification-chart",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="panel",
                        ),
                        html.Section(
                            [
                                html.H3("Acidentes por tipo de causa"),
                                dcc.Graph(
                                    id="cause-chart",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="panel panel-wide",
                        ),
                    ],
                    className="chart-grid",
                ),
                html.Div(
                    [
                        html.Section(
                            [
                                html.H3("Acidentes por UF"),
                                dcc.Graph(
                                    id="uf-chart",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="panel",
                        ),
                        html.Section(
                            [
                                html.H3("Evolução mensal"),
                                dcc.Graph(
                                    id="monthly-chart",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="panel panel-wide",
                        ),
                    ],
                    className="chart-grid",
                ),
            ],
            className="content",
        ),
        html.Footer("Fonte: Dados Abertos da Polícia Rodoviária Federal"),
    ],
    className="app-shell",
)


def chart_layout(figure, height=360):
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 12, "r": 18, "t": 8, "b": 12},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Arial", "color": "#52606d"},
        hoverlabel={"bgcolor": "#17202a", "font_color": "#ffffff"},
    )
    return figure


@app.callback(
    Output("accident-total", "children"),
    Output("victim-total", "children"),
    Output("death-total", "children"),
    Output("fatal-total", "children"),
    Output("serious-total", "children"),
    Output("classification-chart", "figure"),
    Output("cause-chart", "figure"),
    Output("uf-chart", "figure"),
    Output("monthly-chart", "figure"),
    Input("year-filter", "value"),
    Input("uf-filter", "value"),
)
def update_dashboard(selected_years, selected_ufs):
    filtered = DATA[DATA["ano"].isin(selected_years or YEARS)]
    if selected_ufs:
        filtered = filtered[filtered["uf"].isin(selected_ufs)]

    classification = (
        filtered["classificacao_acidente"]
        .fillna("Não informado")
        .value_counts()
        .head(12)
        .sort_values()
        .reset_index()
    )
    classification.columns = ["classificacao", "acidentes"]
    classification_figure = px.bar(
        classification,
        x="acidentes",
        y="classificacao",
        orientation="h",
        text="acidentes",
        color_discrete_sequence=["#f2c500"],
    )
    classification_figure.update_traces(textposition="outside")

    causes = (
        filtered["causa_acidente"]
        .value_counts()
        .head(15)
        .sort_values()
        .reset_index()
    )
    causes.columns = ["causa", "acidentes"]
    cause_figure = px.bar(
        causes,
        x="acidentes",
        y="causa",
        orientation="h",
        text="acidentes",
        color_discrete_sequence=["#1683d8"],
    )
    cause_figure.update_traces(textposition="outside")

    by_uf = (
        filtered.groupby("uf", as_index=False)
        .agg(
            acidentes=("id", "size"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
        )
        .sort_values("acidentes", ascending=False)
    )
    uf_figure = px.bar(
        by_uf.sort_values("acidentes"),
        x="acidentes",
        y="uf",
        orientation="h",
        text="acidentes",
        color_discrete_sequence=["#f2c500"],
    )
    uf_figure.update_traces(textposition="outside")

    monthly = (
        filtered.groupby(["ano", "mes"], as_index=False)
        .size()
        .rename(columns={"size": "acidentes"})
    )
    monthly["periodo"] = (
        monthly["ano"].astype(str)
        + "-"
        + monthly["mes"].astype(int).astype(str).str.zfill(2)
    )
    monthly_figure = px.line(
        monthly,
        x="periodo",
        y="acidentes",
        markers=True,
        color="ano",
        labels={"periodo": "Período", "acidentes": "Acidentes", "ano": "Ano"},
        color_discrete_sequence=["#1683d8", "#e4b900"],
    )

    return (
        f"{len(filtered):,}".replace(",", "."),
        f"{int(filtered[['feridos', 'mortos']].sum().sum()):,}".replace(",", "."),
        f"{int(filtered['mortos'].sum()):,}".replace(",", "."),
        f"{int(filtered['acidente_fatal'].sum()):,}".replace(",", "."),
        f"{int(filtered['feridos_graves'].sum()):,}".replace(",", "."),
        chart_layout(classification_figure),
        chart_layout(cause_figure, 420),
        chart_layout(uf_figure),
        chart_layout(monthly_figure),
    )


server = app.server


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
