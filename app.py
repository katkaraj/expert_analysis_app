# import balíčků
import dash
import dash_bootstrap_components as dbc

# import komponent aplikace
from src.components.layout_components import header, footer
from src.components.upload_components import upload_card
from src.components.search_components import search_card, search_output
from src.components.graph_components import (study_card, graph_gender_card, graph_mut_card, graph_mut_age_card,
                                             graph_yod_card, graph_age_card)

# import funkcí
from src.callbacks.graph_functions import graph_callbacks
from src.callbacks.upload_functions import upload_callbacks
from src.callbacks.search_functions import search_callbacks

# inicializace aplikace
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])
app = app.server

app.layout = dbc.Container([
    dbc.Row(header),
    dbc.Row([dbc.Col(upload_card), dbc.Col(search_card)]),
    dbc.Row(search_output),
    dbc.Row(study_card),
    dbc.Row([dbc.Col(graph_gender_card), dbc.Col(graph_yod_card)]),
    dbc.Row([dbc.Col(graph_age_card), dbc.Col(graph_mut_card)]),
    dbc.Row(graph_mut_age_card),
    dbc.Row(footer),
])

graph_callbacks(app)
upload_callbacks(app)
search_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
