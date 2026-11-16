import base64
import flet as ft
import plotly.graph_objects as go


def main(page: ft.Page):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=25,
            gauge={"axis": {"range": [0, 100]}}
        )
    )

    svg = fig.to_image(format="svg").decode("utf-8")

    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")

    page.add(
        ft.Image(
            src_base64=encoded,
            width=500,
            height=350,
            fit=ft.BoxFit.CONTAIN,
        )
    )


ft.run(main)