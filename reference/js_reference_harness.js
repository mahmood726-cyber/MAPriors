// js_reference_harness.js
// Ground-truth generator for the MAPriors Python reference implementation.
//
// The three functions below (normalPDF, normalQuantile, moritaESSMixture,
// deriveMAPBinary, deriveMAPContinuous) are copied VERBATIM from
// map-priors.html so the Python port in mappriors_ref.py can be locked
// against the exact numbers the browser app produces.
//
// If map-priors.html changes, re-run:  node reference/js_reference_harness.js
// and re-freeze reference/js_ground_truth.json. NEVER hand-edit the numbers.

'use strict';

// ---- verbatim from map-priors.html (normalPDF / normalQuantile) ----
function normalPDF(x, mu, sigma) {
  const z = (x - mu) / sigma;
  return Math.exp(-0.5 * z * z) / (sigma * Math.sqrt(2 * Math.PI));
}
function normalQuantile(p) {
  if (p <= 0) return -Infinity; if (p >= 1) return Infinity; if (p === 0.5) return 0;
  const a=[-3.969683028665376e1,2.209460984245205e2,-2.759285104469687e2,1.383577518672690e2,-3.066479806614716e1,2.506628277459239e0];
  const b=[-5.447609879822406e1,1.615858368580409e2,-1.556989798598866e2,6.680131188771972e1,-1.328068155288572e1];
  const c=[-7.784894002430293e-3,-3.223964580411365e-1,-2.400758277161838e0,-2.549732539343734e0,4.374664141464968e0,2.938163982698783e0];
  const d=[7.784695709041462e-3,3.224671290700398e-1,2.445134137142996e0,3.754408661907416e0];
  const pL=0.02425; let q,r;
  if(p<pL){q=Math.sqrt(-2*Math.log(p));return(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)}
  if(p<=1-pL){q=p-0.5;r=q*q;return(((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)}
  q=Math.sqrt(-2*Math.log(1-p));return-(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
}

// ---- verbatim from map-priors.html (moritaESSMixture) ----
function moritaESSMixture(mu_map, var_map, w, mu_vague, var_vague) {
  const se_map = Math.sqrt(var_map);
  const se_vague = Math.sqrt(var_vague);
  let mode = mu_map;
  for (let iter = 0; iter < 30; iter++) {
    const f1 = w * normalPDF(mode, mu_map, se_map);
    const f2 = (1-w) * normalPDF(mode, mu_vague, se_vague);
    const f = f1 + f2;
    if (f < 1e-300) break;
    const fp = -f1*(mode-mu_map)/var_map - f2*(mode-mu_vague)/var_vague;
    const fpp = f1*((mode-mu_map)**2/var_map - 1)/var_map
              + f2*((mode-mu_vague)**2/var_vague - 1)/var_vague;
    const wfpp = -f1/var_map + f1*(mode-mu_map)**2/(var_map*var_map)
               - f2/var_vague + f2*(mode-mu_vague)**2/(var_vague*var_vague);
    if (Math.abs(wfpp) < 1e-300) break;
    const step = fp / wfpp;
    mode -= step;
    if (Math.abs(step) < 1e-12) break;
  }
  const f1 = w * normalPDF(mode, mu_map, se_map);
  const f2 = (1-w) * normalPDF(mode, mu_vague, se_vague);
  const f = f1 + f2;
  if (f < 1e-300) return 1 / var_map;
  const fpp = f1*((mode-mu_map)**2/(var_map*var_map) - 1/var_map)
            + f2*((mode-mu_vague)**2/(var_vague*var_vague) - 1/var_vague);
  const fp = -f1*(mode-mu_map)/var_map - f2*(mode-mu_vague)/var_vague;
  const negCurv = -fpp/f + (fp/f)**2;
  return Math.max(0, negCurv);
}

// ---- verbatim from map-priors.html (deriveMAPBinary) ----
function deriveMAPBinary(studies, w, confLevel) {
  const k = studies.length;
  const yi = [], vi = [];
  for (const s of studies) {
    const e = s.events === 0 ? 0.5 : (s.events === s.n ? s.n - 0.5 : s.events);
    const p = e / s.n;
    const logitP = Math.log(p / (1 - p));
    const v = 1 / (s.n * p * (1 - p));
    yi.push(logitP);
    vi.push(v);
  }
  const wi = vi.map(v => 1/v);
  const sumW = wi.reduce((a,b) => a+b, 0);
  const mu_fe = wi.reduce((s,w,i) => s+w*yi[i], 0) / sumW;
  const Q = wi.reduce((s,w,i) => s+w*(yi[i]-mu_fe)**2, 0);
  const C = sumW - wi.reduce((s,w) => s+w*w, 0) / sumW;
  const tau2_dl = Math.max(0, (Q - (k-1)) / C);
  let tau2 = tau2_dl;
  for (let iter = 0; iter < 50; iter++) {
    const wi2 = vi.map(v => 1/(v+tau2));
    const sw2 = wi2.reduce((a,b)=>a+b,0);
    const mu = wi2.reduce((s,w,i)=>s+w*yi[i],0)/sw2;
    const wi3 = wi2.map(w=>w*w);
    const r2 = yi.map((y,i)=>(y-mu)**2);
    const dL = -0.5*wi2.reduce((s,w)=>s+w,0) + 0.5*wi3.reduce((s,w)=>s+w,0)/sw2
               + 0.5*wi3.reduce((s,w,i)=>s+w*r2[i],0);
    const sumW2 = wi3.reduce((s,w)=>s+w,0);
    const sumW3 = wi2.reduce((s,w)=>s+w*w*w,0);
    const ddL = 0.5*sumW2 - sumW3/sw2 + 0.5*(sumW2*sumW2)/(sw2*sw2);
    if (Math.abs(ddL) < 1e-15) break;
    const step = dL / ddL;
    tau2 = Math.max(0, tau2 + step);
    if (Math.abs(step) < 1e-10) break;
  }
  const wi_final = vi.map(v => 1/(v+tau2));
  const sw_final = wi_final.reduce((a,b)=>a+b,0);
  const mu_post = wi_final.reduce((s,w,i)=>s+w*yi[i],0)/sw_final;
  const se_mu = Math.sqrt(1/sw_final);
  const map_var = tau2 + se_mu * se_mu;
  const map_se = Math.sqrt(map_var);
  const vague_mu = 0;
  const vague_var = 100;
  const robust_mu = w * mu_post + (1 - w) * vague_mu;
  const robust_var = w * (map_var + mu_post * mu_post) + (1 - w) * (vague_var + vague_mu * vague_mu) - robust_mu * robust_mu;
  const robust_se = Math.sqrt(Math.max(0.001, robust_var));
  const p_hat = 1 / (1 + Math.exp(-mu_post));
  const single_info = p_hat * (1 - p_hat);
  const ess_map = (1 / map_var) / single_info;
  const ess_robust = moritaESSMixture(mu_post, map_var, w, vague_mu, vague_var) / single_info;
  const z = normalQuantile(1 - (1 - confLevel) / 2);
  return {
    type: 'binary',
    mu: mu_post, se_mu, tau2, tau: Math.sqrt(tau2),
    map_mu: mu_post, map_se, map_var,
    robust_mu, robust_se, robust_var,
    vague_mu, vague_se: Math.sqrt(vague_var),
    p_hat,
    map_lower_logit: mu_post - z * map_se,
    map_upper_logit: mu_post + z * map_se,
    robust_lower_logit: robust_mu - z * robust_se,
    robust_upper_logit: robust_mu + z * robust_se,
    ess_map, ess_robust,
    k, Q, I2: Q > (k-1) ? Math.max(0, (Q-(k-1))/Q*100) : 0,
    w, confLevel
  };
}

// ---- verbatim from map-priors.html (deriveMAPContinuous) ----
function deriveMAPContinuous(studies, w, confLevel) {
  const k = studies.length;
  const yi = studies.map(s => s.mean);
  const vi = studies.map(s => (s.sd * s.sd) / s.n);
  const wi = vi.map(v => 1/v);
  const sumW = wi.reduce((a,b)=>a+b,0);
  const mu_fe = wi.reduce((s,w,i)=>s+w*yi[i],0)/sumW;
  const Q = wi.reduce((s,w,i)=>s+w*(yi[i]-mu_fe)**2,0);
  const C = sumW - wi.reduce((s,w)=>s+w*w,0)/sumW;
  let tau2 = Math.max(0, (Q-(k-1))/C);
  for (let iter = 0; iter < 50; iter++) {
    const wi2 = vi.map(v=>1/(v+tau2));
    const sw2 = wi2.reduce((a,b)=>a+b,0);
    const mu = wi2.reduce((s,w,i)=>s+w*yi[i],0)/sw2;
    const wi3 = wi2.map(w=>w*w);
    const r2 = yi.map((y,i)=>(y-mu)**2);
    const dL = -0.5*wi2.reduce((s,w)=>s+w,0) + 0.5*wi3.reduce((s,w)=>s+w,0)/sw2 + 0.5*wi3.reduce((s,w,i)=>s+w*r2[i],0);
    const sumW2 = wi3.reduce((s,w)=>s+w,0);
    const sumW3 = wi2.reduce((s,w)=>s+w*w*w,0);
    const ddL = 0.5*sumW2 - sumW3/sw2 + 0.5*(sumW2*sumW2)/(sw2*sw2);
    if (Math.abs(ddL)<1e-15) break;
    tau2 = Math.max(0, tau2 + dL/ddL);
    if (Math.abs(dL/ddL)<1e-10) break;
  }
  const wi_f = vi.map(v=>1/(v+tau2));
  const sw_f = wi_f.reduce((a,b)=>a+b,0);
  const mu_post = wi_f.reduce((s,w,i)=>s+w*yi[i],0)/sw_f;
  const se_mu = Math.sqrt(1/sw_f);
  const map_var = tau2 + se_mu*se_mu;
  const map_se = Math.sqrt(map_var);
  const grand_sd = Math.sqrt(vi.reduce((s,v)=>s+v,0)/k) * 10;
  const vague_mu = 0;
  const vague_var = grand_sd * grand_sd;
  const robust_mu = w*mu_post + (1-w)*vague_mu;
  const robust_var = w*(map_var + mu_post*mu_post) + (1-w)*(vague_var+vague_mu*vague_mu) - robust_mu*robust_mu;
  const robust_se = Math.sqrt(Math.max(0.001, robust_var));
  const avg_sigma2 = studies.reduce((s,st) => s + st.sd * st.sd, 0) / k;
  const single_info_cont = 1 / avg_sigma2;
  const ess_map = (1/map_var) / single_info_cont;
  const ess_robust = moritaESSMixture(mu_post, map_var, w, vague_mu, vague_var) / single_info_cont;
  const z = normalQuantile(1-(1-confLevel)/2);
  return {
    type: 'continuous',
    mu: mu_post, se_mu, tau2, tau: Math.sqrt(tau2),
    map_mu: mu_post, map_se, map_var,
    robust_mu, robust_se, robust_var,
    vague_mu, vague_se: Math.sqrt(vague_var),
    map_lower: mu_post - z*map_se, map_upper: mu_post + z*map_se,
    robust_lower: robust_mu - z*robust_se, robust_upper: robust_mu + z*robust_se,
    ess_map, ess_robust,
    k, Q, I2: Q>(k-1) ? Math.max(0,(Q-(k-1))/Q*100) : 0,
    w, confLevel
  };
}

// ---- built-in datasets (verbatim from DEMO_DATASETS) ----
const DATASETS = {
  crohns: { type: 'binary', data: [
    { trial: 'Study A (2002)', events: 15, n: 80 },
    { trial: 'Study B (2004)', events: 22, n: 120 },
    { trial: 'Study C (2005)', events: 18, n: 95 },
    { trial: 'Study D (2007)', events: 25, n: 150 },
    { trial: 'Study E (2008)', events: 12, n: 70 },
    { trial: 'Study F (2010)', events: 30, n: 175 },
    { trial: 'Study G (2011)', events: 20, n: 110 },
    { trial: 'Study H (2013)', events: 28, n: 160 },
  ]},
  uc: { type: 'continuous', data: [
    { trial: 'ACT-1 (2005)', mean: 5.2, sd: 2.1, n: 121 },
    { trial: 'ACT-2 (2005)', mean: 4.8, sd: 2.3, n: 123 },
    { trial: 'GEMINI 1 (2013)', mean: 5.5, sd: 1.9, n: 149 },
    { trial: 'OCTAVE 1 (2018)', mean: 5.1, sd: 2.0, n: 112 },
    { trial: 'UNIFI (2019)', mean: 4.9, sd: 2.2, n: 189 },
    { trial: 'ELEVATE (2022)', mean: 5.3, sd: 1.8, n: 158 },
  ]},
  onco: { type: 'binary', data: [
    { trial: 'Keynote-024 ctrl (2016)', events: 31, n: 154 },
    { trial: 'Checkmate-078 ctrl (2018)', events: 18, n: 131 },
    { trial: 'Impower-110 ctrl (2020)', events: 28, n: 163 },
    { trial: 'Rationale-301 ctrl (2022)', events: 24, n: 152 },
    { trial: 'JUPITER-02 ctrl (2021)', events: 21, n: 140 },
  ]},
};

function derive(ds, w, confLevel) {
  return ds.type === 'binary'
    ? deriveMAPBinary(ds.data, w, confLevel)
    : deriveMAPContinuous(ds.data, w, confLevel);
}

// Emit ground truth for each dataset across a grid of robust weights.
const weights = [0.0, 0.25, 0.5, 0.8, 1.0];
const confLevel = 0.95;
const out = {};
for (const name of Object.keys(DATASETS)) {
  out[name] = { type: DATASETS[name].type, weights: {} };
  for (const w of weights) {
    out[name].weights[w.toFixed(2)] = derive(DATASETS[name], w, confLevel);
  }
}
process.stdout.write(JSON.stringify(out, null, 2) + '\n');
