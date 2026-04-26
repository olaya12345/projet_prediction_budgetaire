import pandas as pd
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(DATA_DIR, "Classeur1_clean.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "data_for_ai.csv")

def creer_data_for_ai():
    print("=" * 60)
    print("CREATION DATA_FOR_AI.CSV")
    print("=" * 60)
    
    print("\n[1/4] Lecture des donnees nettoyees...")
    df = pd.read_csv(INPUT_FILE, parse_dates=['RefDate'])
    print(f"  Transactions: {len(df):,}")
    
    print("\n[2/4] Aggregation mensuelle par compte...")
    df_monthly = df.groupby(['annee', 'mois', 'num_compte', 'classe', 'type']).agg({
        'Debit': 'sum',
        'Credit': 'sum',
        'libelle': 'first'
    }).reset_index()
    
    df_monthly['montant_final'] = df_monthly.apply(
        lambda x: x['Debit'] - x['Credit'] if x['type'] == 'charge' else x['Credit'] - x['Debit'],
        axis=1
    )
    
    df_monthly['date'] = pd.to_datetime(
        df_monthly['annee'].astype(str) + '-' + df_monthly['mois'].astype(str) + '-01'
    )
    
    print(f"  Lignes monthly: {len(df_monthly):,}")
    
    print("\n[3/4] Preparation du format pour ML...")
    df_ai = df_monthly[['date', 'num_compte', 'libelle', 'classe', 'type', 'Debit', 'Credit', 'montant_final']].copy()
    df_ai = df_ai.rename(columns={'num_compte': 'account'})
    df_ai = df_ai.sort_values(['account', 'date']).reset_index(drop=True)
    
    df_ai['nom_compte'] = df_ai['account']
    
    print("\n[4/4] Sauvegarde...")
    df_ai.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"  [OK] Fichier: {OUTPUT_FILE}")
    
    print("\n" + "=" * 60)
    print("RESUME DATA_FOR_AI")
    print("=" * 60)
    print(f"  Total lignes: {len(df_ai):,}")
    print(f"  Comptes uniques: {df_ai['account'].nunique()}")
    print(f"  Classe 6: {(df_ai['classe'] == 6).sum():,} lignes")
    print(f"  Classe 7: {(df_ai['classe'] == 7).sum():,} lignes")
    print(f"  Annees: {sorted(df_ai['date'].dt.year.unique())}")
    print(f"  Periode: {df_ai['date'].min().date()} - {df_ai['date'].max().date()}")
    print(f"  Total montant_final: {df_ai['montant_final'].sum():,.2f} DH")
    print("=" * 60)
    
    print("\n--- Exemple comptes Classe 6 ---")
    cl6 = df_ai[df_ai['classe'] == 6].head(3)
    print(cl6[['date', 'account', 'type', 'Debit', 'Credit', 'montant_final']].to_string())
    
    print("\n--- Exemple comptes Classe 7 ---")
    cl7 = df_ai[df_ai['classe'] == 7].head(3)
    print(cl7[['date', 'account', 'type', 'Debit', 'Credit', 'montant_final']].to_string())
    
    return df_ai

if __name__ == "__main__":
    creer_data_for_ai()
