# import balíčků
from dash import dcc, html
import dash_bootstrap_components as dbc
import sqlite3

# připojení k databázi
conn = sqlite3.connect("src/database/appDB.sqlite")
cur = conn.cursor()

# vyhledání názvů studií v databázi
cur.execute(f'SELECT DISTINCT nazev FROM studie_enum')

# převedení názvů studií do položek pro rozbalovací menu
options = [{'label': row[0], 'value': row[0]} for row in cur.fetchall()]
conn.close()


# rozbalovací menu pro výběr studie a její zobrazení v grafech
dropdown_study = html.Div(
    [dbc.Label("Choose study:"),
     dcc.Dropdown(id='dropdown_study',
                  options=options,
                  placeholder="Select")
     ]
)

# filtr pro zorbrazení pohlaví v grafech
m_f_checklist = html.Div([
    dbc.Label("Male/Female"),
    dbc.Checklist(id='m_f_checklist',
                  options=[{'label': 'Male', 'value': 'Male'},
                           {'label': 'Female', 'value': 'Female'}
                           ]
                  )
])

# filtr pro zobrazení věku v grafech
age_checklist = html.Div([
    dbc.Label("Age"),
    dbc.Checklist(id='age_checklist',
                  options=[{'label': 'Children', 'value': 'Children'},
                           {'label': 'AYAs', 'value': 'AYAs'},
                           {'label': 'Elderly', 'value': 'Elderly'}
                           ]
                  )
])

# karta s výběrem filtrů pro zobrazení grafů
study_card = dbc.Card([
    dbc.CardHeader('Graph filters'),
    dbc.CardBody([dropdown_study, m_f_checklist, age_checklist]
                 )
], className="p-2 bg-dark mb-3 bg-opacity-10")

# zobrazení grafu podle věku v době diagnózy

graph_yod_card = dbc.Card([
    dbc.CardHeader('Patients by the year of diagnosis and sex'),
    dbc.CardBody(dcc.Graph(id='diagnosis_age_graph')
                 )], className='p-2 mb-3')

# zobrazení grafu podle pohlaví pacienta
graph_gender_card = dbc.Card([
    dbc.CardHeader('Patients by sex'),
    dbc.CardBody(dcc.Graph(id='sex_graph')
                 )], className='p-2 mb-3')

# zobrazení grafu podle věku a pohlaví pacienta
graph_age_card = dbc.Card([
    dbc.CardHeader('Patients by age and sex'),
    dbc.CardBody(dcc.Graph(id='age_graph')
                 )], className='p-2 mb-3')

# zobrazení počtu mutací v jednotlivých genech v grafu
graph_mut_card = dbc.Card([
    dbc.CardHeader('Number of mutations in gene in study'),
    dbc.CardBody(dcc.Graph(id='mut_graph')
                 )], className='p-2 mb-3')

# zobrazení počtu mutací podle věkových kategorií v jednotlivých genech v grafu
graph_mut_age_card = dbc.Card([
    dbc.CardHeader('Number of mutations in gene'),
    dbc.CardBody(dcc.Graph(id='mut_graph1')
                 )], className='p-2 mb-3')


