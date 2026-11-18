"""
Regroupe etudiants.csv, productions.csv et interventions.csv dans un seul
fichier Excel (ltpa_donnees.xlsx) : un onglet par table, chaque onglet mis
en forme de TABLEAU Excel (nécessaire pour l'import dans Power BI Service).
"""
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

print("Création du fichier Excel consolidé...")

# Lecture des CSV, avec de vraies dates (sinon elles resteraient du texte)
tables = {
    "etudiants": pd.read_csv("etudiants.csv", parse_dates=["Date_Inscription", "Date_Fin"]),
    "productions": pd.read_csv("productions.csv", parse_dates=["Date_Production"]),
    "interventions": pd.read_csv("interventions.csv", parse_dates=["Date_Intervention"]),
}

with pd.ExcelWriter("ltpa_donnees.xlsx", engine="openpyxl") as writer:
    for nom, df in tables.items():
        df.to_excel(writer, sheet_name=nom, index=False)
        ws = writer.sheets[nom]

        # Transforme la plage de données en tableau Excel nommé
        derniere_col = get_column_letter(df.shape[1])
        tableau = Table(displayName=nom, ref=f"A1:{derniere_col}{len(df) + 1}")
        tableau.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(tableau)

        # Affiche les dates sans l'heure (AAAA-MM-JJ)
        for i, col in enumerate(df.columns, start=1):
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                for ligne in range(2, len(df) + 2):
                    ws.cell(row=ligne, column=i).number_format = "YYYY-MM-DD"

        # Largeur de colonnes lisible
        for i, col in enumerate(df.columns, start=1):
            largeur = max(len(str(col)), df[col].astype(str).str.len().max()) + 2
            ws.column_dimensions[get_column_letter(i)].width = min(largeur, 40)

        print(f"   - onglet '{nom}' : {len(df)} lignes")

print("✅ Fichier 'ltpa_donnees.xlsx' créé avec succès !")
