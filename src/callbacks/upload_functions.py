# import balíčků
import base64
import pandas as pd
import io
import re
import os
from dash import Input, Output, State, dcc
import dash_mantine_components as dmc
import sqlite3

# cesta ke složce s reporty, vytvoření složky pokud není v adresáři
reports_folder = 'src/data/reports'
if not os.path.exists(reports_folder):
    os.makedirs(reports_folder)


# úprava txt souboru
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df_name = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter="\t", nrows=3, header=None)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter="\t", skiprows=4, header=0)
    df = df.iloc[:, :-1]
    df.insert(1, "Classification", value="")
    name = str(df_name.iloc[1, 1])
    name = re.split('[-_]', name)
    result = name[0]
    return df, result


def upload_callbacks(app):
    # nahrání souboru do složky
    @app.callback(
        Output('upload_label', 'children'),
        Input('upload-data', 'contents'),
        State('upload-data', 'filename'),
    )
    def upload_file(contents, filenames):
        try:
            if contents is not None:
                for content, filename in zip(contents, filenames):
                    df, name = parse_contents(content, filename)
                    save_to_dir(df, name)
                    file_path = os.path.join(reports_folder, f'{name}.xlsx')
                    save_filepath_to_db(name, file_path)
                    return dmc.Alert(f"Report {name} was uploaded successfully", duration=5000, color='green')
        except Exception as e:
            print(e)
            return dmc.Alert("There was an error processing this file.", duration=5000, color='red')


# uložení souboru ve formátu txt do složky
def save_to_dir(df, name):
    file_path = os.path.join(reports_folder, f'{name}.xlsx')
    df.to_excel(file_path)
    dcc.send_file(file_path)


# uložení cesty k souboru do databáze
def save_filepath_to_db(filename, file_path):
    conn = sqlite3.connect('src/database/appDB.sqlite')
    cur = conn.cursor()
    cur.execute("SELECT id FROM report_odber WHERE kod = ?", (filename,))
    row = cur.fetchone()
    if row is None:
        cur.execute(f'INSERT INTO report_odber (kod, cesta) VALUES (?,?)', (filename, file_path))
        conn.commit()
    conn.close()
