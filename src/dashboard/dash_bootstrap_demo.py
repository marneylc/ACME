"""
Dash port of Shiny iris k-means example:

https://shiny.rstudio.com/gallery/kmeans-example.html
"""
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
# from sklearn import datasets
from sklearn.cluster import KMeans
# from pathlib import Path


def demo(datas:dict):
    # iris_raw = datasets.load_iris()
    # iris = pd.DataFrame(iris_raw["data"], columns=iris_raw["feature_names"])
    app = dash.Dash(__name__)
    # app.css.config.serve_locally = False

    controls = dbc.Card(
        [
            dbc.FormGroup(
                [
                    dbc.Label("Data source"),
                    dcc.Dropdown(
                        id="data-source",
                        options=[
                            {"label": col, "value": col} for col in datas
                        ],
                        value="All Documents",
                    ),
                ]
            ),
            dbc.FormGroup(
                [
                    dbc.Label("Normalize word counts to range [0, 1]"),
                    dcc.RadioItems(
                        id="is-normalized",
                        options=[{"label":"True","value":"t"},
                                 {"label":"False","value":"f"},],
                        value='False'
                    )
                    # dcc.Dropdown(
                    #     id="is-normalized",
                    #     options=[
                    #         {"label": col, "value": col} for col in ("")
                    #     ],
                    #     value="sepal width (cm)",
                    # ),
                ]
            ),
            # dbc.FormGroup(
            #     [
            #         dbc.Label("Cluster count"),
            #         dbc.Input(id="cluster-count", type="number", value=3),
            #     ]
            # ),
        ],
        body=True,
    )

    app.layout = dbc.Container(
        [
            html.H1("Iris k-means clustering"),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(controls, md=4),
                    dbc.Col(dcc.Graph(id="count-graph"), md=8),
                ],
                align="center",
            ),
        ],
        fluid=True,
    )


    @app.callback(
        Output("count-graph", "figure"),
        [
            Input("data-source", "value"),
            Input("is-normalized", "value"),
            # Input("cluster-count", "value"),
        ],
    )
    def make_graph(x, y):
        nonlocal datas
        # minimal input validation, make sure there's at least one cluster
        df = datas[x][y]

        # data = [
        #     go.Scatter(
        #         x=df.loc[df.cluster == c, x],
        #         y=df.loc[df.cluster == c, y],
        #         mode="markers",
        #         marker={"size": 8},
        #         name="Cluster {}".format(c),
        #     )
        #     for c in range(n_clusters)
        # ]
        #
        # data.append(
        #     go.Scatter(
        #         x=centers[:, 0],
        #         y=centers[:, 1],
        #         mode="markers",
        #         marker={"color": "#000", "size": 12, "symbol": "diamond"},
        #         name="Cluster centers",
        #     )
        # )

        layout = {"xaxis": {"title": x}, "yaxis": {"title": y}}
        data = []

        return go.Figure(data=data, layout=layout)


    # make sure that x and y values can't be the same variable
    def filter_options(v):
        """Disable option v"""
        return [
            {"label": col, "value": col, "disabled": col == v}
            for col in iris.columns
        ]


    # functionality is the same for both dropdowns, so we reuse filter_options
    app.callback(Output("x-variable", "options"), [Input("y-variable", "value")])(
        filter_options
    )
    app.callback(Output("y-variable", "options"), [Input("x-variable", "value")])(
        filter_options
    )

    app.run_server(debug=True, port=8888)


if __name__ == "__main__":
    demo()