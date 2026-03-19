#!/usr/bin/env python
"""
Comprehensive Selenium test suite for MAP Priors & Dynamic Borrowing Engine.
Tests: Page Load, Data Input, MAP Prior Derivation, Robust MAP Slider,
       Phase 2 Features, Phase 3 Features, Export & Report.
"""
import sys
import io
import time
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
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
# Category 1: Page Load & UI (5 tests)
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

def test_03_data_table_renders(driver):
    tbody = driver.find_element(By.ID, "dataBody")
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    assert len(rows) == 3, f"Expected 3 empty rows, got {len(rows)}"

def test_04_robust_slider_default(driver):
    sl = driver.find_element(By.ID, "wSlider")
    assert sl.is_displayed(), "Robust MAP slider not found"
    val = sl.get_attribute("value")
    assert val == "80", f"Default slider value is {val}, expected 80"
    lbl = driver.find_element(By.ID, "wVal")
    assert "80%" in lbl.text, f"Slider label shows '{lbl.text}'"

def test_05_dark_mode_toggle(driver):
    body = driver.find_element(By.TAG_NAME, "body")
    assert "dark" not in body.get_attribute("class"), "Body starts in dark mode unexpectedly"
    driver.find_element(By.ID, "themeBtn").click()
    time.sleep(0.2)
    cls = body.get_attribute("class") or ""
    assert "dark" in cls, f"Dark mode not applied, class='{cls}'"
    # Toggle back
    driver.find_element(By.ID, "themeBtn").click()
    time.sleep(0.2)
    cls2 = body.get_attribute("class") or ""
    assert "dark" not in cls2, "Dark mode not toggled off"


# =========================================================================
# Category 2: Data Input (5 tests)
# =========================================================================

def test_06_load_crohns(driver):
    load_example(driver, "crohns")
    time.sleep(0.3)
    badge = driver.find_element(By.ID, "studyBadge")
    assert "8" in badge.text, f"Badge shows '{badge.text}', expected 8 studies"
    sel_val = driver.execute_script("return document.getElementById('endpointType').value")
    assert sel_val == "binary", f"Endpoint type is '{sel_val}'"

def test_07_load_uc(driver):
    load_example(driver, "uc")
    time.sleep(0.3)
    badge = driver.find_element(By.ID, "studyBadge")
    assert "6" in badge.text, f"Badge shows '{badge.text}', expected 6 studies"
    sel_val = driver.execute_script("return document.getElementById('endpointType').value")
    assert sel_val == "continuous", f"Endpoint type is '{sel_val}'"

def test_08_load_oncology(driver):
    load_example(driver, "onco")
    time.sleep(0.3)
    badge = driver.find_element(By.ID, "studyBadge")
    assert "5" in badge.text, f"Badge shows '{badge.text}', expected 5 studies"
    sel_val = driver.execute_script("return document.getElementById('endpointType').value")
    assert sel_val == "binary", f"Endpoint type is '{sel_val}'"

def test_09_dataset_dropdown_options(driver):
    dd_content = driver.find_element(By.ID, "exampleDropdown")
    btns = dd_content.find_elements(By.TAG_NAME, "button")
    assert len(btns) == 3, f"Expected 3 dataset options, got {len(btns)}"

def test_10_rate_auto_computes(driver):
    load_example(driver, "crohns")
    time.sleep(0.3)
    # First study: 15 events, 80 N => rate = 18.8%
    tbody = driver.find_element(By.ID, "dataBody")
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    rate_cell = rows[0].find_element(By.CSS_SELECTOR, '[data-f="rate"]')
    rate_text = rate_cell.text
    assert "18.8%" in rate_text, f"Rate cell shows '{rate_text}', expected '18.8%'"


# =========================================================================
# Category 3: MAP Prior Derivation (8 tests)
# =========================================================================

def test_11_crohns_map_mean(driver):
    load_example(driver, "crohns")
    derive_map(driver)
    # MAP prior mean on probability scale should be ~17-18%
    p_hat = driver.execute_script("return mapResult.p_hat")
    pct = p_hat * 100
    assert 15 <= pct <= 22, f"MAP prior mean = {pct:.1f}%, expected 15-22%"

def test_12_tau_small(driver):
    tau = driver.execute_script("return mapResult.tau")
    assert tau < 0.5, f"tau = {tau}, expected < 0.5 (low heterogeneity)"

def test_13_i2_low(driver):
    i2 = driver.execute_script("return mapResult.I2")
    assert i2 < 30, f"I2 = {i2:.1f}%, expected < 30%"

def test_14_ess_pure_map(driver):
    ess = driver.execute_script("return mapResult.ess_map")
    assert ess > 50, f"ESS (pure MAP) = {ess:.1f}, expected > 50"

def test_15_ess_robust(driver):
    ess_r = driver.execute_script("return mapResult.ess_robust")
    assert ess_r > 10, f"ESS (robust MAP w=80%) = {ess_r:.1f}, expected > 10"

def test_16_density_plot_svg(driver):
    container = driver.find_element(By.ID, "densityPlot")
    svgs = container.find_elements(By.TAG_NAME, "svg")
    assert len(svgs) >= 1, "No SVG found in density plot"

def test_17_forest_plot_svg(driver):
    container = driver.find_element(By.ID, "forestPlot")
    svgs = container.find_elements(By.TAG_NAME, "svg")
    assert len(svgs) >= 1, "No SVG found in forest plot"

def test_18_map_predictive_ci_contains_studies(driver):
    """MAP predictive CI should be wide enough to contain most study CIs."""
    result = driver.execute_script("""
        var r = mapResult;
        var z = 1.96;
        var mapLo = r.map_mu - z * r.map_se;
        var mapHi = r.map_mu + z * r.map_se;
        var contained = 0;
        for (var i = 0; i < r.yi.length; i++) {
            var yi = r.yi[i];
            if (yi >= mapLo && yi <= mapHi) contained++;
        }
        return { contained: contained, total: r.yi.length, mapLo: mapLo, mapHi: mapHi };
    """)
    # At least half the study point estimates should be within the MAP predictive CI
    ratio = result["contained"] / result["total"]
    assert ratio >= 0.5, (
        f"Only {result['contained']}/{result['total']} study means within MAP CI "
        f"[{result['mapLo']:.3f}, {result['mapHi']:.3f}]"
    )


# =========================================================================
# Category 4: Robust MAP Slider (3 tests)
# =========================================================================

def test_19_slider_100_ess(driver):
    """Moving slider to 100% -> ESS robust ~= ESS pure."""
    load_example(driver, "crohns")
    set_slider(driver, "wSlider", 100)
    derive_map(driver)
    ess_map = driver.execute_script("return mapResult.ess_map")
    ess_rob = driver.execute_script("return mapResult.ess_robust")
    ratio = ess_rob / ess_map if ess_map > 0 else 0
    assert ratio > 0.85, f"ESS ratio at w=100%: {ratio:.3f} (robust={ess_rob:.1f}, pure={ess_map:.1f})"

def test_20_slider_0_ess(driver):
    """Moving slider to 0% -> ESS robust is very small."""
    load_example(driver, "crohns")
    set_slider(driver, "wSlider", 0)
    derive_map(driver)
    ess_rob = driver.execute_script("return mapResult.ess_robust")
    assert ess_rob < 5, f"ESS robust at w=0%: {ess_rob:.1f}, expected < 5"

def test_21_slider_display_updates(driver):
    set_slider(driver, "wSlider", 65)
    lbl = driver.find_element(By.ID, "wVal").text
    assert "65%" in lbl, f"Slider label shows '{lbl}', expected '65%'"
    set_slider(driver, "wSlider", 30)
    lbl2 = driver.find_element(By.ID, "wVal").text
    assert "30%" in lbl2, f"Slider label shows '{lbl2}', expected '30%'"


# =========================================================================
# Category 5: Phase 2 Features (6 tests)
# =========================================================================

def test_22_power_prior_section(driver):
    load_example(driver, "crohns")
    set_slider(driver, "wSlider", 80)
    derive_map(driver)
    card = driver.find_element(By.ID, "powerPriorCard")
    assert card.is_displayed(), "Power prior card not visible"
    sl = driver.find_element(By.ID, "alpha0Slider")
    assert sl.is_displayed(), "alpha0 slider not found"

def test_23_comparison_table(driver):
    card = driver.find_element(By.ID, "comparisonCard")
    assert card.is_displayed(), "Comparison card not visible"
    content = driver.find_element(By.ID, "comparisonContent")
    table = content.find_element(By.CSS_SELECTOR, "table.comparison-table")
    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    assert len(rows) == 5, f"Expected 5 comparison rows, got {len(rows)}"
    # Check labels
    labels = [r.find_elements(By.TAG_NAME, "td")[0].text for r in rows]
    assert "Frequentist" in labels[0], f"Row 1 label: {labels[0]}"
    assert "MAP" in labels[1], f"Row 2 label: {labels[1]}"
    assert "Robust" in labels[2], f"Row 3 label: {labels[2]}"
    assert "Power" in labels[3], f"Row 4 label: {labels[3]}"
    assert "Commensurate" in labels[4], f"Row 5 label: {labels[4]}"

def test_24_sample_size_section(driver):
    card = driver.find_element(By.ID, "sampleSizeCard")
    assert card.is_displayed(), "Sample size card not visible"
    content = driver.find_element(By.ID, "sampleSizeContent")
    html = content.get_attribute("innerHTML")
    assert "Savings" in html or "savings" in html.lower(), "No savings text in sample size section"

def test_25_prior_data_conflict(driver):
    card = driver.find_element(By.ID, "pdcCard")
    assert card.is_displayed(), "Prior-data conflict card not visible"
    inp = driver.find_element(By.ID, "pdcObserved")
    assert inp.is_displayed(), "PDC observed input not found"

def test_26_oc_simulation_section(driver):
    card = driver.find_element(By.ID, "ocCard")
    assert card.is_displayed(), "OC card not visible"
    n_ctrl = driver.find_element(By.ID, "ocNCtrl")
    n_trt = driver.find_element(By.ID, "ocNTrt")
    n_sim = driver.find_element(By.ID, "ocNSim")
    assert n_ctrl.is_displayed(), "ocNCtrl input not found"
    assert n_trt.is_displayed(), "ocNTrt input not found"
    assert n_sim.is_displayed(), "ocNSim input not found"

def test_27_power_curve_section(driver):
    btn = driver.find_element(By.ID, "ocPowerCurveBtn")
    assert btn.is_displayed(), "Power curve button not found"
    plot = driver.find_element(By.ID, "ocPowerCurvePlot")
    assert plot is not None, "Power curve plot container not found"


# =========================================================================
# Category 6: Phase 3 Features (8 tests)
# =========================================================================

def test_28_commensurate_prior_section(driver):
    card = driver.find_element(By.ID, "commPriorCard")
    assert card.is_displayed(), "Commensurate prior card not visible"
    sl = driver.find_element(By.ID, "tauCommSlider")
    assert sl.is_displayed(), "tauComm slider not found"

def test_29_commensurate_in_comparison(driver):
    """Comparison table should have 5 rows (Freq, MAP, Robust, Power, Commensurate)."""
    content = driver.find_element(By.ID, "comparisonContent")
    table = content.find_element(By.CSS_SELECTOR, "table.comparison-table")
    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    assert len(rows) == 5, f"Expected 5 rows, got {len(rows)}"
    last_label = rows[4].find_elements(By.TAG_NAME, "td")[0].text
    assert "Commensurate" in last_label, f"Last row is '{last_label}'"

def test_30_animation_section(driver):
    card = driver.find_element(By.ID, "animCard")
    assert card.is_displayed(), "Animation card not visible"
    play_btn = driver.find_element(By.ID, "animPlayBtn")
    assert play_btn.is_displayed(), "Play button not found"
    assert play_btn.text.strip() in ("Play", "Pause"), f"Button text: '{play_btn.text}'"

def test_31_r_code_export_button(driver):
    """R code export button exists in header."""
    btns = driver.find_elements(By.CSS_SELECTOR, "header .hdr-btns button")
    texts = [b.text for b in btns]
    assert any("R Code" in t or "Export R" in t for t in texts), f"Button texts: {texts}"

def test_32_regulatory_report_button(driver):
    btns = driver.find_elements(By.CSS_SELECTOR, "header .hdr-btns button")
    texts = [b.text for b in btns]
    assert any("Regulatory" in t for t in texts), f"Button texts: {texts}"

def test_33_dataset_dropdown_3_options(driver):
    """Verify dropdown has exactly 3 dataset options."""
    dd = driver.find_element(By.ID, "exampleDropdown")
    btns = dd.find_elements(By.TAG_NAME, "button")
    assert len(btns) == 3, f"Expected 3 dataset options, got {len(btns)}"

def test_34_tau_comm_slider_updates_ess(driver):
    """Changing tauComm slider updates the ESS display in commensurate section."""
    set_slider(driver, "tauCommSlider", 20)
    time.sleep(0.3)
    content = driver.find_element(By.ID, "commPriorContent").get_attribute("innerHTML")
    assert "ESS" in content, "ESS not found in commensurate prior content"
    # Check that the ESS value changed when we move to a different tau
    set_slider(driver, "tauCommSlider", 150)
    time.sleep(0.3)
    content2 = driver.find_element(By.ID, "commPriorContent").get_attribute("innerHTML")
    assert "ESS" in content2, "ESS not found after slider change"
    # The content should differ (different tau -> different ESS)
    assert content != content2, "Commensurate content didn't change when slider moved"

def test_35_animation_play_clickable(driver):
    """Animation Play button is clickable without console errors."""
    errors_before = get_console_errors(driver)
    play_btn = driver.find_element(By.ID, "animPlayBtn")
    play_btn.click()
    time.sleep(1.5)
    # Let at least one frame render
    step_label = driver.find_element(By.ID, "animStepLabel").text
    assert "Step" in step_label or "Ready" in step_label, f"Step label: '{step_label}'"
    # Stop animation
    driver.execute_script("animReset()")
    time.sleep(0.3)
    errors_after = get_console_errors(driver)
    new_errors = [e for e in errors_after if e not in errors_before]
    assert len(new_errors) == 0, f"Console errors after Play: {new_errors}"


# =========================================================================
# Category 7: Export & Report (3 tests)
# =========================================================================

def test_36_export_report_button(driver):
    btns = driver.find_elements(By.CSS_SELECTOR, "header .hdr-btns button")
    texts = [b.text for b in btns]
    assert any("Export" in t or "CSV" in t for t in texts), f"Button texts: {texts}"

def test_37_r_code_export_exists(driver):
    btns = driver.find_elements(By.CSS_SELECTOR, "header .hdr-btns button")
    r_btn = [b for b in btns if "R Code" in b.text or "Export R" in b.text]
    assert len(r_btn) >= 1, "R code export button not found"

def test_38_export_buttons_clickable_no_errors(driver):
    """Both Export CSV and Export R Code buttons are clickable without console errors."""
    # We need mapResult to exist for these to work
    load_example(driver, "crohns")
    set_slider(driver, "wSlider", 80)
    derive_map(driver)
    errors_before = get_console_errors(driver)

    # Click Export CSV -- it triggers a download, no error expected
    driver.execute_script("exportReport()")
    time.sleep(0.5)

    # Export R Code -- also triggers a download
    driver.execute_script("exportRCode()")
    time.sleep(0.5)

    errors_after = get_console_errors(driver)
    new_severe = [e for e in errors_after if e not in errors_before]
    assert len(new_severe) == 0, f"Console errors after export: {new_severe}"


# =========================================================================
# Main
# =========================================================================

def main():
    print("=" * 70)
    print("MAP Priors & Dynamic Borrowing Engine -- Selenium Test Suite")
    print("=" * 70)

    driver = setup_driver()

    all_tests = [
        # Category 1: Page Load & UI
        ("1.1 Page title contains 'MAP Priors'", test_01_page_title),
        ("1.2 Endpoint type dropdown (Binary/Continuous)", test_02_endpoint_dropdown),
        ("1.3 Data table renders 3 empty rows", test_03_data_table_renders),
        ("1.4 Robust MAP slider default 80%", test_04_robust_slider_default),
        ("1.5 Dark mode toggle works", test_05_dark_mode_toggle),
        # Category 2: Data Input
        ("2.1 Load Crohn's -> 8 binary studies", test_06_load_crohns),
        ("2.2 Load UC -> 6 continuous studies", test_07_load_uc),
        ("2.3 Load Oncology -> 5 binary studies", test_08_load_oncology),
        ("2.4 Dataset dropdown has 3 options", test_09_dataset_dropdown_options),
        ("2.5 Rate auto-computes (18.8% for 15/80)", test_10_rate_auto_computes),
        # Category 3: MAP Prior Derivation
        ("3.1 Crohn's MAP prior mean ~17-18%", test_11_crohns_map_mean),
        ("3.2 tau is small (low heterogeneity)", test_12_tau_small),
        ("3.3 I2 < 30%", test_13_i2_low),
        ("3.4 ESS (pure MAP) is substantial", test_14_ess_pure_map),
        ("3.5 ESS (robust MAP w=80%) > 10", test_15_ess_robust),
        ("3.6 Prior density plot renders SVG", test_16_density_plot_svg),
        ("3.7 Forest plot renders SVG", test_17_forest_plot_svg),
        ("3.8 MAP predictive CI contains study CIs", test_18_map_predictive_ci_contains_studies),
        # Category 4: Robust MAP Slider
        ("4.1 Slider 100% -> ESS robust ~= ESS pure", test_19_slider_100_ess),
        ("4.2 Slider 0% -> ESS robust very small", test_20_slider_0_ess),
        ("4.3 Slider value display updates in real-time", test_21_slider_display_updates),
        # Category 5: Phase 2 Features
        ("5.1 Power prior section with alpha0 slider", test_22_power_prior_section),
        ("5.2 Comparison table: 5 approaches", test_23_comparison_table),
        ("5.3 Sample size determination section", test_24_sample_size_section),
        ("5.4 Prior-data conflict section", test_25_prior_data_conflict),
        ("5.5 OC simulation section with inputs", test_26_oc_simulation_section),
        ("5.6 Power curve section exists", test_27_power_curve_section),
        # Category 6: Phase 3 Features
        ("6.1 Commensurate prior with tauComm slider", test_28_commensurate_prior_section),
        ("6.2 Commensurate in comparison table (5 rows)", test_29_commensurate_in_comparison),
        ("6.3 Prior evolution animation section", test_30_animation_section),
        ("6.4 R code export button exists", test_31_r_code_export_button),
        ("6.5 Regulatory report button exists", test_32_regulatory_report_button),
        ("6.6 Dataset dropdown has 3 options", test_33_dataset_dropdown_3_options),
        ("6.7 tauComm slider updates ESS display", test_34_tau_comm_slider_updates_ess),
        ("6.8 Animation Play clickable no errors", test_35_animation_play_clickable),
        # Category 7: Export & Report
        ("7.1 Export report button exists", test_36_export_report_button),
        ("7.2 R code export button exists", test_37_r_code_export_exists),
        ("7.3 Export buttons clickable no console errors", test_38_export_buttons_clickable_no_errors),
    ]

    try:
        for name, fn in all_tests:
            run_test(name, fn, driver)
    finally:
        # Final console error check
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
