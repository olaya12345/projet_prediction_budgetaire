import sys 
sys.path.insert(0, '.') 
from models.smart_average_model import calculer_budget_previsionnel 
r = calculer_budget_previsionnel('COMPTE_7111', year_target=2026) 
print(r.keys()) 
print(r.get('budget_annuel')) 
