"""
Pipeline ETL LTPA : CSV -> PostgreSQL
Lit etudiants.csv, productions.csv et interventions.csv (générés par
generer_donnees.py), crée les tables avec les bons types et les clés,
puis charge les données.
"""
import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

print("🚀 Démarrage du pipeline ETL LTPA...")

# --- 1. CONNEXION (Docker PostgreSQL) --------------------------------------
# Les valeurs par défaut sont les tiennes ; on peut les remplacer par des
# variables d'environnement pour ne pas laisser le mot de passe dans le code.

DB_USER = "admin_ltpa"
DB_PASSWORD = "password_ltpa"
DB_HOST = "localhost"
DB_PORT = "5434"
DB_NAME = "ltpa_simulation"

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
try:
    with engine.connect():
        print("✅ Connexion à PostgreSQL réussie !")
except Exception as e:
    print(f"❌ Erreur de connexion à la base de données : {e}")
    sys.exit(1)

# --- 2. EXTRACTION (lecture des CSV, avec de vraies dates) -----------------
print("📥 Extraction des données depuis les fichiers CSV...")
try:
    df_etudiants = pd.read_csv("etudiants.csv", parse_dates=["Date_Inscription", "Date_Fin"])
    df_productions = pd.read_csv("productions.csv", parse_dates=["Date_Production"])
    df_interventions = pd.read_csv("interventions.csv", parse_dates=["Date_Intervention"])
except FileNotFoundError as e:
    print(f"❌ Fichier introuvable : {e.filename}. Avez-vous lancé generer_donnees.py ?")
    sys.exit(1)

print(f"   - {len(df_etudiants)} étudiants extraits.")
print(f"   - {len(df_productions)} productions extraites.")
print(f"   - {len(df_interventions)} interventions extraites.")

# --- 3. TRANSFORMATION (nettoyage basique) ---------------------------------
print("🔄 Transformation et nettoyage des données...")
df_etudiants = df_etudiants.drop_duplicates(subset=["ID_Etudiant"])
df_productions = df_productions.drop_duplicates(subset=["ID_Production"])
df_interventions = df_interventions.drop_duplicates(subset=["ID_Intervention"])
print("   - Vérification des doublons terminée.")

# --- 4. CRÉATION DES TABLES (types + clés primaires et étrangères) ---------
DDL = """
DROP TABLE IF EXISTS interventions, productions, etudiants CASCADE;

CREATE TABLE etudiants (
    "ID_Etudiant"      VARCHAR(10) PRIMARY KEY,
    "Nom"              VARCHAR(100) NOT NULL,
    "Prenom"           VARCHAR(100) NOT NULL,
    "Departement"      VARCHAR(50)  NOT NULL,
    "Option"           VARCHAR(100) NOT NULL,
    "Date_Inscription" DATE         NOT NULL,
    "Statut"           VARCHAR(20)  NOT NULL,
    "Date_Fin"         DATE
);

CREATE TABLE productions (
    "ID_Production"           VARCHAR(10) PRIMARY KEY,
    "Produit"                 VARCHAR(100) NOT NULL,
    "Departement"             VARCHAR(50)  NOT NULL,
    "Option_Associee"         VARCHAR(100) NOT NULL,
    "ID_Etudiant_Responsable" VARCHAR(10) REFERENCES etudiants("ID_Etudiant"),
    "Quantite"                NUMERIC(10,2) NOT NULL,
    "Unite"                   VARCHAR(20)  NOT NULL,
    "Date_Production"         DATE         NOT NULL,
    "Statut_Vente"            VARCHAR(20)  NOT NULL
);

CREATE TABLE interventions (
    "ID_Intervention"   VARCHAR(10) PRIMARY KEY,
    "ID_Etudiant"       VARCHAR(10) NOT NULL REFERENCES etudiants("ID_Etudiant"),
    "Equipement"        VARCHAR(100) NOT NULL,
    "Type"              VARCHAR(20)  NOT NULL,
    "Duree_Heures"      NUMERIC(4,1) NOT NULL,
    "Date_Intervention" DATE         NOT NULL,
    "Statut"            VARCHAR(20)  NOT NULL
);
"""

# --- 5. CHARGEMENT (dans une seule transaction : tout ou rien) -------------
print("📤 Chargement des données dans PostgreSQL...")
try:
    with engine.begin() as conn:
        conn.execute(text(DDL))
        print("   - Tables créées (avec types et clés).")
        # Ordre important : les étudiants d'abord, car les autres tables y font référence
        df_etudiants.to_sql("etudiants", conn, if_exists="append", index=False)
        print("   - Table 'etudiants' chargée.")
        df_productions.to_sql("productions", conn, if_exists="append", index=False)
        print("   - Table 'productions' chargée.")
        df_interventions.to_sql("interventions", conn, if_exists="append", index=False)
        print("   - Table 'interventions' chargée.")
    print("🎉 Pipeline ETL terminé avec succès !")
except Exception as e:
    print(f"❌ Erreur lors du chargement (rien n'a été modifié) : {e}")
    sys.exit(1)