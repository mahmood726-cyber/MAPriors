// Browser-free numerical harness for map-priors.html.
//
// Loads the statistical <script> block from the single-file app into a Node
// `vm` context with a minimal chainable-Proxy DOM stub (the derive/ESS/power
// functions themselves never touch the DOM), then evaluates a battery of the
// pure statistical functions and prints the results as JSON on stdout.
//
// Consumed by tests/test_numerical.py, which pins these outputs to the
// committed baseline (tests/baseline_map_priors.json) and asserts a set of
// independently-derived numerical identities.
//
// Regenerate the baseline with:  node tests/js_harness.js > tests/baseline_map_priors.json

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'map-priors.html'), 'utf8');

const open = html.indexOf('<script>');
const close = html.lastIndexOf('</script>');
if (open < 0 || close < 0) throw new Error('could not locate <script> block');
let script = html.slice(open + '<script>'.length, close);

// Strip only the two trailing auto-run invocations that fire on page load and
// touch the DOM heavily. All function/const declarations remain intact; we call
// the pure statistical functions directly below.
script = script.replace(/\n\s*renderHeader\(\);/, '\n/* renderHeader() stripped for headless eval */');
script = script.replace(/\n\s*autoLoadDemo\(\);/, '\n/* autoLoadDemo() stripped for headless eval */');

// --- Minimal chainable DOM/browser stub -------------------------------------
function makeStub() {
  const fn = function () { return makeStub(); };
  return new Proxy(fn, {
    get(_t, prop) {
      if (prop === 'value') return '80';
      if (prop === 'textContent' || prop === 'innerHTML') return '';
      if (prop === 'checked') return false;
      if (prop === 'length') return 0;
      if (prop === 'style') return new Proxy({}, { get: () => '', set: () => true });
      if (prop === 'classList') return { add() {}, remove() {}, toggle() {}, contains() { return false; } };
      if (prop === 'dataset') return {};
      if (prop === Symbol.toPrimitive) return () => '';
      if (prop === 'then') return undefined; // not a thenable
      return makeStub();
    },
    set() { return true; },
    apply() { return makeStub(); },
  });
}

const documentStub = {
  getElementById: () => makeStub(),
  querySelector: () => makeStub(),
  querySelectorAll: () => [],
  createElement: () => makeStub(),
  createElementNS: () => makeStub(),
  addEventListener() {},
  removeEventListener() {},
  body: makeStub(),
  documentElement: makeStub(),
  head: makeStub(),
};

const sandbox = {
  document: documentStub,
  localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
  setTimeout: () => 0,
  clearTimeout: () => {},
  requestAnimationFrame: () => 0,
  console,
  Math, JSON, Date, parseInt, parseFloat, isFinite, isNaN,
  Array, Object, Number, String, Boolean, Infinity, NaN, undefined,
  Proxy, Symbol,
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.navigator = { userAgent: 'node' };
sandbox.location = { href: '' };

vm.createContext(sandbox);

// Test datasets injected into the app's own `studies` global.
const DS_CONT = [
  { trial: 'A', mean: 5.0, sd: 2.0, n: 100 },
  { trial: 'B', mean: 5.0, sd: 2.0, n: 100 },
];
const DS_CONT_HET = [
  { trial: 'A', mean: 4.0, sd: 1.5, n: 80 },
  { trial: 'B', mean: 6.5, sd: 2.1, n: 120 },
  { trial: 'C', mean: 5.2, sd: 1.8, n: 95 },
];
const DS_BIN = [
  { trial: 'A', events: 31, n: 154 },
  { trial: 'B', events: 18, n: 131 },
  { trial: 'C', events: 28, n: 163 },
];
const DS_BIN_ZERO = [
  { trial: 'A', events: 0, n: 100 },
  { trial: 'B', events: 5, n: 100 },
];
const DS_BIN_FULL = [
  { trial: 'A', events: 100, n: 100 },
  { trial: 'B', events: 95, n: 100 },
];

const driver = `
(function () {
  const out = {};

  // ---- pure math helpers (independently checkable) ----
  out.normalCDF_0 = normalCDF(0);
  out.normalCDF_196 = normalCDF(1.959963984540054);
  out.normalCDF_neg196 = normalCDF(-1.959963984540054);
  out.normalQuantile_975 = normalQuantile(0.975);
  out.normalQuantile_5 = normalQuantile(0.5);
  out.normalPDF_std0 = normalPDF(0, 0, 1);

  // moritaESSMixture at w=1 collapses to a pure normal: curvature = 1/var
  out.morita_w1 = moritaESSMixture(0, 0.25, 1.0, 0, 100);
  out.morita_w0 = moritaESSMixture(0, 0.25, 0.0, 0, 100);
  out.morita_mix = moritaESSMixture(0.3, 0.2, 0.8, 0, 100);

  // chi2CDF sanity
  out.chi2CDF_df1_x0 = chi2CDF(0, 1);
  out.chi2CDF_df1_x384 = chi2CDF(3.841458820694124, 1); // ~0.95

  // tteToLogHR exact (exponential + Parmar SE)
  out.tte = tteToLogHR(12, 100, 200);
  out.tte_events0 = tteToLogHR(12, 0, 200); // Math.max(1, events) guard

  // ---- deriveMAPContinuous ----
  studies = ${JSON.stringify(DS_CONT)};
  out.cont_homog = deriveMAPContinuous(0.8, 0.95);
  studies = ${JSON.stringify(DS_CONT_HET)};
  out.cont_het = deriveMAPContinuous(0.8, 0.95);
  out.cont_het_w0 = deriveMAPContinuous(0.0, 0.95);
  out.cont_het_w1 = deriveMAPContinuous(1.0, 0.95);

  // ---- deriveMAPBinary ----
  studies = ${JSON.stringify(DS_BIN)};
  mapResult = deriveMAPBinary(0.8, 0.95);
  out.bin = mapResult;
  out.power_bin = computePowerPrior(0.5);

  studies = ${JSON.stringify(DS_BIN_ZERO)};
  out.bin_zero = deriveMAPBinary(0.8, 0.95); // events=0 continuity correction

  studies = ${JSON.stringify(DS_BIN_FULL)};
  out.bin_full = deriveMAPBinary(0.8, 0.95); // events=n continuity correction

  return JSON.stringify(out);
})();
`;

try {
  vm.runInContext(script, sandbox, { filename: 'map-priors.app.js' });
} catch (e) {
  // Top-level const wrappers may reference DOM lazily; declarations are hoisted
  // regardless, so surface only if a target function ends up undefined.
  process.stderr.write('app-script warning: ' + e.message + '\n');
}

const result = vm.runInContext(driver, sandbox, { filename: 'driver.js' });
process.stdout.write(result);
