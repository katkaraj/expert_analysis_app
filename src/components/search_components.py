# import balíčků
from dash import html, dcc
import dash_bootstrap_components as dbc

# pole pro vyhledávání reportu v databázi podle kódu reportu
search_input = dbc.Input(
    id='report_input',
    placeholder='The report number',
    type='text')

# tlačítko pro otevření reportu v aplikaci
search_button = dbc.Button(
    'Open',
    id='open_button',
    n_clicks=0)

# vytvoření karty pro vyhledávání reportu v databázi a otevření v aplikaci
search_card = dbc.Card([
    dbc.Label("Search report: "),
    dbc.Row([
        dbc.Col(search_input),
        dbc.Col(search_button)]),
    dbc.Row(html.Div(id='search_ex_alert'))], body=True, className="p-2 bg-dark mb-3 bg-opacity-10", style={"height":"150px"})

# karta pro zobrazení vyhledaného reportu
initial_tabs = []
search_output = dbc.Card([
    dbc.CardHeader("Variant classification:"),
    dbc.CardBody([dcc.Loading
                  (children=[dbc.Tabs(initial_tabs, id="tabs", active_tab='tab-1' if initial_tabs else None)]
                   , fullscreen=False, type='circle'), html.P(id='tabs_content')]), ], className='p-2 mb-3')
