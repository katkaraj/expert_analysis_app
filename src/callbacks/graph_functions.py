# import balíčků
from dash import dcc, Input, Output
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# funkce pro vytvoření jednotlivých gafů
def graph_callbacks(app):
    # zobrazení grafu podle data diagnózy
    @app.callback(
        Output('diagnosis_age_graph', 'figure'),
        Input('dropdown_study', 'value'),
        Input('m_f_checklist', 'value'),
        Input('age_checklist', 'value')
    )
    def update_graph_yod(study, sex, age):
        conn = sqlite3.connect('src/database/appDB.sqlite')
        query = f"""
            SELECT p.idpacient, p.diagnoza,
                CASE
                    WHEN substr(p.diagnoza, -4)  <= '2005' THEN 'Before 2005'
                    WHEN substr(p.diagnoza, -4) BETWEEN '2006' AND '2010' THEN '2006 - 2010'
                    WHEN substr(p.diagnoza, -4) BETWEEN '2011' AND '2015' THEN '2011 - 2015'
                    WHEN substr(p.diagnoza, -4) BETWEEN '2016' AND '2020' THEN '2016 - 2020'
                    ELSE 'After 2021'
                END AS Date,
                CASE
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4)  <= 17 THEN 'Children'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 18 AND 39 THEN 'AYAs'
                    ELSE 'Elderly'
                END AS Age_Check,
                CASE 
                    WHEN substr(p.rc, 3, 1) IN ('5', '6') THEN 'Female'
                    ELSE  'Male'
                END AS Sex
             FROM pacient p
             INNER JOIN studie s ON p.idpacient = s.pacient_idpacient
             INNER JOIN studie_enum se ON s.studie_enum_idstudie = se.idstudie
             WHERE se.nazev = '{study}'

    """
        df_new = pd.read_sql(query, conn)
        conn.close()

        if sex:
            df_new = df_new[df_new['Sex'].isin(sex)]
        if age:
            df_new = df_new[df_new['Age_Check'].isin(age)]

        patients_count = df_new.groupby(['Date', 'Sex']).size().reset_index(name='Number of Patients')

        fig = px.bar(patients_count, x='Number of Patients', y='Date', color='Sex',
                     title=f'The year of diagnosis in {study}',
                     color_discrete_map={'Female': 'FireBrick', 'Male': 'DodgerBlue'})
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color="black"))
        fig.update_yaxes(categoryorder='array',
                         categoryarray=['Before 2005', '2006 - 2010', '2011 - 2015', '2016 - 2020', 'After 2021'])

        return fig

    # zobrazení grafu podle pohlaví
    @app.callback(
        Output('sex_graph', 'figure'),
        Input('dropdown_study', 'value'),
        Input('m_f_checklist', 'value'),
        Input('age_checklist', 'value'),
    )
    def update_graph_sex(study, sex, age):
        conn = sqlite3.connect('src/database/appDB.sqlite')
        query = f"""
            SELECT p.idpacient,
                CASE 
                    WHEN substr(p.rc, 3, 1) IN ('5', '6') THEN 'Female'
                    ELSE  'Male'
                END AS Sex,
                CASE
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4)  <= 17 THEN 'Children'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 18 AND 39 THEN 'AYAs'
                    ELSE 'Elderly'
                END AS Age_Check
             FROM pacient p
             INNER JOIN studie s ON p.idpacient = s.pacient_idpacient
             INNER JOIN studie_enum se ON s.studie_enum_idstudie = se.idstudie
             WHERE se.nazev = '{study}'   
        """
        df_new = pd.read_sql(query, conn)
        conn.close()

        if sex:
            df_new = df_new[df_new['Sex'].isin(sex)]
        if age:
            df_new = df_new[df_new['Age_Check'].isin(age)]

        df_counts = df_new['Sex'].value_counts().reset_index()
        df_counts.columns = ['Sex', 'Number of Patients']

        figg = go.Figure(data=[go.Pie(labels=df_counts['Sex'],
                                      values=df_counts['Number of Patients'],
                                      hoverinfo='text',
                                      textinfo='value+percent',
                                      marker=dict(colors=['DodgerBlue', 'FireBrick']))])
        figg.update_layout(title_text="Number of patients by sex")
        return figg

    # zobrazení grafu podle věku
    @app.callback(
        Output('age_graph', 'figure'),
        Input('dropdown_study', 'value'),
        Input('m_f_checklist', 'value'),
        Input('age_checklist', 'value')
    )
    def upgrade_graph_age(study, sex, age):
        conn = sqlite3.connect('src/database/appDB.sqlite')
        query = f"""
            SELECT p.narozen, 
                CASE
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4)  <= 4 THEN '0-4'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 5 AND 9 THEN '5-9'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 10 AND 14 THEN '10-14'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 15 AND 24 THEN '15-24'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 25 AND 40 THEN '25-40'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 41 AND 54 THEN '41-54'
                    ELSE '55+'
                END AS Age,
                CASE
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4)  <= 17 THEN 'Children'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 18 AND 39 THEN 'AYAs'
                    ELSE 'Elderly'
                END AS Age_Check,
                CASE 
                    WHEN substr(p.rc, 3, 1) IN ('5', '6') THEN 'Female'
                    ELSE  'Male'
                END AS Sex
             FROM pacient p
             INNER JOIN studie s ON p.idpacient = s.pacient_idpacient
             INNER JOIN studie_enum se ON s.studie_enum_idstudie = se.idstudie
             WHERE se.nazev = '{study}'
        """
        df_new = pd.read_sql(query, conn)
        conn.close()

        if sex:
            df_new = df_new[df_new['Sex'].isin(sex)]
        if age:
            df_new = df_new[df_new['Age_Check'].isin(age)]

        patient_count = df_new.groupby(['Age', 'Sex']).size().reset_index(name='Number of Patients')
        fig = px.bar(patient_count, x='Age', y='Number of Patients', color='Sex',
                     title=f'Number of patients by age in {study}', color_discrete_map={'Female': 'FireBrick',
                                                                                        'Male': 'DodgerBlue'})
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color="black"))
        fig.update_xaxes(categoryorder='array', categoryarray=['0-4', '5-9', '10-14', '15-24', '25-40', '41-54', '55+'])

        return fig

    # zobrazení grafu podle mutací v genu
    @app.callback(
        Output('mut_graph', 'figure'),
        Output('mut_graph1', 'figure'),
        Input('dropdown_study', 'value'),
        Input('m_f_checklist', 'value'),
        Input('age_checklist', 'value')
    )
    def upgrade_graph_mut(study, sex, age):
        conn = sqlite3.connect('src/database/appDB.sqlite')
        query = f"""
            SELECT m.Gene, COUNT(*) AS Mutations
            FROM mutace_panel m
            INNER JOIN pacient_odber_mutace pom on m."HGVS notation" = pom.mutace_idmutace
            INNER JOIN studie s on pom.pacient_idpacient = s.pacient_idpacient
            INNER JOIN studie_enum se on s.studie_enum_idstudie = se.idstudie
            WHERE se.nazev = '{study}'
            GROUP BY m.Gene
            """
        query_filter = f"""
            SELECT p.narozen, 
                CASE
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4)  <= 17 THEN 'Children'
                    WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 18 AND 39 THEN 'AYAs'
                    ELSE 'Elderly'
                END AS Age_Check,
                CASE 
                    WHEN substr(p.rc, 3, 1) IN ('5', '6') THEN 'Female'
                    ELSE  'Male'
                END AS Sex,
                m.Gene,
                COUNT(*) AS Mutation_count
             FROM pacient p
             INNER JOIN pacient_odber_mutace pom ON p.idpacient = pom.pacient_idpacient
             INNER JOIN mutace_panel m ON pom.mutace_idmutace = m."HGVS notation"
             INNER JOIN studie s ON p.idpacient = s.pacient_idpacient
             INNER JOIN studie_enum se ON s.studie_enum_idstudie = se.idstudie
             WHERE se.nazev = '{study}'
             GROUP BY p.narozen, Age_Check, Sex, m.Gene
        """
        df_genes = pd.read_sql(query, conn)
        df_new = pd.read_sql(query_filter, conn)
        conn.close()

        if sex:
            df_new = df_new[df_new['Sex'].isin(sex)]
        if age:
            df_new = df_new[df_new['Age_Check'].isin(age)]

        df = pd.merge(df_genes, df_new, on='Gene', how='left')
        df.drop(columns=['Sex'], inplace=True)
        fig = px.bar(df_genes, x='Mutations', y='Gene', labels={'x': 'Number of mutations', 'y': 'Gene'},
                     title=f'Number of mutations in Gene in {study}', color_discrete_sequence=["#E8D83B"])
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color="black"))
        fig1 = px.bar(df, x='Gene', y='Mutations', color='Age_Check', barmode='group',
                      labels={'x': 'Number of mutations', 'y': 'Gene'}, title=f'Number of mutations in Gene in {study}',
                      color_discrete_map={'Children': 'Turquoise', 'AYAs': 'Yellow', 'Elderly': 'MediumVioletRed '})
        fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color="black"))

        return fig, fig1
    #zobrazen grafu podle onemocnění pacienta
    @app.callback(
        Output('dis_graph', 'figure'),
        Input('dropdown_study', 'value'),
        Input('m_f_checklist', 'value'),
        Input('age_checklist', 'value')
    )
    def upgrade_graph_disease(study, sex, age):
        conn = sqlite3.connect('src/database/appDB.sqlite')
        query = f"""
               SELECT o.nazev AS Disease,
                   CASE 
                       WHEN substr(p.rc, 3, 1) IN ('5', '6') THEN 'Female'
                       ELSE 'Male'
                   END AS Sex,
                   CASE
                       WHEN strftime('%Y', 'now') - substr(p.narozen, -4) <= 17 THEN 'Children'
                       WHEN strftime('%Y', 'now') - substr(p.narozen, -4) BETWEEN 18 AND 39 THEN 'AYAs'
                       ELSE 'Elderly'
                   END AS Age_Check
               FROM pacient p
               INNER JOIN onemocneni o ON p.onemocneni_idonemocneni = o.idonemocneni
               INNER JOIN studie s ON p.idpacient = s.pacient_idpacient
               INNER JOIN studie_enum se ON s.studie_enum_idstudie = se.idstudie
               WHERE se.nazev = '{study}'
           """
        df = pd.read_sql(query, conn)
        conn.close()

        if sex:
            df = df[df['Sex'].isin(sex)]
        if age:
            df = df[df['Age_Check'].isin(age)]

        patient_count = df.groupby(['Disease', 'Sex', 'Age_Check']).size().reset_index(name='Number of Patients')
        fig = px.bar(patient_count, x='Disease', y='Number of Patients', color='Sex', barmode='group',
                     title=f'Number of patients by disease in {study}',
                     color_discrete_map={'Female': 'FireBrick', 'Male': 'DodgerBlue'})
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(color="black"))

        return fig