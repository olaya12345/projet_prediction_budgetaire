import pandas as pd
import os

def preparer_donnees_ia(input_file):
    print(f"--- Préparation des données pour l'IA : {input_file} ---")
    
    # 1. Chargement du fichier nettoyé
    if not os.path.exists(input_file):
        print(f"Erreur : {input_file} introuvable. As-tu lancé validate_data.py ?")
        return

    df = pd.read_csv(input_file)
    
    # 2. Conversion de la date
    df['date'] = pd.to_datetime(df['date'])
    
    # 3. Agrégation Mensuelle (Somme par mois et par compte)
    # On respecte la structure SAP : on groupe par mois, numéro de compte et nom
    df_mensuel = df.groupby([
        df['date'].dt.to_period('M'), 
        'num_compte', 
        'nom_compte', 
        'type'
    ]).agg({
        'montant_debit': 'sum',
        'montant_credit': 'sum'
    }).reset_index()

    # 4. Calcul du montant net (Requis pour les modèles de prédiction)
    # Dans ton cas, on va surtout prédire le débit (dépenses) ou crédit (produits)
    df_mensuel['montant_final'] = df_mensuel['montant_debit'] + df_mensuel['montant_credit']
    
    # Nettoyage du format de date pour le CSV final
    df_mensuel['date'] = df_mensuel['date'].dt.to_timestamp()
    
    # 5. Extraction des colonnes nécessaires pour le Intelligence Layer
    output_df = df_mensuel[['date', 'num_compte', 'nom_compte', 'type', 'montant_final']]
    
    # 6. Sauvegarde
    output_file = "data_for_ai.csv"
    output_df.to_csv(output_file, index=False)
    
    print("\n====================================")
    print(f"AGRÉGATION TERMINÉE")
    print(f"Lignes agrégées : {len(output_df)}")
    print(f"Fichier créé    : {output_file}")
    print("====================================")

if __name__ == "__main__":
    preparer_donnees_ia("historique_sap_CLEAN.csv")