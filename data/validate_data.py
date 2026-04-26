import pandas as pd
import numpy as np
import os

# TEST DE SURVIE IMMÉDIAT
print(">>> LE SCRIPT VIENT DE SE LANCER !")

def valider_donnees(file_path):
    # Vérifier si le fichier existe avant de commencer
    if not os.path.exists(file_path):
        print(f" ERREUR : Le fichier {file_path} est introuvable dans ce dossier.")
        return

    print(f"--- Démarrage de la validation : {file_path} ---")
    df = pd.read_csv(file_path)
    initial_rows = len(df)
    
    # 1. Suppression des doublons
    df = df.drop_duplicates()
    
    # 2. Nettoyage des types
    df['type'] = df['type'].astype(str).str.strip().str.lower()
    
    # 3. Détection des Outliers (IQR)
    def is_outlier(group):
        valeurs = group['montant_debit'] + group['montant_credit']
        Q1 = valeurs.quantile(0.25)
        Q3 = valeurs.quantile(0.75)
        IQR = Q3 - Q1
        return (valeurs < (Q1 - 1.5 * IQR)) | (valeurs > (Q3 + 1.5 * IQR))

    outlier_mask = df.groupby('num_compte', group_keys=False).apply(lambda x: is_outlier(x))
    
    df_outliers = df[outlier_mask]
    df_clean = df[~outlier_mask]

    # AFFICHAGE DU RAPPORT
    print("\n====================================")
    print(f"   RAPPORT DE VALIDATION SAP")
    print("====================================")
    print(f"Lignes brutes      : {initial_rows}")
    print(f"Lignes saines      : {len(df_clean)}")
    print(f"Anomalies isolées  : {len(df_outliers)}")
    print("====================================")
    
    # Sauvegarde
    df_clean.to_csv("historique_sap_CLEAN.csv", index=False)
    print(" Fichier 'historique_sap_CLEAN.csv' créé !")

# ON LANCE LA FONCTION DIRECTEMENT ICI
valider_donnees("historique_sap.csv")