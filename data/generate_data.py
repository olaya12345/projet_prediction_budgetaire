
import pandas as pd
import numpy as np
import random

random.seed(42)
np.random.seed(42)


COMPTES = [
    ("COMPTE_6011", "Achats matières premières",  85000,  "dépense"),
    ("COMPTE_6141", "Loyers",                      45000,  "dépense"),
    ("COMPTE_6161", "Assurances",                  12500,  "dépense"),
    ("COMPTE_6165", "Electricité et eau",           28000,  "dépense"),
    ("COMPTE_6171", "Transport et livraisons",      18000,  "dépense"),
    ("COMPTE_6174", "Téléphone et internet",         8500,  "dépense"),
    ("COMPTE_6176", "Honoraires consultants",       35000,  "dépense"),
    ("COMPTE_6178", "Fournitures de bureau",         6200,  "dépense"),
    ("COMPTE_6185", "Maintenance équipements",      22000,  "dépense"),
    ("COMPTE_6190", "Formation du personnel",       14000,  "dépense"),
    ("COMPTE_6200", "Salaires",                    320000,  "dépense"),
    ("COMPTE_6210", "Charges sociales CNSS",        89000,  "dépense"),
    ("COMPTE_7111", "Chiffre d affaires",          750000,  "produit"),
    ("COMPTE_7120", "Subventions reçues",           25000,  "produit"),
    ("COMPTE_7300", "Intérêts bancaires reçus",      8000,  "produit"),
]

# --- Saisonnalité par mois ---
SAISONNALITE = {
    1: 1.15, 2: 0.95, 3: 1.05, 4: 1.00,
    5: 1.02, 6: 0.97, 7: 0.85, 8: 0.80,
    9: 1.05, 10: 1.10, 11: 1.12, 12: 1.20,
}

# --- Générer les transactions ---
def generer_transactions():
    print("Démarrage de la génération des données...")

    lignes = []

    for annee in range(2016,2026):
        for mois in range(1, 13):
            for code, nom, montant_base, type_compte in COMPTES:

                # Calcul du montant réaliste
                facteur_annee = 1 + (0.04 * (annee - 2016))
                facteur_mois  = SAISONNALITE[mois]
                bruit         = random.uniform(0.85, 1.15)
                montant       = round(montant_base * facteur_annee * facteur_mois * bruit, 2)

                # Date aléatoire dans le mois
                jour = random.randint(1, 28)
                date = f"{annee}-{mois:02d}-{jour:02d}"

                # Remplir les colonnes debit/credit selon le type
                if type_compte == "dépense":
                    montant_debit  = montant
                    montant_credit = 0.0
                else:  # produit
                    montant_debit  = 0.0
                    montant_credit = montant

                lignes.append({
                    "date"           : date,
                    "num_compte"     : code,
                    "nom_compte"     : nom,
                    "type"           : type_compte,
                    "montant_debit"  : montant_debit,
                    "montant_credit" : montant_credit,
                })

    # Créer le DataFrame et trier par date
    df = pd.DataFrame(lignes)
    df = df.sort_values("date").reset_index(drop=True)

    print(f"  {len(df)} transactions générées.")
    print(f"  Période : {df['date'].min()} → {df['date'].max()}")
    print(f"  Comptes : {df['num_compte'].nunique()}")

    return df


# --- Sauvegarder en CSV ---
def sauvegarder(df):
    df.to_csv("historique_sap.csv", index=False, encoding="utf-8-sig")
    print(f"  Fichier sauvegardé : historique_sap.csv")


# --- Lancement ---
if __name__ == "__main__":
    df = generer_transactions()
    sauvegarder(df)
    print("Terminé !")