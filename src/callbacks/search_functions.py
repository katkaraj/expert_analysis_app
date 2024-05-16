# import balíčků
import dash.exceptions
from dash import dcc, html, dash_table, Input, Output, State, MATCH
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import sqlite3
import genebe as gnb
import webbrowser
from src.callbacks.upload_functions import save_to_dir


def search_callbacks(app):
    def search_patient(report_number):
        conn = sqlite3.connect('src/database/appDB.sqlite')
        cur = conn.cursor()

        # vyhledání informací o pacientovi v databázi
        cur.execute("SELECT pacient_idpacient FROM odber WHERE kod = ?", (report_number,))
        patient_code = cur.fetchone()[0]
        search_pat = f"SELECT idpacient, rc, prestavba, narozen, jmeno, prijmeni, diagnoza FROM pacient WHERE idpacient = ?"
        df_pat = pd.read_sql(search_pat, conn, params=[patient_code])
        df_pat = df_pat.rename(columns={'idpacient': 'Patient ID', 'rc': 'Insurance number', 'prestavba': 'Breakpoint',
                                        'narozen': 'Date of birth', 'jmeno': 'First name', 'prijmeni': 'Last name',
                                        'diagnoza': 'Diagnosis'})

        # vyhledání ostatních reportů pacienta v databázi
        codes = f"SELECT kod FROM odber WHERE pacient_idpacient =?"
        df = pd.read_sql(codes, conn, params=[patient_code])
        codes = df['kod']
        string = ', '.join(codes)
        conn.close()
        alert_reports = dbc.Alert(["More patient data were found: ", string], dismissable=True, color="warning")

        if not df_pat.empty and not codes.empty:
            return df_pat, alert_reports
        elif not df_pat.empty:
            return df_pat, None
        else:
            return "Patient not found", ""

    # funkce pro vyhledání cesty a názvu reportu v databázi a následné otevření
    def search_report(report_number):
        conn = sqlite3.connect('src/database/appDB.sqlite')
        cur = conn.cursor()
        cur.execute("SELECT cesta FROM report_odber WHERE kod = ?", (report_number,))
        file_path = cur.fetchone()[0]
        df = pd.read_excel(file_path)
        conn.close()

        def transform_classification(varianty):
            if ';' in varianty:
                if varianty.startswith('m.'):
                    variant_parts = varianty.split('[')
                    transformed = 'm.' + variant_parts[1].split(']')[0]
                    return transformed
                else:
                    parts = varianty.split(':')
                    variant_parts = parts[1].split(';')[0].replace('(', '').replace(')', '').split('[')
                    transformed = parts[0] + ':' + variant_parts[0] + variant_parts[1]
                    return transformed.rstrip(']')
            else:
                return varianty

        variants = df['Mutation Call: HGVS Coding'].apply(transform_classification)
        variants_string = ', '.join("'" + variant + "'" for variant in variants)
        variants_list = [variant.strip("'") for variant in variants_string.split(', ')]
        parsed_var = gnb.parse_hgvs(variants_list)
        df1 = gnb.annotate_variants_list_to_dataframe(parsed_var)
        df = df.iloc[:, 1:]

        classification_column = df1["acmg_classification"]
        if not 'Classification_genebe' in df.columns:
            df.insert(2, "Classification_genebe", classification_column)
        if not 'HGVS notation' in df.columns:
            df.insert(3, "HGVS notation", variants_list)
        return df, df1

    # otevření varianty na webu genebe
    @app.callback(
        Output({'type': 'output', 'index': MATCH}, 'children'),
        Input({'type': 'table', 'index': MATCH}, 'active_cell'),
        State({'type': 'table', 'index': MATCH}, 'data'),
        prevent_initial_call=True
    )
    def open_genebe(active_cell, table):
        data_row = active_cell['row']
        data_col_id = active_cell['column_id']
        if data_col_id == 'HGVS notation':
            df = pd.DataFrame(table)
            cell_value = df.loc[data_row, data_col_id]
            link = f'https://genebe.net/variant/hg38/{cell_value}'
            webbrowser.open_new_tab(link)
        return ''

    # funkce pro podbarvení řádků v excelovém souboru
    def style_excel(row):
        value = row.loc['Classification']
        if value == 'Uncertain significance':
            color = '#F8C471'
        elif value == 'Pathogenic':
            color = '#EC7063'
        elif value == 'Likely_pathogenic':
            color = '#EC7063'
        elif value == '':
            color = 'white'
        else:
            color = 'white'

        return ['background-color: {}'.format(color) for r in row]

    # funkce pro expport vybraných řádků reportu
    @app.callback(
        Output({'type': 'export_download', 'index': MATCH}, 'data'),
        Input({'type': 'export_button', 'index': MATCH}, 'n_clicks'),
        State({'type': 'table', 'index': MATCH}, 'data'),
        State({'type': 'checklist', 'index': MATCH}, 'value'),
        State('tabs', 'active_tab'),
        prevent_initial_call=True
    )
    def export_chosen_variants(n_clicks, table, value, tab):
        name = tab.split('_')[-1]
        if n_clicks:
            df = pd.DataFrame(table)
            classification = value
            df_rows = df.loc[df['Classification'].isin(classification)]
            df_rows_color = df_rows.style.apply(style_excel, axis=1)
            path = f'{name}_{", ".join(value)}.xlsx'
            df_rows_color.to_excel(path, index=False)
            return dcc.send_file(path)

    # funkce pro export celé tabulky reportu
    @app.callback(
        Output({'type': 'export_all_download', 'index': MATCH}, 'data'),
        Input({'type': 'export_all_button', 'index': MATCH}, 'n_clicks'),
        State({'type': 'table', 'index': MATCH}, 'data'),
        State('tabs', 'active_tab'),
        prevent_initial_call=True
    )
    def export_variants(n_clicks_all, table, tab):
        name = tab.split('_')[-1]
        if n_clicks_all:
            df_all = pd.DataFrame(table)
            path_all = f'{name}_all.xlsx'
            df_all_color = df_all.style.apply(style_excel, axis=1)
            df_all_color.to_excel(path_all, index=False)
            return dcc.send_file(path_all)

    # funkce pro uložení mutovaných variant do databáze mutací
    def save_variant_to_db(df, kod):
        conn = sqlite3.connect('src/database/appDB.sqlite')
        cur = conn.cursor()

        cur.execute(f"SELECT id FROM odber WHERE kod='{kod}'")
        idodber = cur.fetchone()[0]
        cur.execute(f"SELECT pacient_idpacient FROM odber WHERE kod='{kod}'")
        idpacient = cur.fetchone()[0]

        cur.execute("SELECT `HGVS notation` FROM mutace_panel")
        existing_hgvs = set(row[0] for row in cur.fetchall())

        rows = df[df['Classification'].isin(['Pathogenic', 'Likely_pathogenic'])]

        for _, row in rows.iterrows():
            idmutace = row['HGVS notation']
            if idmutace in existing_hgvs:
                cur.execute("""UPDATE mutace_panel 
                               SET Classification=?, Classification_genebe=?, Chrom=?, Pos=?, 
                                   `Ref Pos`=?, Function=?, Gene=?, Exon=?, CDS=?, `Amino Acid Change`=?
                               WHERE `HGVS notation`=?""",
                            (row['Classification'], row['Classification_genebe'], row['Chrom'], row['Pos'],
                             row['Ref Pos'], row['Function'], row['Gene'], row['Exon'], row['CDS'],
                             row['Amino Acid Change'], idmutace))
            else:
                cur.execute("""INSERT INTO mutace_panel 
                               (`HGVS notation`, Classification, Classification_genebe, Chrom, Pos, 
                                `Ref Pos`, Function, Gene, Exon, CDS, `Amino Acid Change`)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (idmutace, row['Classification'], row['Classification_genebe'], row['Chrom'],
                             row['Pos'], row['Ref Pos'], row['Function'], row['Gene'], row['Exon'],
                             row['CDS'], row['Amino Acid Change']))

            cur.execute(
                "SELECT COUNT(*) FROM pacient_odber_mutace WHERE pacient_idpacient=? AND odber_idodber=? AND mutace_idmutace=?",
                (idpacient, idodber, idmutace))
            existing_count = cur.fetchone()[0]
            if existing_count == 0:
                cur.execute(
                    "INSERT INTO pacient_odber_mutace (pacient_idpacient, odber_idodber, mutace_idmutace) VALUES (?,?,?)",
                    (idpacient, idodber, idmutace))

        conn.commit()
        conn.close()

    #funkce pro uložení změn v tabulce
    @app.callback(
        Output({'type': 'save_message', 'index': MATCH}, 'children'),
        Input({'type': 'save_button', 'index': MATCH}, 'n_clicks'),
        State({'type': 'table', 'index': MATCH}, 'data'),
        State('tabs', 'active_tab'),
        prevent_initial_call=True
    )
    def save_edited_table(n_clicks, table, tab):
        if n_clicks > 0:
            name = tab.split('_')[-1]
            df = pd.DataFrame(table)
            save_variant_to_db(df, name)
            save_to_dir(df, name)
            return dmc.Alert('Report was saved', duration=5000, color='green')

    # funkce pro vypsání indexů na kterých se liší klasifikace
    def classification_alert(df):
        compare = ((df['Classification'].isin(['Benign', 'Likely_benign'])) & df['Classification_genebe'].isin(
            ['Benign', 'Likely_benign'])) | \
                  ((df['Classification'] == 'Uncertain_significance') & df['Classification_genebe'].isin(
                      ['Uncertain_significance'])) | \
                  ((df['Classification'].isin(['Pathogenic', 'Likely_pathogenic'])) & df['Classification_genebe'].isin(
                      ['Pathogenic', 'Likely_pathogenic'])) | \
                  ((df['Classification'].isna()) & df['Classification_genebe'].isna())

        index = df.loc[(compare == False) & df['Coverage'].gt(300), 'Index'] if df['Coverage'].gt(300).any() else None

        if not index.empty:
            class_alert = dbc.Alert(f"Different classification on indexes: {', '.join(index.astype(str))}",
                                dismissable=True, color="danger")
            return class_alert
        else:
            return None

    # zobrazení reportu v záložce
    def tab_content(report_number):
        df_patient, report_codes = search_patient(report_number)
        df, df_gnb = search_report(report_number)
        table = dash_table.DataTable(
            id={'type': 'table',
                'index': report_number},
            data=df.to_dict('records'),
            editable=True,
            sort_action="native",
            style_table={"overflowX": "auto", 'overflowY': 'auto'},
            style_data={"textAlign": "left", 'cursor': 'pointer'},
            style_header={'fontWeight': 'bold', "textAlign": "left", "backgroundColor": "white"},
            columns=[{'name': col, 'id': col, 'presentation': 'dropdown'} for col in df.columns],
            dropdown={'Classification': {'options': [{'label': i, 'value': i} for i in
                                                     ["Benign", "Likely_benign", "Uncertain_significance", "Pathogenic",
                                                      "Likely_pathogenic"]]}},
            style_data_conditional=[{'if': {'filter_query': '{Coverage} < 300'}, 'backgroundColor': '#FADBD8'},
                                    {'if': {'filter_query': '{Classification} = Uncertain_significance'},
                                     'backgroundColor': '#F8C471'},
                                    {'if': {'filter_query': '{Classification} = Pathogenic'},
                                     'backgroundColor': '#EC7063'},
                                    {'if': {'filter_query': '{Classification} = Likely_pathogenic'},
                                     'backgroundColor': '#EC7063'},
                                    ],
        )

        # legenda k podbarvení reportu
        legenda = dbc.Card([dbc.CardHeader("Color scheme based on variant classification:"),
                            dbc.CardBody([dbc.Row([
                                dbc.Col(
                                    html.Div(style={'background-color': '#F8C471', 'height': '20px', 'width': '20px'}),
                                    width=2),
                                dbc.Col(html.P("Uncertain significance"), width=10),
                            ]),
                                dbc.Row([
                                    dbc.Col(
                                        html.Div(
                                            style={'background-color': '#EC7063', 'height': '20px', 'width': '20px'}),
                                        width=2),
                                    dbc.Col(html.P("Pathogenic or Likely Pathogenic"), width=10),
                                ]),
                                dbc.Row([
                                    dbc.Col(
                                        html.Div(
                                            style={'background-color': '#FADBD8', 'height': '20px', 'width': '20px'}),
                                        width=2),
                                    dbc.Col(html.P("Coverage under 300"), width=10),
                                ]), ])])

        class_alert = classification_alert(df)
        checklist = html.Div([dbc.Label("Choose variants for export:"),
                              dbc.Checklist(
                                  options=["Benign", "Likely_benign", "Uncertain significance", "Pathogenic",
                                           "Likely_pathogenic"],
                                  id={'type': 'checklist',
                                      'index': report_number},
                                  inline=False
                              ), ])
        save_button = dbc.Button("Save work", id={'type': 'save_button',
                                                  'index': report_number}, n_clicks=0)
        export_button = dbc.Button("Export selected to excel", id={'type': 'export_button',
                                                                   'index': report_number}, n_clicks=0,
                                   className='me-1')
        export_all_button = dbc.Button("Export all to excel", id={'type': 'export_all_button',
                                                                  'index': report_number}, n_clicks=0, className='me-1')

        rep_acc_item = dbc.AccordionItem([dbc.Row(report_codes),
                                          dbc.Row(class_alert),
                                          dbc.Row(legenda),
                                          dbc.Row([table, html.Div(id={'type': 'output', 'index': report_number})]),
                                          dbc.Row([
                                              dbc.Col(checklist),
                                              dbc.Col([export_button, html.Div(
                                                  dcc.Download(id={'type': 'export_download', 'index': report_number})),
                                                       export_all_button, html.Div(dcc.Download(
                                                      id={'type': 'export_all_download', 'index': report_number}))]),
                                              html.Div(id={'type': 'export_message',
                                                           'index': report_number})], className='mb-3'),
                                          dbc.Row([save_button, html.Div(id={'type': 'save_message',
                                                                             'index': report_number})]),
                                          ], title="Report table")
        data_list = df_patient.to_dict('records')
        pat_acc_item = dbc.AccordionItem([dbc.Row([
            dbc.Col([f"{col}"], style={"font-weight": "bold"}),
            dbc.Col([data[col]])
        ]) for data in data_list for col in df_patient.columns
        ], title="Patient info")

        rep_acc = dbc.Accordion([rep_acc_item], start_collapsed=True, flush=True)
        pat_acc = dbc.Accordion([pat_acc_item], start_collapsed=True, flush=True)
        content = html.Div([pat_acc, rep_acc])

        return content

    # otevření nové záložky
    @app.callback(
        Output('tabs', 'children'),
        Output('search_ex_alert','children'),
        Input('open_button', 'n_clicks'),
        State('tabs', 'children'),
        State('report_input', 'value'),
        prevent_initial_call=True
    )
    def open_tab(n_clicks, current_children, report_number):
        try:
            conn = sqlite3.connect('src/database/appDB.sqlite')
            cur = conn.cursor()
            cur.execute(f"SELECT id FROM report_odber WHERE kod = ?", (report_number,))
            id = cur.fetchone()[0]

            if n_clicks:
                if id is not None:
                    new_tab_id = report_number
                    new_tab = dbc.Tab(label=report_number, tab_id=new_tab_id, children=[tab_content(report_number)],
                              loading_state=True)
                    current_children.append(new_tab)
                    return current_children, None

        except Exception as e:
            print(e)
            alert = dmc.Alert("This report isn't in the database.", duration=5000, color='red')
            return current_children, alert

        return current_children