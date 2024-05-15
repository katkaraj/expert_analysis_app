# import balíčků
from dash import html, dcc
import dash_bootstrap_components as dbc

# komponenta pro nahrání reportu
uploader = html.Div([
    dcc.Upload(id="upload-data",
               children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
               style={'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center',
                      'margin': '10px'},
               multiple=True, ), ])

# vytvoření karty pro nahrání reportu
upload_card = dbc.Card([
    dbc.Label('Upload report: '),
    dbc.Row(uploader),
    dbc.Row(html.Div(id='upload_label')),
], body=True, className="p-2 bg-dark mb-3 bg-opacity-10", style={"height": "150px"})
