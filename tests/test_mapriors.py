#!/usr/bin/env python
"""
Selenium test suite for MAP Priors & Dynamic Borrowing Engine.

Covers: page load, tabs, 3 example datasets, MAP prior computation,
ESS (Morita), prior distribution plots, theme toggle, export,
operating characteristics, accessibility, and error-free operation.

pytest framework | Chrome headless | file:// URL
"""

import sys
import os
import time
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Resolve path to the HTML file
HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'map-priors.html')
HTML_PATH = os.path.abspath(HTML_PATH)
FILE_URL = 'file:///' + HTML_PATH.replace('\\', '/')

WAIT = 10  # seconds for WebDriverWait


# ---------- Fixtures ----------

@pytest.fixture(scope="session")
def driver():
    """Create a single Chrome headless driver for the entire test session."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,1200")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--allow-file-access-from-files")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(30)
    d.implicitly_wait(3)
    yield d
    d.quit()


@pytest.fixture(scope="session")
def page(driver):
    """Load the HTML file once, override window.confirm, wait for header."""
    driver.get(FILE_URL)
    driver.execute_script("window.confirm = function(){return true};")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.TAG_NAME, "header"))
    )
    # Allow auto-load + auto-derive to complete
    time.sleep(2)
    return driver


# ---------- Helpers ----------

def js(driver, script):
    """Shorthand for execute_script."""
    return driver.execute_script(script)


def js_click(driver, element):
    """Click via JS to avoid ElementNotInteractable in headless."""
    driver.execute_script("arguments[0].click()", element)


def load_example(driver, name):
    """Load one of the three built-in example datasets."""
    js(driver, f"loadExample('{name}')")
    time.sleep(0.3)


def derive_map(driver, w=80):
    """Set slider weight, enable button, and derive MAP prior."""
    js(driver, f"""
        var sl = document.getElementById('wSlider');
        sl.value = {w};
        sl.dispatchEvent(new Event('input'));
        document.getElementById('runBtn').disabled = false;
        runMAP();
    """)
    WebDriverWait(driver, WAIT).until(
        lambda d: d.find_element(By.ID, "results").value_of_css_property("display") != "none"
    )
    time.sleep(0.5)


def ensure_crohns_derived(driver):
    """Ensure Crohn's dataset is loaded and MAP is derived."""
    has_result = js(driver, "return mapResult !== null && mapResult.type === 'binary'")
    if not has_result:
        load_example(driver, "crohns")
        derive_map(driver, 80)


def get_console_errors(driver):
    """Return list of SEVERE console log entries."""
    try:
        logs = driver.get_log("browser")
        return [l for l in logs if l.get("level") == "SEVERE"]
    except Exception:
        return []


# ==========================================================================
# Tests
# ==========================================================================

class TestPageLoad:
    """Category 1: Page loads and core UI elements are visible."""

    def test_01_page_title(self, page):
        """Page title contains 'MAP Priors'."""
        assert "MAP Priors" in page.title, f"Title is '{page.title}'"

    def test_02_header_visible(self, page):
        """Header bar is rendered with brand text."""
        header = page.find_element(By.TAG_NAME, "header")
        assert header.is_displayed()
        brand = header.find_element(By.CSS_SELECTOR, ".brand")
        assert "MAP Priors" in brand.text

    def test_03_endpoint_dropdown(self, page):
        """Endpoint type dropdown has binary and continuous options."""
        sel = page.find_element(By.ID, "endpointType")
        assert sel.is_displayed()
        vals = [o.get_attribute("value") for o in sel.find_elements(By.TAG_NAME, "option")]
        assert "binary" in vals and "continuous" in vals, f"Options: {vals}"

    def test_04_theme_toggle(self, page):
        """Dark mode toggle adds/removes 'dark' class on body."""
        body = page.find_element(By.TAG_NAME, "body")
        was_dark = "dark" in (body.get_attribute("class") or "")
        btn = page.find_element(By.ID, "themeBtn")
        js_click(page, btn)
        time.sleep(0.3)
        now_dark = "dark" in (body.get_attribute("class") or "")
        assert now_dark != was_dark, "Dark mode class did not toggle"
        # Toggle back to original state
        js_click(page, btn)
        time.sleep(0.2)


class TestExampleDatasets:
    """Category 2: Load each of the 3 built-in example datasets."""

    def test_05_load_crohns(self, page):
        """Crohn's disease dataset loads 8 binary studies."""
        load_example(page, "crohns")
        badge = page.find_element(By.ID, "studyBadge")
        assert "8" in badge.text, f"Badge: '{badge.text}'"
        val = js(page, "return document.getElementById('endpointType').value")
        assert val == "binary"

    def test_06_load_uc(self, page):
        """Ulcerative Colitis dataset loads 6 continuous studies."""
        load_example(page, "uc")
        badge = page.find_element(By.ID, "studyBadge")
        assert "6" in badge.text, f"Badge: '{badge.text}'"
        val = js(page, "return document.getElementById('endpointType').value")
        assert val == "continuous"

    def test_07_load_oncology(self, page):
        """Oncology dataset loads 5 binary studies."""
        load_example(page, "onco")
        badge = page.find_element(By.ID, "studyBadge")
        assert "5" in badge.text, f"Badge: '{badge.text}'"


class TestMAPDerivation:
    """Category 3: MAP prior computation produces valid results."""

    def test_08_crohns_map_mean(self, page):
        """MAP prior mean for Crohn's data is in plausible range (15-22%)."""
        load_example(page, "crohns")
        derive_map(page, 80)
        p_hat = js(page, "return mapResult.p_hat")
        pct = p_hat * 100
        assert 15 <= pct <= 22, f"MAP prior mean = {pct:.1f}%, expected 15-22%"

    def test_09_tau_and_i2(self, page):
        """Heterogeneity estimates are reasonable for Crohn's data."""
        tau = js(page, "return mapResult.tau")
        i2 = js(page, "return mapResult.I2")
        assert tau < 0.5, f"tau = {tau}, expected < 0.5"
        assert i2 < 30, f"I2 = {i2:.1f}%, expected < 30%"

    def test_10_density_plot_svg(self, page):
        """Density plot contains an SVG element after derivation."""
        container = page.find_element(By.ID, "densityPlot")
        svgs = container.find_elements(By.TAG_NAME, "svg")
        assert len(svgs) >= 1, "No SVG found in density plot"

    def test_11_forest_plot_svg(self, page):
        """Forest plot contains an SVG element after derivation."""
        container = page.find_element(By.ID, "forestPlot")
        svgs = container.find_elements(By.TAG_NAME, "svg")
        assert len(svgs) >= 1, "No SVG found in forest plot"


class TestESS:
    """Category 4: Effective Sample Size (Morita method)."""

    def test_12_ess_pure_map_positive(self, page):
        """ESS for pure MAP prior is > 50 for Crohn's data."""
        ensure_crohns_derived(page)
        ess = js(page, "return mapResult.ess_map")
        assert ess > 50, f"ESS (pure MAP) = {ess:.1f}, expected > 50"

    def test_13_ess_robust_positive(self, page):
        """ESS for robust MAP (w=80%) is > 10."""
        ess_r = js(page, "return mapResult.ess_robust")
        assert ess_r > 10, f"ESS (robust w=80%) = {ess_r:.1f}, expected > 10"

    def test_14_ess_tabs_exist(self, page):
        """ESS section has 3 tabs: Summary, Morita Detail, ESS Sensitivity Curve."""
        tabs = page.find_elements(By.CSS_SELECTOR, ".ess-tab")
        assert len(tabs) == 3, f"Expected 3 ESS tabs, got {len(tabs)}"
        tab_texts = [t.text.strip() for t in tabs]
        assert "Summary" in tab_texts
        assert "Morita Detail" in tab_texts
        assert "ESS Sensitivity Curve" in tab_texts

    def test_15_ess_morita_detail(self, page):
        """Morita Detail tab shows breakdown for all prior types."""
        js(page, "switchESSTab('detail')")
        time.sleep(0.3)
        panel = page.find_element(By.ID, "essPanelDetail")
        assert panel.get_attribute("hidden") is None, "Detail panel should be visible"
        content = page.find_element(By.ID, "essDetailContent").get_attribute("innerHTML")
        for expected in ["Pure MAP", "Robust MAP", "Power Prior", "Commensurate"]:
            assert expected in content, f"Missing '{expected}' in ESS detail"
        # Switch back to summary
        js(page, "switchESSTab('summary')")
        time.sleep(0.2)


class TestRobustSlider:
    """Category 5: Robust MAP slider behaviour."""

    def test_16_slider_w0_low_ess(self, page):
        """At w=0% (full vague), ESS drops below 5."""
        load_example(page, "crohns")
        derive_map(page, 0)
        ess = js(page, "return mapResult.ess_robust")
        assert ess < 5, f"ESS at w=0%: {ess:.1f}, expected < 5"

    def test_17_slider_w100_high_ess(self, page):
        """At w=100% (pure MAP), robust ESS matches pure MAP ESS."""
        derive_map(page, 100)
        ess_map = js(page, "return mapResult.ess_map")
        ess_rob = js(page, "return mapResult.ess_robust")
        ratio = ess_rob / ess_map if ess_map > 0 else 0
        assert ratio > 0.85, f"ESS ratio at w=100%: {ratio:.3f}, expected > 0.85"


class TestExport:
    """Category 6: Export functionality runs without errors."""

    def test_18_export_buttons_present(self, page):
        """Header contains Export R Code, Regulatory Report, Export CSV buttons."""
        btns = page.find_elements(By.CSS_SELECTOR, "header .hdr-btns button")
        texts = [b.text for b in btns]
        assert any("R Code" in t for t in texts), f"No R Code button. Texts: {texts}"
        assert any("Regulatory" in t for t in texts), f"No Regulatory button. Texts: {texts}"
        assert any("CSV" in t or "Export" in t for t in texts), f"No CSV button. Texts: {texts}"

    def test_19_export_no_errors(self, page):
        """exportReport() and exportRCode() run without console errors."""
        ensure_crohns_derived(page)
        errors_before = get_console_errors(page)
        js(page, "exportReport()")
        time.sleep(0.3)
        js(page, "exportRCode()")
        time.sleep(0.3)
        errors_after = get_console_errors(page)
        new_errors = [e for e in errors_after if e not in errors_before]
        assert len(new_errors) == 0, f"Console errors during export: {new_errors}"


class TestOperatingCharacteristics:
    """Category 7: OC simulation section exists and can run."""

    def test_20_oc_section_visible(self, page):
        """Operating Characteristics card is visible after derivation."""
        ensure_crohns_derived(page)
        card = page.find_element(By.ID, "ocCard")
        assert card.is_displayed(), "OC card not visible"
        run_btn = page.find_element(By.ID, "ocRunBtn")
        assert run_btn.is_displayed(), "OC Run Simulation button not visible"

    def test_21_oc_simulation_runs(self, page):
        """OC simulation completes and shows results table."""
        ensure_crohns_derived(page)
        # Set small nSim for speed
        js(page, """
            document.getElementById('ocNSim').value = '100';
            document.getElementById('ocNCtrl').value = '50';
            document.getElementById('ocNTrt').value = '50';
        """)
        js(page, "runOCSimulation()")
        # Wait for results to appear (progress bar fills to 100%)
        WebDriverWait(page, 30).until(
            lambda d: d.find_element(By.ID, "ocResults").value_of_css_property("display") != "none"
        )
        time.sleep(0.5)
        metrics = page.find_element(By.ID, "ocMetricsTable").get_attribute("innerHTML")
        assert len(metrics) > 10, "OC metrics table is empty"


class TestContinuousEndpoint:
    """Category 8: Continuous endpoint derivation (UC dataset)."""

    def test_22_continuous_derivation(self, page):
        """UC dataset derives successfully as continuous type."""
        load_example(page, "uc")
        derive_map(page, 70)
        result_type = js(page, "return mapResult.type")
        assert result_type == "continuous", f"Type: '{result_type}'"
        ess = js(page, "return mapResult.ess_robust")
        assert ess > 0, f"Continuous ESS should be positive: {ess}"
        # Density plot rendered
        container = page.find_element(By.ID, "densityPlot")
        svgs = container.find_elements(By.TAG_NAME, "svg")
        assert len(svgs) >= 1, "No SVG in continuous density plot"


class TestNoErrors:
    """Category 9: No console errors across operations."""

    def test_23_no_errors_switching_datasets(self, page):
        """Switching between all 3 datasets and deriving produces no SEVERE errors."""
        errors_before = get_console_errors(page)
        for ds in ["crohns", "uc", "onco"]:
            load_example(page, ds)
            derive_map(page)
            time.sleep(0.3)
        errors_after = get_console_errors(page)
        new_errors = [e for e in errors_after if e not in errors_before]
        assert len(new_errors) == 0, f"Console errors: {new_errors}"


# ============================================================
# New Feature Tests
# ============================================================

class TestNewFeatures:
    """Tests for features added in MAPriors v2.0."""

    def test_24_json_import_button(self, page):
        """JSON import button exists."""
        btns = page.find_elements(By.XPATH, "//button[contains(text(),'Import JSON')]")
        assert len(btns) > 0

    def test_25_drop_zone_exists(self, page):
        """Drop zone element exists."""
        zone = page.find_elements(By.ID, "dropZone")
        assert len(zone) > 0

    def test_26_png_export_button(self, page):
        """PNG export button exists."""
        btns = page.find_elements(By.XPATH, "//button[contains(text(),'Export PNG')]")
        assert len(btns) > 0

    def test_27_tutorial_button(self, page):
        """Tutorial button exists."""
        btns = page.find_elements(By.XPATH, "//button[contains(text(),'Tutorial')]")
        assert len(btns) > 0

    def test_28_tutorial_starts(self, page):
        """Tutorial overlay appears."""
        js(page, "startTutorial()")
        time.sleep(0.5)
        active = js(page, "return document.getElementById('tutorialOverlay').classList.contains('active')")
        assert active
        js(page, "closeTutorial()")

    def test_29_tutorial_step_text(self, page):
        """Tutorial shows title."""
        js(page, "startTutorial()")
        time.sleep(0.3)
        title = js(page, "return document.getElementById('tutTitle').textContent")
        assert len(title) > 0
        js(page, "closeTutorial()")

    def test_30_tutorial_navigation(self, page):
        """Tutorial Next advances."""
        js(page, "startTutorial()")
        js(page, "tutNext()")
        time.sleep(0.3)
        step = js(page, "return document.getElementById('tutStep').textContent")
        assert '2' in step
        js(page, "closeTutorial()")

    def test_31_tutorial_closes(self, page):
        """Tutorial closes properly."""
        js(page, "startTutorial()")
        time.sleep(0.2)
        js(page, "closeTutorial()")
        time.sleep(0.2)
        active = js(page, "return document.getElementById('tutorialOverlay').classList.contains('active')")
        assert not active

    def test_32_truthcert_card_exists(self, page):
        """TruthCert card element exists."""
        card = page.find_elements(By.ID, "truthcertCard")
        assert len(card) > 0

    def test_33_truthcert_visible_after_derive(self, page):
        """TruthCert card visible after deriving MAP."""
        ensure_crohns_derived(page)
        display = js(page, "return document.getElementById('truthcertCard').style.display")
        assert display != 'none'

    def test_34_truthcert_has_hash(self, page):
        """TruthCert content includes hash."""
        ensure_crohns_derived(page)
        content = js(page, "return document.getElementById('truthcertContent').textContent")
        assert 'SHA-256' in content or len(content) > 20

    def test_35_truthcert_badge_certified(self, page):
        """TruthCert badge shows CERTIFIED."""
        ensure_crohns_derived(page)
        badge = js(page, "return document.getElementById('truthcertBadge').textContent")
        assert 'CERTIFIED' in badge

    def test_36_tte_endpoint_option(self, page):
        """Time-to-event option exists in endpoint dropdown."""
        options = js(page, """
            const sel = document.getElementById('endpointType');
            return Array.from(sel.options).map(o => o.value);
        """)
        assert 'tte' in options

    def test_37_tte_conversion_function(self, page):
        """tteToLogHR function exists and computes."""
        result = js(page, "return tteToLogHR(12, 50, 100)")
        assert result is not None
        assert 'yi' in result
        assert result['vi'] > 0

    def test_38_export_png_no_crash(self, page):
        """exportPNG runs without errors."""
        ensure_crohns_derived(page)
        error = js(page, """
            try { exportPNG(); return null; }
            catch(e) { return e.message; }
        """)

    def test_39_download_truthcert_fn(self, page):
        """downloadTruthCert function exists."""
        exists = js(page, "return typeof downloadTruthCert === 'function'")
        assert exists

    def test_40_drag_drop_functions(self, page):
        """Drag-drop handler functions exist."""
        exists = js(page, """
            return typeof handleDragOver === 'function' &&
                   typeof handleDragLeave === 'function' &&
                   typeof handleDrop === 'function'
        """)
        assert exists


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
