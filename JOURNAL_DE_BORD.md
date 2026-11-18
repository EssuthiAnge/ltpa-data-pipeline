# 📓 Journal de Bord - Projet Data LTPA

## Session 1 : Initialisation et Architecture des Données

### 1. Contexte
Création d'une simulation de pipeline ETL pour le site du LTPA de Yabassi. Les données simuleront la gestion des étudiants et des productions agricoles.

### 2. Actions réalisées
*   Vérification de l'environnement (Linux, Docker, Python).
*   Création de l'environnement virtuel Python (`venv`).
*   Installation des dépendances : `pandas`, `sqlalchemy`, `psycopg2-binary`, `faker`.
*   Initialisation des fichiers de documentation (`README.md` et `JOURNAL_DE_BORD.md`).
*   Création des fichiers `.gitignore` et `requirements.txt`.

### 3. Configuration de la Base de Données (Docker)
*   Création d'un fichier `docker-compose.yml` (PostgreSQL 17).
*   Exposition sur le port `5434` pour éviter les conflits avec d'autres projets locaux.
*   Utilisation d'un volume nommé (`postgres_data`) pour la persistance des données.

### 4. Conception des données (Basée sur le dossier de contenu LTPA)
*   **Départements :** PA, PV, TCPA, MEA.
*   **Options (11) :** Aquaculture, Monogastriques, Bovins, Cultures Pérennes, Semences, Céréales, Maraîchage, Racines, Transformation Animale, Transformation Végétale, Maintenance.
*   **Données générées :** 150 étudiants fictifs et 300 productions.
*   **Logique métier :** Respect des dates d'inscription, gestion des unités réalistes (Têtes, Litres, Kg).

### 5. Développement du Pipeline ETL
*   **Script `generate_data.py` :** Utilisation de Faker et random avec seed (42) pour la reproductibilité. Génération des fichiers `etudiants.csv` et `productions.csv` (encodage `utf-8-sig` pour Excel).
*   **Script `main.py` :** Connexion à PostgreSQL via SQLAlchemy. Lecture des CSV (Pandas), suppression des doublons, et chargement dans les tables `etudiants` et `productions` (avec `if_exists="replace"`).

### 6. Problèmes rencontrés & Solutions
*   **Problème :** Erreur `No module named 'psycopg'` lors de la connexion.
*   **Solution :** SQLAlchemy 2.1 utilise par défaut `psycopg` (v3). Modification de la chaîne de connexion en `postgresql+psycopg2://` pour forcer l'utilisation du pilote installé.

### 7. Vérification
*   Connexion réussie via DBeaver sur la base `ltpa_simulation`.
*   Vérification visuelle des 150 étudiants et 300 productions insérés avec succès.

## Session 2 : Audit de la Qualité des Données (Data Quality)

### 1. Problèmes identifiés sur la première version
*   Incohérence temporelle : des productions étaient datées avant l'inscription des étudiants.
*   Incohérence logique : des étudiants récemment inscrits avaient le statut "Diplômé".
*   Incohérence de mesure : les animaux (lapins, moutons) étaient en décimales au lieu d'être en entiers (têtes).
*   Reproductibilité : l'utilisation de dates dynamiques (today) rendait les données différentes à chaque exécution.

## Session 3 : Refonte du Générateur et Modélisation DDL

### 1. Améliorations apportées (Générateur)
*   Refonte du script `generate_data.py` avec des dates fixes pour une reproductibilité totale.
*   Ajout de "fenêtres d'activité" : un étudiant ne peut produire qu'entre son inscription et sa sortie.
*   Gestion des unités : "Têtes" pour les animaux, "Kg" pour les récoltes.
*   Ajout de contrôles d'intégrité (assertions) avant l'export CSV.
*   Création d'une nouvelle table `interventions.csv` pour les activités de maintenance.

### 2. Améliorations apportées (Pipeline ETL)
*   Remplacement de `to_sql(if_exists='replace')` par l'exécution de requêtes **DDL** (Data Definition Language).
*   Création explicite des tables avec les bons types (`DATE`, `NUMERIC`) et les contraintes (`PRIMARY KEY`, `FOREIGN KEY`).
*   Utilisation d'une transaction (`engine.begin()`) : si une erreur survient, aucune donnée n'est insérée (principe du "tout ou rien").

### 3. Vérification visuelle et Preuves
*   Validation dans DBeaver : les colonnes de dates sont bien typées (icône calendrier) et les relations sont établies.
*   Captures d'écran ajoutées au dossier `images/` :

**Table etudiants :**
![Aperçu des étudiants](images/etudiant.png)

**Table productions :**
![Aperçu des productions](images/production.png)

**Table interventions :**
![Aperçu des interventions](images/intervention.png)


## Session 4 : Visualisation avec Power BI Service

### 1. Objectif
Construire un tableau de bord Power BI à partir des trois tables du projet (`etudiants`, `productions`, `interventions`), depuis un poste Linux et sans machine virtuelle.

### 2. Contraintes identifiées
*   Power BI Service (version web) ne peut pas lire directement la base PostgreSQL qui tourne dans Docker sur le poste local : l'accès passerait par une passerelle de données, qui ne s'installe que sous Windows.
*   Contournement retenu : exporter les données dans un fichier Excel, que Power BI lit depuis OneDrive.
*   Les données étant déjà générées, les CSV de la session 3 servent de source (ils sont identiques au contenu des tables PostgreSQL).

### 3. Préparation du fichier Excel
*   Installation de `openpyxl` dans le `venv` ; mise à jour de `requirements.txt` avec `pip freeze > requirements.txt`.
*   Création du script `to_excel.py` qui regroupe les trois CSV dans un seul fichier `ltpa_donnees.xlsx` (un onglet par table).
*   Choix techniques :
    *   `parse_dates` à la lecture des CSV, pour que les dates soient de vraies dates et non du texte ;
    *   chaque onglet est mis en forme de **tableau Excel** nommé (`etudiants`, `productions`, `interventions`), ce qui facilite la détection par Power BI ;
    *   affichage des dates au format `AAAA-MM-JJ`.
*   Vérification du fichier dans un tableur en ligne : trois onglets, tableaux filtrables, dates alignées à droite (donc reconnues comme dates), `Date_Fin` vide pour les étudiants actifs.

### 4. Import dans Power BI Service
*   Tentative d'import local (Importer > Rapport ou Classeur > Depuis cet ordinateur) : **refusée** par Power BI, qui n'accepte plus l'envoi de fichiers Excel depuis un dossier local.
*   Solution : téléversement de `ltpa_donnees.xlsx` dans le **OneDrive** du compte scolaire, à la racine de « My files ».
*   L'import via « Workbook » crée seulement un classeur consultable, pas un modèle de données. Le bon chemin est : **Create > Excel > Link to file > Browse OneDrive**.
*   Dans Power Query : sélection des trois éléments `etudiants`, `interventions` et `productions` (les versions sans chiffre ; les tableaux `etudiants1`, `interventions3`, `productions2` donnent le même contenu). Types détectés correctement (texte, nombre décimal, date).
*   Création du **modèle sémantique seul** (« Create a semantic model only ») nommé `LTPA_modele`.

### 5. Modélisation des relations
*   Relation `interventions[ID_Etudiant]` → `etudiants[ID_Etudiant]` détectée automatiquement par Power BI (même nom de colonne).
*   Relation `productions[ID_Etudiant_Responsable]` → `etudiants[ID_Etudiant]` créée manuellement (noms de colonnes différents, donc non détectée).
*   Réglages des deux relations : cardinalité **plusieurs à un (\*:1)**, filtre croisé **Single**, relations **actives**.
*   Résultat : un schéma en étoile, avec `etudiants` au centre et les deux tables d'activité autour.

### 6. Rapport `LTPA_dashboard`
*   Carte « Count of ID_Etudiant » : affiche **150**, ce qui confirme que le modèle lit bien tous les étudiants.
*   Graphique en barres « étudiants par département » (quatre barres dont le total fait 150).
*   Le filtrage croisé fonctionne : un clic sur une barre filtre la carte, et inversement.
*   Rapport enregistré dans « My workspace ».

### 7. Problèmes rencontrés & Solutions
*   **Problème :** la fenêtre de sélection de fichier du navigateur semblait vide.
    **Solution :** le filtre « All Supported Types » masquait les fichiers ; le passer sur « All files » les affiche.
*   **Problème :** « Power BI no longer supports the upload of Excel files from local folders ».
    **Solution :** passer par OneDrive.
*   **Problème :** l'élément `ltpa_donnees` de type *Workbook* ne permettait pas de créer de relations.
    **Solution :** créer un *Semantic model* depuis la page Create > Excel.
*   **Problème :** la relation entre `productions` et `etudiants` n'existait pas.
    **Solution :** création manuelle dans Manage relationships.
*   **Point d'attention :** l'aperçu Power Query affiche les dates au format américain (`2/21/2026` = 21 février 2026) ; les valeurs sont correctes.

### 8. À savoir
*   Le fichier Excel dans OneDrive est une **copie figée** des données : si les CSV sont régénérés, il faut renvoyer le fichier dans OneDrive puis actualiser le modèle.
*   Le modèle sémantique et le rapport sont stockés dans Power BI Service ; Docker n'est pas nécessaire pour les consulter.

### 9. Prochaines étapes
*   Graphique des productions par option, groupé par unité (ne jamais additionner des kg et des têtes).
*   Graphique des interventions par équipement et par type.
*   Répartition des étudiants par statut.
*   Segments (filtres) par département et par option.
*   Capture d'écran du tableau de bord dans `images/` pour le `README.md`.
*   Vérifier si le compte scolaire permet le partage du rapport (bouton *Share*) ; sinon, export PDF.

## Session 5 : Création du Dashboard Power BI

### 1. Contexte et Contraintes
*   Power BI Desktop n'étant pas disponible nativement sur Linux, l'outil **Power BI Service** (version web) a été utilisé via le compte étudiant.
*   La connexion directe à PostgreSQL (Docker) étant bloquée par la passerelle web, les données ont été consolidées dans un fichier Excel (`ltpa_donnees.xlsx`) déposé sur OneDrive.

### 2. Importation des données
*   Découverte de l'interface Power BI et tentative d'importation locale.
*   Résolution des problèmes de filtre de fichiers et contournement du blocage d'importation locale via OneDrive.

**Preuves visuelles - Importation :**
![PBI 01](images/pbi_01_accueil.png)
![PBI 02](images/pbi_02_menu_import.png)
![PBI 03](images/pbi_03_source_locale.png)
![PBI 04](images/pbi_04_bug_filtre.png)
![PBI 05](images/pbi_05_solution_filtre.png)
![PBI 06](images/pbi_06_erreur_locale.png)
![PBI 07](images/pbi_07_onedrive_upload.png)
![PBI 08](images/pbi_08_import_reussi.png)
![PBI 09](images/pbi_09_creation_modele.png)
![PBI 10](images/pbi_10_creation_rapport.png)
![PBI 11](images/pbi_11_connexion_onedrive.png)
![PBI 12](images/pbi_12_url_onedrive.png)

### 3. Transformation (Power Query)
*   Sélection des tables pertinentes pour éviter les doublons.
*   Vérification du typage des données (notamment les dates) et des étapes appliquées.

**Preuves visuelles - Power Query :**
![PBI 13](images/pbi_13_selection_tables.png)
![PBI 14](images/pbi_14_apercu_donnees.png)
![PBI 15](images/pbi_15_power_query_etapes.png)

### 4. Modélisation (Schéma en étoile)
*   Création du modèle sémantique `LTPA_modele`.
*   Création des relations 1-à-plusieurs (*:1) entre la table de faits (`etudiants`) et les tables de dimensions (`productions`, `interventions`).

**Preuves visuelles - Modélisation :**
![PBI 16](images/pbi_16_creation_modele_seul.png)
![PBI 17](images/pbi_17_nom_modele.png)
![PBI 18](images/pbi_18_schema_etoile.png)
![PBI 19](images/pbi_19_relations_powerbi.png)
![PBI 20](images/pbi_20_creation_relation_manuelle.png)
![PBI 21](images/pbi_21_relations_validees.png)
![PBI 22](images/pbi_22_schema_etoile.png)

### 5. Création des visuels et Dashboard
*   Création du rapport `LTPA_dashboard`.
*   Ajout de cartes KPI (ex: 150 étudiants) pour valider la connexion.
*   Ajout d'un graphique en barres pour la répartition des effectifs par département.

**Preuves visuelles - Visualisation :**
![PBI 23](images/pbi_23_page_blanche.png)
![PBI 24](images/pbi_24_choix_visuel_carte.png)
![PBI 25](images/pbi_25_selection_donnee.png)
![PBI 26](images/pbi_26_visuel_vide.png)
![PBI 27](images/pbi_27_kpi_150.png)
![PBI 28](images/pbi_28_sauvegarde_rapport.png)
![PBI 29](images/pbi_29_rapport_sauvegarde.png)
![PBI 30](images/pbi_30_dashboard_final.png)