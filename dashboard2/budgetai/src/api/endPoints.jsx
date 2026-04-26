import client from './client';
 
// // ── AUTH
// export const login    = (email, password) => client.post('/auth/login',    { email, password });
// export const register = (email, password, nom, role) => client.post('/auth/register', { email, password, nom, role });
// export const getMe    = () => client.get('/auth/me');
 
// export const getHealth   = () => client.get('/health');
// export const getAccounts = () => client.get('/accounts');

// export const predictBest = (account_code,year_target) => client.post('/predict/best',{account_code,year_target});
// export const predictAccount    = (account_code, year_target) => client.post('/predict/account',     { account_code, year_target });
// export const predictConsolidate= (year_target) => client.post('/predict/consolidate', { year_target });
// export const predictScenarios  = (year_target, variation_pct = 10) => client.post('/predict/scenarios', { year_target, variation_pct });
// export const getAlerts = (year_target) => client.get(`/alerts/${year_target}`);
//  export const exportExcel = (year_target, nb_annees_historique = 5) =>
//   client.post('/export/excel', { year_target, nb_annees_historique }, { responseType: 'blob' });
export async function login(payload) {
  const { data } = await client.post("/auth/login", payload);
  return data;
}

export async function healthCheck() {
  const { data } = await client.get("/health");
  return data;
}
export async function getAccounts(){
  const { data } = await client.get("/accounts");
  return data;
}
export async function consolidate({year_target,with_ia_comments = false}){
   const { data } = await client.post("/predict/consolidate", {
    year_target,
    with_ia_comments,
  });
  return data;
}


export async function predictBest({account_code,year_target}){
  const {data} = await client.post("/predict/best", {
    account_code,
    year_target,
  });
  return data;
}
export async function predictAccount({account_code,year_target,with_ia_comments=false}){
  const {data} = await client.post("/predict/account",{
    account_code,
    year_target,
    with_ia_comments,
  });
  return data;
}
export async function getAlerts(year_target){
  const { data } = await client.get(`/alerts/${year_target}`);
  return data;
}
