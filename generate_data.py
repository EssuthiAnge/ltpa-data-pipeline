import pandas as pd
from faker import Faker
import random

# Initialisation et reproductibilité totale
fake = Faker('fr_FR')
Faker.seed(42)
random.seed(42)

# --- 1. GÉNÉRATION DES ÉTUDIANTS ---
departements = ["Production Animale", "Production Végétale", "TCPA", "Maintenance"]
options = {
    "Production Animale": ["Aquaculture", "Monogastriques", "Bovins et Petits Ruminants"],
    "Production Végétale": ["Cultures Pérennes", "Plants et Semences", "Céréales et Champignons", "Maraîchage", "Racines et Tubercules"],
    "TCPA": ["Transformation Animale", "Transformation Végétale"],
    "Maintenance": ["Maintenance des Équipements Agricoles"]
}

etudiants = []
for i in range(1, 151):
    dept = random.choice(departements)
    etudiants.append({
        "ID_Etudiant": f"ETU{i:03d}",
        "Nom": fake.last_name(),
        "Prenom": fake.first_name(),
        "Departement": dept,
        "Option": random.choice(options[dept]),
        "Date_Inscription": fake.date_between(start_date="-2y", end_date="today"),
        "Statut": random.choices(["Actif", "Diplômé", "Abandon"], weights=[80, 15, 5])[0]
    })

df_etudiants = pd.DataFrame(etudiants)
df_etudiants.to_csv("etudiants.csv", index=False, encoding="utf-8-sig")
print("✅ Fichier 'etudiants.csv' généré (150 lignes).")

# --- 2. GÉNÉRATION DES PRODUCTIONS ---
productions_possibles = {
    "Aquaculture": ["Silure", "Tilapia"],
    "Monogastriques": ["Porc", "Poulet de chair", "Poule pondeuse", "Lapin"],
    "Bovins et Petits Ruminants": ["Bovin (embouche)", "Mouton", "Chèvre"],
    "Cultures Pérennes": ["Cacao", "Café", "Palmier à huile"],
    "Plants et Semences": ["Plants greffés", "Semences certifiées"],
    "Céréales et Champignons": ["Maïs", "Haricot", "Pleurotes"],
    "Maraîchage": ["Tomate", "Piment", "Oignon"],
    "Racines et Tubercules": ["Manioc", "Igname", "Macabo"],
    "Transformation Animale": ["Poisson fumé", "Charcuterie"],
    "Transformation Végétale": ["Farine de manioc", "Huile d'arachide"]
}

# Dictionnaire inversé pour retrouver le département à partir de l'option
option_vers_dept = {opt: dept for dept, opts in options.items() for opt in opts}

productions = []
for i in range(1, 301):
    option = random.choice(list(productions_possibles.keys()))
    produit = random.choice(productions_possibles[option])
    
    # Sélection d'un étudiant de la même option (si disponible)
    etudiants_option = df_etudiants[df_etudiants["Option"] == option]["ID_Etudiant"].tolist()
    etu_id = random.choice(etudiants_option) if etudiants_option else None

    productions.append({
        "ID_Production": f"PROD{i:03d}",
        "Produit": produit,
        "Departement": option_vers_dept[option],
        "Option_Associee": option,
        "ID_Etudiant_Responsable": etu_id,
        "Quantite_Kg_ou_Unites": round(random.uniform(10.0, 500.0), 2),
        "Date_Production": fake.date_between(start_date="-1y", end_date="today"),
        "Statut_Vente": random.choices(["En stock", "Vendu", "Perdu"], weights=[30, 60, 10])[0]
    })

df_productions = pd.DataFrame(productions)
df_productions.to_csv("productions.csv", index=False, encoding="utf-8-sig")
print("✅ Fichier 'productions.csv' généré (300 lignes).")
