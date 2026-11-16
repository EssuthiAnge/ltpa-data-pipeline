import pandas as pd
from sqlalchemy import create_engine
import time

print("🚀 Démarrage du pipeline ETL LTPA...")

# --- 1. CONFIGURATION DE LA CONNEXION (DOCKER POSTGRESQL) ---
# Format : postgresql://utilisateur:mot_de_passe@hote:port/nom_de_la_base
DB_USER = "admin_ltpa"
DB_PASSWORD = "password_ltpa"
DB_HOST = "localhost"
DB_PORT = "5434"
DB_NAME = "ltpa_simulation"

connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
try:
    # Création du moteur de connexion SQLAlchemy
    engine = create_engine(connection_string)
    # Test de connexion
    with engine.connect() as conn:
        print("✅ Connexion à PostgreSQL réussie !")
except Exception as e:
    print(f"❌ Erreur de connexion à la base de données : {e}")
    exit()

# --- 2. EXTRACTION (Lecture des CSV) ---
print("📥 Extraction des données depuis les fichiers CSV...")
try:
    df_etudiants = pd.read_csv("etudiants.csv")
    df_productions = pd.read_csv("productions.csv")
    print(f"   - {len(df_etudiants)} étudiants extraits.")
    print(f"   - {len(df_productions)} productions extraites.")
except FileNotFoundError:
    print("❌ Erreur : Les fichiers CSV n'existent pas. Avez-vous lancé generate_data.py ?")
    exit()

# --- 3. TRANSFORMATION (Nettoyage basique) ---
print("🔄 Transformation et nettoyage des données...")
# Exemple : S'assurer qu'il n'y a pas de doublons sur les ID
df_etudiants = df_etudiants.drop_duplicates(subset=["ID_Etudiant"])
df_productions = df_productions.drop_duplicates(subset=["ID_Production"])
print("   - Vérification des doublons terminée.")

# --- 4. CHARGEMENT (Envoi vers PostgreSQL) ---
print("📤 Chargement des données dans PostgreSQL...")
try:
    # On envoie df_etudiants dans la table 'etudiants'
    # if_exists='replace' écrase la table si elle existe déjà (pratique pour le développement)
    df_etudiants.to_sql(name="etudiants", con=engine, if_exists="replace", index=False)
    print("   - Table 'etudiants' mise à jour.")
    
    # On envoie df_productions dans la table 'productions'
    df_productions.to_sql(name="productions", con=engine, if_exists="replace", index=False)
    print("   - Table 'productions' mise à jour.")
    
    print("🎉 Pipeline ETL terminé avec succès !")
except Exception as e:
    print(f"❌ Erreur lors du chargement des données : {e}")