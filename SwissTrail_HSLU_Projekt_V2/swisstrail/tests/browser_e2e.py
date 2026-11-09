"""Real Chromium browser system tests; launched against an isolated local FastAPI instance.

The production database is never modified. The GeoAdmin SearchServer response
is deterministic in-browser; WMTS tile requests are stubbed to avoid network
flakiness. Leaflet itself is loaded in the browser. Run explicitly via:
  python -m pytest -q tests/browser_e2e.py
"""
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4"
    "z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg=="
)
SEARCH_RESULTS = {
    "results": [
        {"name": "Luzern, Schweiz", "lat": 47.049, "lon": 8.309, "origin": "gg25"}
    ]
}

@pytest.fixture(scope="module")
def site(tmp_path_factory):
    folder = tmp_path_factory.mktemp("swisstrail-browser")
    db = folder / "users.db"
    segments = folder / "trails.db"
    with sqlite3.connect(segments) as con:
        con.executescript("""
            CREATE TABLE trail_segments(
                id INTEGER PRIMARY KEY,category TEXT,length_km REAL,coords_json TEXT);
            CREATE VIRTUAL TABLE trail_index USING rtree(
                id,min_lon,max_lon,min_lat,max_lat);
        """)
        con.execute("INSERT INTO trail_segments VALUES(1,?,?,?)", (
            "Wanderweg",0.08,json.dumps([[8.4848,47.0558],[8.4852,47.0562]])))
        con.execute("INSERT INTO trail_index VALUES(1,8.4848,8.4852,47.0558,47.0562)")
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        port=s.getsockname()[1]
    env=os.environ.copy()
    env.update({
        "SWISSTRAIL_DB":str(db),
        "SWISSTRAIL_TRAILS_DB":str(segments),
        "SWISSTRAIL_AUTO_IMPORT":"0",
        "SWISSTRAIL_SECURE_COOKIE":"0",
        "PYTHONUNBUFFERED":"1",
    })
    proc=subprocess.Popen(
        [sys.executable,"-m","uvicorn","app:app","--host","127.0.0.1","--port",str(port)],
        cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
    )
    address=f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            if proc.poll() is not None:
                raise RuntimeError("Test server stopped unexpectedly")
            try:
                with urlopen(address+"/api/health",timeout=1) as response:
                    assert response.status==200
                    break
            except Exception:
                time.sleep(.12)
        else:
            raise RuntimeError("Test server did not respond within 12 seconds")
        yield address
    finally:
        proc.terminate()
        try: proc.communicate(timeout=5)
        except subprocess.TimeoutExpired: proc.kill();proc.communicate(timeout=5)

@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
        yield browser
        browser.close()

def setup_page(browser,site,viewport=None):
    context=browser.new_context(viewport=viewport or {"width":1440,"height":900},locale="de-CH")
    page=context.new_page()
    page.route("**/wmts.geo.admin.ch/**",lambda route:route.fulfill(
        status=200,content_type="image/png",body=__import__("base64").b64decode(PIXEL_PNG)))
    # Stub only the external location provider, not the local backend.
    page.route("**/api/geoadmin/search**",lambda route:route.fulfill(
        status=200,content_type="application/json",body=json.dumps(SEARCH_RESULTS)))
    page.goto(site,wait_until="domcontentloaded",timeout=30000)
    page.wait_for_function("typeof L !== 'undefined' && document.querySelector('#map').classList.contains('leaflet-container')",timeout=25000)
    return context,page

def test_public_expedition_homepage_browser(browser,site):
    ctx,page=setup_page(browser,site)
    try:
        assert page.locator("#heroTitle").inner_text().startswith("Weniger Alltag.")
        assert "Vincent" in page.locator(".team-section").inner_text()
        for person in ["Vincent","Marlon","Enzkar","Kevin"]:
            assert person in page.locator("footer").inner_text()
        assert page.locator(".destination").count()==3
        page.locator("#surpriseMe").click()
        page.locator(".mapcard").wait_for(state="visible")
        assert page.locator("#toast").is_visible()
        page.locator("#heroExplore").click()
        assert page.locator("#map").is_visible()
        # A screenshot serves as visual evidence without inventing test outcomes.
        Path("artifacts").mkdir(exist_ok=True)
        page.screenshot(path="artifacts/browser-desktop.png",full_page=True,animations="disabled")
    finally:ctx.close()

def test_official_trails_and_geoadmin_search_browser(browser,site):
    ctx,page=setup_page(browser,site)
    try:
        # This is an actual Leaflet click event handled by the page's JS.
        page.evaluate("""() => {
          map.setView([47.056,8.485],14);
          map.fire('click',{latlng:L.latLng(47.056,8.485)});
        }""")
        page.locator(".leaflet-popup-content").wait_for(state="visible",timeout=10000)
        text=page.locator(".leaflet-popup-content").inner_text()
        assert "Offizieller Wanderwegabschnitt" in text
        assert "Wanderweg" in text
        assert "0.08 km" in text
        page.locator("#searchInput").fill("Luzern")
        page.locator("#searchButton").click()
        page.locator("#searchResults button.result").first.wait_for(timeout=10000)
        assert "Luzern" in page.locator("#searchResults button.result").first.inner_text()
        page.locator("#searchResults button.result").first.click()
        assert "Luzern" in page.locator(".leaflet-popup-content").last.inner_text()
    finally:ctx.close()

def test_registration_saved_places_routes_and_login(browser,site):
    ctx,page=setup_page(browser,site)
    try:
        username="test_"+uuid.uuid4().hex[:10]
        password="HsluBrowserOnly123!"
        page.locator("#loginButton").click()
        page.locator("#authSwitch").click()
        page.locator("#authUser").fill(username)
        page.locator("#authPassword").fill(password)
        page.locator("#authSubmit").click()
        page.locator("#userArea").wait_for(state="visible",timeout=10000)
        assert username in page.locator("#userName").inner_text()
        page.locator("#officialTrailToggle").uncheck()
        page.evaluate("() => map.fire('click',{latlng:L.latLng(47.05,8.31)})")
        page.locator("#placeModal:not(.hidden)").wait_for(timeout=5000)
        page.locator("#placeName").fill("HSLU Testort")
        page.locator("#placeNotes").fill("Temporäre Browser-Testdaten")
        page.locator("#placeForm button[type=submit]").click()
        page.wait_for_function("document.querySelector('#savedCount').textContent==='1'",timeout=10000)
        page.locator("#drawToggle").click()
        page.evaluate("""() => {
          map.fire('click',{latlng:L.latLng(47.04,8.30)});
          map.fire('click',{latlng:L.latLng(47.06,8.34)});
        }""")
        page.locator("#finishRoute").click()
        page.locator("#routeModal:not(.hidden)").wait_for(timeout=5000)
        page.locator("#routeName").fill("Browsertest Route")
        page.locator("#routeDifficulty").select_option("Bergwanderweg")
        page.locator("#routeForm button[type=submit]").click()
        page.wait_for_function("document.querySelector('#routeCount').textContent==='1'",timeout=10000)
        page.reload(wait_until="domcontentloaded")
        page.locator("#userArea").wait_for(state="visible",timeout=10000)
        page.locator("[data-tab=routes]").click()
        assert "Browsertest Route" in page.locator("#routeList").inner_text()
        page.locator("[data-tab=saved]").click()
        assert "HSLU Testort" in page.locator("#savedList").inner_text()
        page.locator("#logoutButton").click()
        page.locator("#loginButton").wait_for(state="visible",timeout=10000)
        page.locator("#loginButton").click()
        page.locator("#authUser").fill(username)
        page.locator("#authPassword").fill(password)
        page.locator("#authSubmit").click()
        page.locator("#userArea").wait_for(state="visible",timeout=10000)
        page.locator("[data-tab=routes]").click()
        page.wait_for_function("document.querySelector('#routeCount').textContent==='1'",timeout=10000)
        assert "Browsertest Route" in page.locator("#routeList").inner_text()
    finally:ctx.close()

def test_mobile_layout_browser(browser,site):
    ctx,page=setup_page(browser,site,{"width":390,"height":844})
    try:
        page.locator("#heroTitle").wait_for(state="visible")
        assert page.locator("#surpriseMe").is_visible()
        assert page.locator(".destination").count()==3
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 3")
        Path("artifacts").mkdir(exist_ok=True)
        page.screenshot(path="artifacts/browser-mobile.png",full_page=True,animations="disabled")
    finally:ctx.close()
