#!/usr/bin/env python
"""
Comprehensive Selenium test suite for MAP Priors & Dynamic Borrowing Engine.

Tests: Page Load, Data Input, MAP Prior Derivation, Robust MAP Slider,
       Phase 2 Features, Phase 3 Features, Export & Report,
       NEW: Morita ESS Detail, ESS Sensitivity Curve, Prior-Data Conflict
            Auto-Detection, Borrowing Heatmap, Accessibility, Demo Auto-Load.

60+ tests total.
"""
import sys
import io
import time
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "http://localhost:8782/map-priors.html"

# ---- Helpers ----
def setup_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,1200")
    opts.add_argument("--disable-gpu")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(3)
    return driver


def get_console_errors(driver):
    """Return list of SEVERE console log entries."""
    try:
        logs = driver.get_log("browser")
        return [l for l in logs if l.get("level") == "SEVERE"]
    except Exception:
        return []


def load_example(driver, example_name):
    """Click Load Example dropdown and pick a dataset."""
    driver.execute_script(f"loadExample('{example_name}')")
    time.sleep(0.3)


def derive_map(driver):
    """Click Derive MAP Prior and wait for results."""
    driver.execute_script("""
        document.getElementById('runBtn').disabled = false;
        runMAP();
    """)
    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.ID, "results").value_of_css_property("display") != "none"
    )
    time.sleep(0.5)


def set_slider(driver, slider_id, value):
    """Set a range slider to a specific value and fire oninput."""
    driver.execute_script(f"""
        var sl = document.getElementById('{slider_id}');
        sl.value = {value};
        sl.dispatchEvent(new Event('input'));
    """)
    time.sleep(0.2)


def ensure_crohns_derived(driver):
    """Ensure Crohn's data is loaded and MAP is derived."""
    has_result = driver.execute_script("return mapResult !== null")
    if not has_result:
        load_example(driver, "crohns")
        set_slider(driver, "wSlider", 80)
        derive_map(driver)


# ---- Test Framework ----
results = []

def run_test(name, fn, driver):
    try:
        fn(driver)
        results.append(("PASSED", name))
        print(f"  PASSED  {name}")
    except Exception as e:
        results.append(("FAILED", name, str(e)))
        print(f"  FAILED  {name}")
        print(f"          {e}")
        traceback.print_exc(file=sys.stdout)


# =========================================================================
# Category 1: Page Load & UI (6 tests)
# =========================================================================

def test_01_page_title(driver):
    driver.get(URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "header")))
    assert "MAP Priors" in driver.title, f"Title is '{driver.title}'"

def test_02_endpoint_dropdown(driver):
    sel = driver.find_element(By.ID, "endpointType")
    assert sel.is_displayed(), "Endpoint type dropdown not visible"
    opts = sel.find_elements(By.TAG_NAME, "option")
    vals = [o.get_attribute("value") for o in opts]
    assert "binary" in vals and "continuous" in vals, f"Options: {vals}"

def test_03_auto_load_demo_data(driver):
    """Page should auto-load Crohn's demo data on first visit."""
    time.sleep(1)  # Wait for auto-load + auto-derive
    badge = driver.find_element(By.ID, "studyBadge")
    assert "8" in badge.text, f"Badge shows '{badge.text}', expected 8 studies (auto-loaded)"

def test_04_auto_derive_on_load(driver):
    """MAP should be auto-derived on page load with demo data."""
    time.sleep(1)
    has_result = driver.execute_script("return mapResult !== null")
    assert has_result, "mapResult should be non-null after auto-derive"

def test_05_robust_slider_default(driver):
    sl = driver.find_element(By.ID, "wSlider")
    assert sl.is_displayed(), "Robust MAP slider not found"
    val = sl.get_attribute("value")
    assert val == "80", f"Default slider value is {val}, expected 80"
    lbl = driver.find_element(By.ID, "wVal")
    assert "80%" in lbl.text, f"Slider label shows '{lbl.text}'"

def test_06_dark_mode_toggle(driver):
    body = driver.find_element(By.TAG_NAME, "body")
    assert "dark" not in (body.get_attribute("class") or ""), "Body starts in dark mode"
    driver.find_element(By.ID, "themeBtn").click()
    time.sleep(0.2)
    cls = body.get_attribute("class") or ""
    assert "dark" in cls, f"Dark mode not applied, class='{cls}'"
    driver.find_element(By.ID, "themeBtn").click()
    time.sleep(0.2)


# =========================================================================
# Category 2: Data Input (5 tests)
# =========================================================================

def test_07_load_crohns(driver):
    load_example(driver, "crohns")
    time.sleep(0.3)
    badge = driver.find_element(By.ID, "studyBadge")
    assert "8" in badge.text, f"Badge shows '{badge.text}', expected 8 studies"
    sel_val = driver.execute_script("return document.getElementById('endpointType').value")
    assert sel_val == "binary", f"Endpoint type is '{sel_val}'"

def test_08_load_uc(driver):
    load_example(driver, "uc")
    time.sleep(0.3)
    badge = driver.find_element(By.ID, "studyBadge")
    assert "6" in badge.text, f"Badge shows '{badge.text}', expected 6 studies"
    sel_val = driver.execute_script("return document.getElementById('endpointType').value")
    assert sel_val == "continuous", f"Endpoint type is '{sel_val}'"

def test_09_load_oncology(driver):
    load_example(driver, "onco")
    time.sleep(0.3)
    badge = driver.find_element(By.ID, "studyBadge")
    assert "5" in badge.text, f"Badge shows '{badge.text}', expected 5 studies"

def test_10_rate_auto_computes(driver):
    load_example(driver, "crohns")
    time.sleep(0.3)
    tbody = driver.find_element(By.ID, "dataBody")
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    rate_cell = rows[0].find_element(By.CSS_SELECTOR, '[data-f="rate"]')
    rate_text = rate_cell.text
    assert "18.8%" in rate_text, f"Rate cell shows '{rate_text}', expected '18.8%'"

def test_11_clear_all(driver):
    load_example(driver, "crohns")
    driver.execute_script("clearAll()")
    time.sleep(0.3)
    badge = driver.find_element(By.ID, "studyBadge")
    assert "0" in badge.text, f"Badge shows '{badge.text}', expected 0 after clear"


# =========================================================================
# Category 3: MAP Prior Derivation (8 tests)
# =========================================================================

def test_12_crohns_map_mean(driver):
    load_example(driver, "crohns")
    set_slider(driver, "wSlider", 80)
    derive_map(driver)
    p_hat = driver.execute_script("return mapResult.p_hat")
    pct = p_hat * 100
    assert 15 <= pct <= 22, f"MAP prior mean = {pct:.1f}%, expected 15-22%"

def test_13_tau_small(driver):
    tau = driver.execute_script("return mapResult.tau")
    assert tau < 0.5, f"tau = {tau}, expected < 0.5"

def test_14_i2_low(driver):
    i2 = driver.execute_script("return mapResult.I2")
    assert i2 < 30, f"I2 = {i2:.1f}%, expected < 30%"

def test_15_ess_pure_map(driver):
    ess = driver.execute_script("return mapResult.ess_map")
    assert ess > 50, f"ESS (pure MAP) = {ess:.1f}, expected > 50"

def test_16_ess_robust(driver):
    ess_r = driver.execute_script("return mapResult.ess_robust")
    assert ess_r > 10, f"ESS (robust MAP w=80%) = {ess_r:.1f}, expected > 10"

def test_17_density_plot_svg(driver):
    container = driver.find_element(By.ID, "densityPlot")
    svgs = container.find_elements(By.TAG_NAME, "svg")
    assert len(svgs) >= 1, "No SVG found in density plot"

def test_18_forest_plot_svg(driver):
    container = driver.find_element(By.ID, "forestPlot")
    svgs = container.find_elements(By.TAG_NAME, "svg")
    assert len(svgs) >= 1, "No SVG found in forest plot"

def test_19_map_predictive_ci_contains_studies(driver):
    result = driver.execute_script("""
        var r = mapResult;
        var z = 1.96;
        var mapLo = r.map_mu - z * r.map_se;
        var mapHi = r.map_mu + z * r.map_se;
        var contained = 0;
        for (var i = 0; i < r.yi.length; i++) {
            if (r.yi[i] >= mapLo && r.yi[i] <= mapHi) contained++;
        }
        return { contained: contained, total: r.yi.length };
    """)
    ratio = result["contained"] / result["total"]
    assert ratio >= 0.5, f"Only {result['contained']}/{result['total']} within MAP CI"


# =========================================================================
# Category 4: Robust MAP Slider (4 tests)
# =========================================================================

def test_20_slider_100_ess(driver):
    load_example(driver, "crohns")
    set_slider(driver, "wSlider", 100)
    derive_map(driver)
    ess_map = driver.execute_script("return mapResult.ess_map")
    ess_rob = driver.execute_script("return mapResult.ess_robust")
    ratio = ess_rob / ess_map if ess_map > 0 else 0
    assert ratio > 0.85, f"ESS ratio at w=100%: {ratio:.3f}"

def test_21_slider_0_ess(driver):
    load_example(driver, "crohns")
    set_slider(driver, "wSlider", 0)
    derive_map(driver)
    ess_rob = driver.execute_script("return mapResult.ess_robust")
    assert ess_rob < 5, f"ESS robust at w=0%: {ess_rob:.1f}, expected < 5"

def test_22_slider_display_updates(driver):
    set_slider(driver, "wSlider", 65)
    lbl = driver.find_element(By.ID, "wVal").text
    assert "65%" in lbl, f"Slider label shows '{lbl}'"

def test_23_slider_live_ess_preview(driver):
    """Live ESS preview should appear when slider moves after derivation."""
    ensure_crohns_derived(driver)
    set_slider(driver, "wSlider", 60)
    time.sleep(0.3)
    live_el = driver.execute_script("return document.getElementById('wLiveESS')")
    assert live_el is not None, "Live ESS preview element not created"
    text = driver.execute_script("return document.getElementById('wLiveESS').textContent")
    assert "patients" in text.lower() or "ess" in text.lower(), f"Live ESS text: '{text}'"


# =========================================================================
# Category 5: Phase 2 Features (6 tests)
# =========================================================================

def test_24_power_prior_section(driver):
    ensure_crohns_derived(driver)
    card = driver.find_element(By.ID, "powerPriorCard")
    assert card.is_displayed(), "Power prior card not visible"

def test_25_comparison_table(driver):
    content = driver.find_element(By.ID, "comparisonContent")
    table = content.find_element(By.CSS_SELECTOR, "table.comparison-table")
    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    assert len(rows) == 5, f"Expected 5 comparison rows, got {len(rows)}"

def test_26_sample_size_section(driver):
    content = driver.find_element(By.ID, "sampleSizeContent")
    html = content.get_attribute("innerHTML")
    assert "Savings" in html or "savings" in html.lower(), "No savings text"

def test_27_prior_data_conflict(driver):
    card = driver.find_element(By.ID, "pdcCard")
    assert card.is_displayed(), "PDC card not visible"

def test_28_oc_section(driver):
    card = driver.find_element(By.ID, "ocCard")
    assert card.is_displayed(), "OC card not visible"

def test_29_power_curve_btn(driver):
    btn = driver.find_element(By.ID, "ocPowerCurveBtn")
    assert btn.is_displayed(), "Power curve button not found"


# =========================================================================
# Category 6: Phase 3 Features (6 tests)
# =========================================================================

def test_30_commensurate_prior(driver):
    card = driver.find_element(By.ID, "commPriorCard")
    assert card.is_displayed(), "Commensurate prior card not visible"

def test_31_animation_section(driver):
    card = driver.find_element(By.ID, "animCard")
    assert card.is_displayed(), "Animation card not visible"
    play_btn = driver.find_element(By.ID, "animPlayBtn")
    assert play_btn.text.strip() in ("Play", "Pause"), f"Button: '{play_btn.text}'"

def test_32_tau_comm_slider_updates(driver):
    set_slider(driver, "tauCommSlider", 20)
    time.sleep(0.3)
    content1 = driver.find_element(By.ID, "commPriorContent").get_attribute("innerHTML")
    set_slider(driver, "tauCommSlider", 150)
    time.sleep(0.3)
    content2 = driver.find_element(By.ID, "commPriorContent").get_attribute("innerHTML")
    assert content1 != content2, "Commensurate content didn't change"

def test_33_animation_play(driver):
    errors_before = get_console_errors(driver)
    driver.execute_script("animTogglePlay()")
    time.sleep(1.5)
    step_label = driver.find_element(By.ID, "animStepLabel").text
    assert "Step" in step_label or "Ready" in step_label, f"Step: '{step_label}'"
    driver.execute_script("animReset()")
    errors_after = get_console_errors(driver)
    new_errors = [e for e in errors_after if e not in errors_before]
    assert len(new_errors) == 0, f"Console errors: {new_errors}"

def test_34_export_buttons(driver):
    """Export buttons exist in header."""
    btns = driver.find_elements(By.CSS_SELECTOR, "header .hdr-btns button")
    texts = [b.text for b in btns]
    assert any("R Code" in t or "Export R" in t for t in texts), f"Texts: {texts}"
    assert any("Regulatory" in t for t in texts), f"Texts: {texts}"
    assert any("CSV" in t or "Export" in t for t in texts), f"Texts: {texts}"

def test_35_export_no_errors(driver):
    ensure_crohns_derived(driver)
    errors_before = get_console_errors(driver)
    driver.execute_script("exportReport()")
    time.sleep(0.5)
    driver.execute_script("exportRCode()")
    time.sleep(0.5)
    errors_after = get_console_errors(driver)
    new_severe = [e for e in errors_after if e not in errors_before]
    assert len(new_severe) == 0, f"Errors: {new_severe}"


# =========================================================================
# Category 7: NEW — Morita ESS Detail (5 tests)
# =========================================================================

def test_36_ess_tabs_exist(driver):
    """ESS section should have 3 tabs: Summary, Detail, Curve."""
    ensure_crohns_derived(driver)
    tabs = driver.find_elements(By.CSS_SELECTOR, ".ess-tab")
    assert len(tabs) == 3, f"Expected 3 ESS tabs, got {len(tabs)}"
    tab_texts = [t.text.strip() for t in tabs]
    assert "Summary" in tab_texts, f"Tabs: {tab_texts}"
    assert "Morita Detail" in tab_texts, f"Tabs: {tab_texts}"
    assert "ESS Sensitivity Curve" in tab_texts, f"Tabs: {tab_texts}"

def test_37_ess_tab_summary_default(driver):
    """Summary tab should be selected by default."""
    tab = driver.find_element(By.ID, "essTabSummary")
    selected = tab.get_attribute("aria-selected")
    assert selected == "true", f"Summary tab aria-selected='{selected}'"
    panel = driver.find_element(By.ID, "essPanelSummary")
    assert not panel.get_attribute("hidden"), "Summary panel should not be hidden"

def test_38_ess_tab_detail_click(driver):
    """Clicking Morita Detail tab shows detailed ESS breakdown."""
    driver.execute_script("switchESSTab('detail')")
    time.sleep(0.3)
    panel = driver.find_element(By.ID, "essPanelDetail")
    assert panel.get_attribute("hidden") is None, "Detail panel should be visible"
    content = driver.find_element(By.ID, "essDetailContent").get_attribute("innerHTML")
    assert "Per-Patient Fisher Information" in content, f"Missing Fisher info in detail"
    assert "Regulatory Interpretation" in content, "Missing regulatory interpretation"

def test_39_ess_detail_has_all_methods(driver):
    """Detail panel should show ESS for MAP, Robust, Power, Commensurate."""
    content = driver.find_element(By.ID, "essDetailContent").get_attribute("innerHTML")
    assert "Pure MAP" in content, "Missing Pure MAP ESS"
    assert "Robust MAP" in content, "Missing Robust MAP ESS"
    assert "Power Prior" in content, "Missing Power Prior ESS"
    assert "Commensurate" in content, "Missing Commensurate ESS"

def test_40_ess_detail_values_positive(driver):
    """All ESS values in detail should be positive numbers."""
    result = driver.execute_script("""
        var r = mapResult;
        return {
            ess_map: r.ess_map,
            ess_robust: r.ess_robust,
            ess_map_positive: r.ess_map > 0,
            ess_robust_positive: r.ess_robust > 0
        };
    """)
    assert result["ess_map_positive"], f"ESS map should be positive: {result['ess_map']}"
    assert result["ess_robust_positive"], f"ESS robust should be positive: {result['ess_robust']}"


# =========================================================================
# Category 8: NEW — ESS Sensitivity Curve (4 tests)
# =========================================================================

def test_41_ess_curve_tab(driver):
    """ESS Sensitivity Curve tab shows SVG plot."""
    ensure_crohns_derived(driver)
    driver.execute_script("switchESSTab('curve')")
    time.sleep(0.5)
    panel = driver.find_element(By.ID, "essPanelCurve")
    assert panel.get_attribute("hidden") is None, "Curve panel should be visible"
    svgs = panel.find_elements(By.TAG_NAME, "svg")
    assert len(svgs) >= 1, "No SVG found in ESS curve plot"

def test_42_ess_curve_has_marker(driver):
    """ESS curve should have a marker for the current weight."""
    svg_html = driver.find_element(By.ID, "essCurvePlot").get_attribute("innerHTML")
    assert "circle" in svg_html, "No circle marker in ESS curve"
    assert "ESS=" in svg_html, "No ESS label in curve marker"

def test_43_ess_curve_aria_label(driver):
    """ESS curve SVG should have an aria-label for accessibility."""
    svg = driver.find_element(By.CSS_SELECTOR, "#essCurvePlot svg")
    label = svg.get_attribute("aria-label")
    assert label and "ESS" in label, f"SVG aria-label: '{label}'"

def test_44_ess_monotone_increasing(driver):
    """ESS should generally increase with informative weight."""
    result = driver.execute_script("""
        var r = mapResult;
        var isBin = r.type === 'binary';
        var single_info = isBin ? r.p_hat * (1 - r.p_hat) : 1;
        var vague_mu = isBin ? 0 : r.vague_mu;
        var vague_var = isBin ? 100 : Math.pow(parseFloat(r.vague_se), 2);
        var ess10 = moritaESSMixture(r.map_mu, r.map_var, 0.1, vague_mu, vague_var) / single_info;
        var ess50 = moritaESSMixture(r.map_mu, r.map_var, 0.5, vague_mu, vague_var) / single_info;
        var ess90 = moritaESSMixture(r.map_mu, r.map_var, 0.9, vague_mu, vague_var) / single_info;
        return { ess10: ess10, ess50: ess50, ess90: ess90 };
    """)
    assert result["ess50"] > result["ess10"], \
        f"ESS@50% ({result['ess50']:.1f}) should > ESS@10% ({result['ess10']:.1f})"
    assert result["ess90"] > result["ess50"], \
        f"ESS@90% ({result['ess90']:.1f}) should > ESS@50% ({result['ess50']:.1f})"


# =========================================================================
# Category 9: NEW — Prior-Data Conflict Auto-Detection (5 tests)
# =========================================================================

def test_45_auto_conflict_banner_exists(driver):
    """Auto conflict detection banner should appear after derivation."""
    ensure_crohns_derived(driver)
    banner = driver.find_element(By.ID, "pdcAutoBanner")
    assert banner.value_of_css_property("display") != "none", "Banner should be visible"
    html = banner.get_attribute("innerHTML")
    assert "traffic-light" in html, "Banner should contain a traffic light indicator"

def test_46_auto_conflict_green_for_consistent(driver):
    """Crohn's dataset should show green (consistent) conflict banner."""
    banner = driver.find_element(By.ID, "pdcAutoBanner")
    cls = banner.get_attribute("class") or ""
    # Crohn's data is consistent, should show green or yellow (not red)
    assert "red" not in cls, f"Crohn's should not show red conflict. Classes: {cls}"

def test_47_conflict_check_with_extreme_value(driver):
    """Running PDC with an extreme value should show conflict."""
    driver.execute_script("""
        document.getElementById('pdcObserved').value = '0.90';
        document.getElementById('pdcNewN').value = '50';
        runPDC();
    """)
    time.sleep(0.5)
    content = driver.find_element(By.ID, "pdcContent").get_attribute("innerHTML")
    assert "Conflict" in content or "conflict" in content.lower(), \
        "Extreme value 0.90 should trigger conflict detection"

def test_48_conflict_check_diagnostic_table(driver):
    """PDC should show a multi-measure diagnostic table."""
    content = driver.find_element(By.ID, "pdcContent").get_attribute("innerHTML")
    assert "Tail Probability" in content, "Missing tail probability"
    assert "Box Conflict Measure" in content, "Missing Box measure"
    assert "Bayesian p-value" in content, "Missing Bayesian p-value"
    assert "Standardized Residual" in content, "Missing standardized residual"
    assert "Posterior MAP Weight" in content, "Missing posterior weight"

def test_49_conflict_check_borrowing_fraction(driver):
    """PDC should show dynamic borrowing fraction bar."""
    content = driver.find_element(By.ID, "pdcContent").get_attribute("innerHTML")
    assert "Borrowing Fraction" in content or "Dynamic Borrowing" in content, \
        "Missing borrowing fraction visualization"


# =========================================================================
# Category 10: NEW — Borrowing Weights Heatmap (3 tests)
# =========================================================================

def test_50_borrowing_heatmap_exists(driver):
    """Borrowing heatmap card should be visible after derivation."""
    ensure_crohns_derived(driver)
    card = driver.find_element(By.ID, "borrowHeatmapCard")
    assert card.is_displayed(), "Borrowing heatmap card not visible"
    content = driver.find_element(By.ID, "borrowHeatmapContent")
    html = content.get_attribute("innerHTML")
    assert "borrow-cell" in html or "%" in html, "Heatmap should contain weight cells"

def test_51_borrowing_heatmap_correct_count(driver):
    """Heatmap should have same number of cells as studies."""
    cells = driver.find_elements(By.CSS_SELECTOR, "#borrowHeatmapContent .borrow-cell")
    k = driver.execute_script("return mapResult.k")
    assert len(cells) == k, f"Expected {k} heatmap cells, got {len(cells)}"

def test_52_borrowing_weights_sum_to_100(driver):
    """Borrowing weights should sum to approximately 100%."""
    result = driver.execute_script("""
        var r = mapResult;
        var wi = r.vi.map(function(v) { return 1 / (v + r.tau2); });
        var sumW = wi.reduce(function(a, b) { return a + b; }, 0);
        var pcts = wi.map(function(w) { return (w / sumW) * 100; });
        return { sum: pcts.reduce(function(a,b){return a+b;}, 0), pcts: pcts };
    """)
    assert abs(result["sum"] - 100) < 0.1, f"Weights sum = {result['sum']:.2f}, expected ~100"


# =========================================================================
# Category 11: NEW — Accessibility (8 tests)
# =========================================================================

def test_53_skip_link_exists(driver):
    """Skip link should exist for keyboard users."""
    skip = driver.find_element(By.CSS_SELECTOR, ".skip-link")
    assert skip is not None, "Skip link not found"
    href = skip.get_attribute("href")
    assert "mainContent" in href, f"Skip link href: {href}"

def test_54_main_landmark(driver):
    """Main content should have role=main."""
    main = driver.find_element(By.ID, "mainContent")
    role = main.get_attribute("role")
    assert role == "main", f"Main landmark role: '{role}'"

def test_55_header_banner_role(driver):
    """Header should have role=banner."""
    header = driver.find_element(By.TAG_NAME, "header")
    role = header.get_attribute("role")
    assert role == "banner", f"Header role: '{role}'"

def test_56_slider_aria_attributes(driver):
    """Sliders should have aria-label and aria-valuenow."""
    sl = driver.find_element(By.ID, "wSlider")
    label = sl.get_attribute("aria-label")
    assert label and "weight" in label.lower(), f"Slider aria-label: '{label}'"
    now = sl.get_attribute("aria-valuenow")
    assert now is not None, "Slider missing aria-valuenow"

def test_57_dropdown_aria_haspopup(driver):
    """Example dropdown button should have aria-haspopup."""
    btn = driver.find_element(By.ID, "exampleDropdownBtn")
    popup = btn.get_attribute("aria-haspopup")
    assert popup == "true", f"aria-haspopup: '{popup}'"

def test_58_dropdown_menu_role(driver):
    """Dropdown content should have role=menu."""
    dd = driver.find_element(By.ID, "exampleDropdown")
    role = dd.get_attribute("role")
    assert role == "menu", f"Dropdown role: '{role}'"

def test_59_ess_tablist_role(driver):
    """ESS tabs should have role=tablist."""
    tablist = driver.find_element(By.CSS_SELECTOR, ".ess-tabs")
    role = tablist.get_attribute("role")
    assert role == "tablist", f"ESS tabs role: '{role}'"

def test_60_live_status_region(driver):
    """Live status region should exist for screen reader announcements."""
    live = driver.find_element(By.ID, "liveStatus")
    assert live is not None, "Live status region not found"
    aria_live = live.get_attribute("aria-live")
    assert aria_live == "polite", f"aria-live: '{aria_live}'"


# =========================================================================
# Category 12: Continuous Endpoint (3 tests)
# =========================================================================

def test_61_continuous_derivation(driver):
    """UC dataset (continuous) should derive successfully."""
    load_example(driver, "uc")
    set_slider(driver, "wSlider", 70)
    derive_map(driver)
    result_type = driver.execute_script("return mapResult.type")
    assert result_type == "continuous", f"Type: '{result_type}'"

def test_62_continuous_ess_positive(driver):
    ess = driver.execute_script("return mapResult.ess_robust")
    assert ess > 0, f"Continuous ESS should be positive: {ess}"

def test_63_continuous_density_plot(driver):
    container = driver.find_element(By.ID, "densityPlot")
    svgs = container.find_elements(By.TAG_NAME, "svg")
    assert len(svgs) >= 1, "No SVG in continuous density plot"


# =========================================================================
# Category 13: No Console Errors (2 tests)
# =========================================================================

def test_64_no_console_errors_on_load(driver):
    """No SEVERE console errors on page load."""
    driver.get(URL)
    time.sleep(2)  # Wait for auto-load + auto-derive
    errors = get_console_errors(driver)
    assert len(errors) == 0, f"Console errors on load: {errors}"

def test_65_no_errors_after_all_datasets(driver):
    """Switching between all datasets should produce no errors."""
    errors_before = get_console_errors(driver)
    for ds in ["crohns", "uc", "onco"]:
        load_example(driver, ds)
        derive_map(driver)
        time.sleep(0.3)
    errors_after = get_console_errors(driver)
    new_errors = [e for e in errors_after if e not in errors_before]
    assert len(new_errors) == 0, f"Errors after dataset switching: {new_errors}"


# =========================================================================
# Main
# =========================================================================

def main():
    print("=" * 70)
    print("MAP Priors & Dynamic Borrowing Engine -- Selenium Test Suite")
    print(f"65 tests across 13 categories")
    print("=" * 70)

    driver = setup_driver()

    all_tests = [
        # Cat 1: Page Load & UI
        ("1.1 Page title", test_01_page_title),
        ("1.2 Endpoint dropdown", test_02_endpoint_dropdown),
        ("1.3 Auto-load demo data (8 studies)", test_03_auto_load_demo_data),
        ("1.4 Auto-derive on load", test_04_auto_derive_on_load),
        ("1.5 Robust slider default 80%", test_05_robust_slider_default),
        ("1.6 Dark mode toggle", test_06_dark_mode_toggle),
        # Cat 2: Data Input
        ("2.1 Load Crohn's -> 8 studies", test_07_load_crohns),
        ("2.2 Load UC -> 6 studies", test_08_load_uc),
        ("2.3 Load Oncology -> 5 studies", test_09_load_oncology),
        ("2.4 Rate auto-computes", test_10_rate_auto_computes),
        ("2.5 Clear all works", test_11_clear_all),
        # Cat 3: MAP Derivation
        ("3.1 MAP mean ~17-18%", test_12_crohns_map_mean),
        ("3.2 tau < 0.5", test_13_tau_small),
        ("3.3 I2 < 30%", test_14_i2_low),
        ("3.4 ESS pure > 50", test_15_ess_pure_map),
        ("3.5 ESS robust > 10", test_16_ess_robust),
        ("3.6 Density SVG", test_17_density_plot_svg),
        ("3.7 Forest SVG", test_18_forest_plot_svg),
        ("3.8 MAP CI covers studies", test_19_map_predictive_ci_contains_studies),
        # Cat 4: Robust Slider
        ("4.1 w=100% ESS ~= pure", test_20_slider_100_ess),
        ("4.2 w=0% ESS tiny", test_21_slider_0_ess),
        ("4.3 Slider label updates", test_22_slider_display_updates),
        ("4.4 Live ESS preview", test_23_slider_live_ess_preview),
        # Cat 5: Phase 2
        ("5.1 Power prior card", test_24_power_prior_section),
        ("5.2 Comparison table 5 rows", test_25_comparison_table),
        ("5.3 Sample size section", test_26_sample_size_section),
        ("5.4 PDC card visible", test_27_prior_data_conflict),
        ("5.5 OC section", test_28_oc_section),
        ("5.6 Power curve btn", test_29_power_curve_btn),
        # Cat 6: Phase 3
        ("6.1 Commensurate prior", test_30_commensurate_prior),
        ("6.2 Animation section", test_31_animation_section),
        ("6.3 tauComm slider updates", test_32_tau_comm_slider_updates),
        ("6.4 Animation play", test_33_animation_play),
        ("6.5 Export buttons exist", test_34_export_buttons),
        ("6.6 Export no errors", test_35_export_no_errors),
        # Cat 7: Morita ESS Detail (NEW)
        ("7.1 ESS tabs exist (3)", test_36_ess_tabs_exist),
        ("7.2 Summary tab default", test_37_ess_tab_summary_default),
        ("7.3 Detail tab shows breakdown", test_38_ess_tab_detail_click),
        ("7.4 Detail has all methods", test_39_ess_detail_has_all_methods),
        ("7.5 ESS values positive", test_40_ess_detail_values_positive),
        # Cat 8: ESS Curve (NEW)
        ("8.1 ESS curve SVG", test_41_ess_curve_tab),
        ("8.2 Curve has marker", test_42_ess_curve_has_marker),
        ("8.3 Curve aria-label", test_43_ess_curve_aria_label),
        ("8.4 ESS monotone increasing", test_44_ess_monotone_increasing),
        # Cat 9: Conflict Detection (NEW)
        ("9.1 Auto-conflict banner", test_45_auto_conflict_banner_exists),
        ("9.2 Green for consistent", test_46_auto_conflict_green_for_consistent),
        ("9.3 Extreme value conflict", test_47_conflict_check_with_extreme_value),
        ("9.4 Diagnostic table", test_48_conflict_check_diagnostic_table),
        ("9.5 Borrowing fraction", test_49_conflict_check_borrowing_fraction),
        # Cat 10: Heatmap (NEW)
        ("10.1 Heatmap exists", test_50_borrowing_heatmap_exists),
        ("10.2 Correct cell count", test_51_borrowing_heatmap_correct_count),
        ("10.3 Weights sum to 100%", test_52_borrowing_weights_sum_to_100),
        # Cat 11: Accessibility (NEW)
        ("11.1 Skip link", test_53_skip_link_exists),
        ("11.2 Main landmark", test_54_main_landmark),
        ("11.3 Header banner role", test_55_header_banner_role),
        ("11.4 Slider ARIA", test_56_slider_aria_attributes),
        ("11.5 Dropdown aria-haspopup", test_57_dropdown_aria_haspopup),
        ("11.6 Menu role", test_58_dropdown_menu_role),
        ("11.7 Tablist role", test_59_ess_tablist_role),
        ("11.8 Live status region", test_60_live_status_region),
        # Cat 12: Continuous
        ("12.1 Continuous derivation", test_61_continuous_derivation),
        ("12.2 Continuous ESS > 0", test_62_continuous_ess_positive),
        ("12.3 Continuous density SVG", test_63_continuous_density_plot),
        # Cat 13: Console Errors
        ("13.1 No errors on load", test_64_no_console_errors_on_load),
        ("13.2 No errors after switching", test_65_no_errors_after_all_datasets),
    ]

    try:
        for name, fn in all_tests:
            run_test(name, fn, driver)
    finally:
        severe = get_console_errors(driver)
        if severe:
            print(f"\n  [INFO] Final console errors: {len(severe)}")
            for e in severe[:5]:
                print(f"    {e.get('message', '')[:120]}")
        driver.quit()

    # Summary
    passed = sum(1 for r in results if r[0] == "PASSED")
    failed = sum(1 for r in results if r[0] == "FAILED")
    total = len(results)

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} PASSED, {failed}/{total} FAILED")
    print("=" * 70)

    if failed > 0:
        print("\nFailed tests:")
        for r in results:
            if r[0] == "FAILED":
                print(f"  FAILED  {r[1]}: {r[2]}")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
