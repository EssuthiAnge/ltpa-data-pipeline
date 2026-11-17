"""
Générateur de données fictives : établissement agricole.
Produit 3 fichiers CSV cohérents et reproductibles :
  - etudiants.csv
  - productions.csv
  - interventions.csv (département Maintenance)
"""
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

# --- 0. CONSTANTES ---------------------------------------------------------
SEED = 42
NB_ETUDIANTS = 150
NB_PRODUCTIONS = 300
NB_INTERVENTIONS = 120

DEBUT_INSCRIPTION = date(2024, 11, 1)
DEBUT_PROD = date(2025, 1, 1)
FIN = date(2026, 11, 17)
SEUIL_DIPLOME = date(2025, 11, 17)   # inscrit avant => peut être diplômé
SEUIL_STOCK = date(2026, 8, 31)      # produit avant => rarement en stock

random.seed(SEED)
Faker.seed(SEED)
fake = Faker("fr_FR")

DEPARTEMENTS = ["Production Animale", "Production Végétale", "TCPA", "Maintenance"]
POIDS_DEPARTEMENTS = [30, 35, 20, 15]

OPTIONS = {
    "Production Animale": ["Aquaculture", "Monogastriques", "Bovins et Petits Ruminants"],
    "Production Végétale": ["Cultures Pérennes", "Plants et Semences", "Céréales et Champignons",
                            "Maraîchage", "Racines et Tubercules"],
    "TCPA": ["Transformation Animale", "Transformation Végétale"],
    "Maintenance": ["Maintenance des Équipements Agricoles"],
}
OPTION_VERS_DEPT = {opt: d for d, opts in OPTIONS.items() for opt in opts}

PRODUCTIONS_POSSIBLES = {
    "Aquaculture": ["Silure", "Tilapia"],
    "Monogastriques": ["Porc", "Poulet de chair", "Poule pondeuse", "Lapin"],
    "Bovins et Petits Ruminants": ["Bovin (embouche)", "Mouton", "Chèvre"],
    "Cultures Pérennes": ["Cacao", "Café", "Palmier à huile"],
    "Plants et Semences": ["Plants greffés", "Semences certifiées"],
    "Céréales et Champignons": ["Maïs", "Haricot", "Pleurotes"],
    "Maraîchage": ["Tomate", "Piment", "Oignon"],
    "Racines et Tubercules": ["Manioc", "Igname", "Macabo"],
    "Transformation Animale": ["Poisson fumé", "Charcuterie"],
    "Transformation Végétale": ["Farine de manioc", "Huile d'arachide"],
}

# produit -> (unité, min, max) ; par défaut : Kg entre 10 et 500
UNITES_PRODUITS = {
    "Bovin (embouche)": ("Têtes", 1, 15),
    "Mouton": ("Têtes", 2, 30),
    "Chèvre": ("Têtes", 2, 30),
    "Porc": ("Têtes", 2, 25),
    "Poulet de chair": ("Têtes", 20, 300),
    "Poule pondeuse": ("Têtes", 20, 300),
    "Lapin": ("Têtes", 5, 50),
    "Plants greffés": ("Unités", 50, 500),
    "Huile d'arachide": ("Litres", 10, 200),
}
UNITE_DEFAUT = ("Kg", 10, 500)

EQUIPEMENTS = ["Tracteur", "Motoculteur", "Pompe d'irrigation", "Décortiqueuse",
               "Moulin à manioc", "Semoir", "Groupe électrogène", "Pulvérisateur"]


# --- 1. ÉTUDIANTS ----------------------------------------------------------
def generer_statut_et_fin(date_insc):
    """Statut cohérent avec l'ancienneté, et date de fin associée."""
    if date_insc <= SEUIL_DIPLOME:
        statut = random.choices(["Actif", "Diplômé", "Abandon"], weights=[65, 30, 5])[0]
    else:
        statut = random.choices(["Actif", "Abandon"], weights=[95, 5])[0]

    if statut == "Diplômé":
        fin = min(date_insc + timedelta(days=random.randint(365, 540)), FIN)
    elif statut == "Abandon":
        fin = min(date_insc + timedelta(days=random.randint(30, 400)), FIN)
    else:
        fin = None
    return statut, fin


def generer_etudiants():
    lignes = []
    for i in range(1, NB_ETUDIANTS + 1):
        dept = random.choices(DEPARTEMENTS, weights=POIDS_DEPARTEMENTS)[0]
        date_insc = fake.date_between(start_date=DEBUT_INSCRIPTION, end_date=FIN)
        statut, date_fin = generer_statut_et_fin(date_insc)
        lignes.append({
            "ID_Etudiant": f"ETU{i:03d}",
            "Nom": fake.last_name(),
            "Prenom": fake.first_name(),
            "Departement": dept,
            "Option": random.choice(OPTIONS[dept]),
            "Date_Inscription": date_insc,
            "Statut": statut,
            "Date_Fin": date_fin,
        })
    return pd.DataFrame(lignes)


# --- 2. OUTILS : FENÊTRE D'ACTIVITÉ ----------------------------------------
def fenetres_activite(df_etudiants):
    """Pour chaque étudiant : (début, fin) pendant lesquels il peut produire."""
    fenetres = {}
    for r in df_etudiants.itertuples():
        debut = max(r.Date_Inscription, DEBUT_PROD)
        fin = r.Date_Fin if pd.notna(r.Date_Fin) else FIN
        if debut <= fin:
            fenetres[r.ID_Etudiant] = (debut, fin)
    return fenetres


def candidats_par_option(df_etudiants, fenetres):
    return (
        df_etudiants[df_etudiants["ID_Etudiant"].isin(fenetres)]
        .groupby("Option")["ID_Etudiant"].apply(list).to_dict()
    )


# --- 3. PRODUCTIONS --------------------------------------------------------
def generer_quantite(produit):
    unite, mini, maxi = UNITES_PRODUITS.get(produit, UNITE_DEFAUT)
    if unite in ("Têtes", "Unités"):
        return random.randint(mini, maxi), unite
    return round(random.uniform(mini, maxi), 2), unite


def generer_productions(df_etudiants):
    fenetres = fenetres_activite(df_etudiants)
    par_option = candidats_par_option(df_etudiants, fenetres)
    options_producibles = [o for o in PRODUCTIONS_POSSIBLES if par_option.get(o)]

    lignes = []
    for i in range(1, NB_PRODUCTIONS + 1):
        option = random.choice(options_producibles)
        produit = random.choice(PRODUCTIONS_POSSIBLES[option])
        etu_id = random.choice(par_option[option])
        debut, fin = fenetres[etu_id]
        date_prod = fake.date_between(start_date=debut, end_date=fin)

        poids = [5, 85, 10] if date_prod <= SEUIL_STOCK else [50, 40, 10]
        quantite, unite = generer_quantite(produit)

        lignes.append({
            "ID_Production": f"PROD{i:03d}",
            "Produit": produit,
            "Departement": OPTION_VERS_DEPT[option],
            "Option_Associee": option,
            "ID_Etudiant_Responsable": etu_id,
            "Quantite": quantite,
            "Unite": unite,
            "Date_Production": date_prod,
            "Statut_Vente": random.choices(["En stock", "Vendu", "Perdu"], weights=poids)[0],
        })
    return pd.DataFrame(lignes)


# --- 4. INTERVENTIONS (MAINTENANCE) ----------------------------------------
def generer_interventions(df_etudiants):
    fenetres = fenetres_activite(df_etudiants)
    maintenance = [e for e in df_etudiants.loc[df_etudiants["Departement"] == "Maintenance",
                                               "ID_Etudiant"] if e in fenetres]
    lignes = []
    for i in range(1, NB_INTERVENTIONS + 1):
        etu_id = random.choice(maintenance)
        debut, fin = fenetres[etu_id]
        date_int = fake.date_between(start_date=debut, end_date=fin)
        lignes.append({
            "ID_Intervention": f"INT{i:03d}",
            "ID_Etudiant": etu_id,
            "Equipement": random.choice(EQUIPEMENTS),
            "Type": random.choices(["Préventive", "Corrective"], weights=[40, 60])[0],
            "Duree_Heures": round(random.uniform(0.5, 12.0), 1),
            "Date_Intervention": date_int,
            "Statut": "Terminée" if date_int <= SEUIL_STOCK else
                      random.choices(["Terminée", "En cours"], weights=[70, 30])[0],
        })
    return pd.DataFrame(lignes)


# --- 5. CONTRÔLES DE COHÉRENCE ---------------------------------------------
def verifier(df_e, df_p, df_i):
    assert df_e["ID_Etudiant"].is_unique, "ID_Etudiant en double"
    assert df_p["ID_Production"].is_unique, "ID_Production en double"
    assert df_p["ID_Etudiant_Responsable"].notna().all(), "Production sans responsable"
    assert df_p["ID_Etudiant_Responsable"].isin(df_e["ID_Etudiant"]).all(), "Clé étrangère invalide"
    assert df_i["ID_Etudiant"].isin(df_e["ID_Etudiant"]).all(), "Clé étrangère invalide (interventions)"

    # Étudiants
    assert (df_e.loc[df_e["Statut"] == "Actif", "Date_Fin"].isna()).all(), "Actif avec date de fin"
    fin = df_e[df_e["Statut"] != "Actif"]
    assert (fin["Date_Fin"] > fin["Date_Inscription"]).all(), "Fin avant inscription"
    dipl = df_e[df_e["Statut"] == "Diplômé"]
    assert ((dipl["Date_Fin"] - dipl["Date_Inscription"]).map(lambda d: d.days) >= 365).all(), \
        "Diplômé avec moins d'un an"

    # Productions
    m = df_p.merge(df_e, left_on="ID_Etudiant_Responsable", right_on="ID_Etudiant", validate="m:1")
    assert (m["Date_Production"] >= m["Date_Inscription"]).all(), "Production avant inscription"
    fin_eff = m["Date_Fin"].where(m["Date_Fin"].notna(), FIN)
    assert (m["Date_Production"] <= fin_eff).all(), "Production après départ"
    assert (m["Option_Associee"] == m["Option"]).all(), "Option incohérente"
    assert (m["Departement_x"] == m["Departement_y"]).all(), "Département incohérent"

    # Interventions
    mi = df_i.merge(df_e, on="ID_Etudiant", validate="m:1")
    assert (mi["Departement"] == "Maintenance").all(), "Intervention hors Maintenance"
    assert (mi["Date_Intervention"] >= mi["Date_Inscription"]).all(), "Intervention avant inscription"
    print("✅ Contrôles de cohérence réussis.")


# --- 6. PROGRAMME PRINCIPAL ------------------------------------------------
def exporter(df, nom):
    df.to_csv(nom, index=False, encoding="utf-8-sig")
    print(f"✅ '{nom}' généré ({len(df)} lignes).")


def main():
    df_e = generer_etudiants()
    df_p = generer_productions(df_e)
    df_i = generer_interventions(df_e)
    verifier(df_e, df_p, df_i)
    exporter(df_e, "etudiants.csv")
    exporter(df_p, "productions.csv")
    exporter(df_i, "interventions.csv")


if __name__ == "__main__":
    main()