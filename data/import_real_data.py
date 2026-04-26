import pandas as pd
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(DATA_DIR, "Classeur1.xlsx")
OUTPUT_FILE = os.path.join(DATA_DIR, "Classeur1_clean.csv")

def importer_donnees_reelles():
    print("=" * 60)
    print("IMPORTATION DES DONNÉES RÉELLES SAP")
    print("=" * 60)
    
    print("\n[1/5] Lecture du fichier Excel...")
    df = pd.read_excel(INPUT_FILE, header=1)
    
    print(f"  Lignes brutes: {len(df)}")
    print(f"  Colonnes: {df.columns.tolist()}")
    
    print("\n[2/5] Sélection et nettoyage des colonnes...")
    df = df[['RefDate', 'Account', 'Debit', 'Credit']].copy()
    df = df.dropna(subset=['RefDate'])
    
    df['RefDate'] = pd.to_datetime(df['RefDate'], dayfirst=True)
    df['Account'] = df['Account'].astype(str)
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    
    print(f"  Lignes après nettoyage: {len(df)}")
    
    print("\n[3/5] Classification des comptes (Classe 6 / Classe 7)...")
    df['classe'] = df['Account'].str[:1]
    
    df['type'] = df['classe'].apply(lambda x: 'charge' if x == '6' else 'produit' if x == '7' else 'autre')
    
    classe_counts = df.groupby('classe')['Account'].nunique()
    for c, count in classe_counts.items():
        print(f"  Classe {c}: {count} comptes uniques")
    
    print("\n[4/5] Ajout des colonnes complémentaires...")
    df['libelle'] = ''
    
    df['annee'] = df['RefDate'].dt.year
    df['mois'] = df['RefDate'].dt.month
    df['num_compte'] = df['Account']
    
    print(f"  Periode: {df['RefDate'].min().date()} - {df['RefDate'].max().date()}")
    print(f"  Total Débit: {df['Debit'].sum():,.2f} DH")
    print(f"  Total Crédit: {df['Credit'].sum():,.2f} DH")
    
    print("\n[5/5] Sauvegarde du fichier nettoyé...")
    df_export = df[['RefDate', 'num_compte', 'libelle', 'Debit', 'Credit', 'classe', 'type', 'annee', 'mois']].copy()
    df_export.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"  [OK] Fichier sauvegarde: {OUTPUT_FILE}")
    
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"  Total transactions: {len(df_export):,}")
    print(f"  Comptes Classe 6: {(df_export['classe'] == '6').sum():,}")
    print(f"  Comptes Classe 7: {(df_export['classe'] == '7').sum():,}")
    print(f"  Années disponibles: {sorted(df_export['annee'].unique())}")
    print("=" * 60)
    
    return df_export

if __name__ == "__main__":
    importer_donnees_reelles()
