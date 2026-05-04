"""
Pruebas E2E del Panel de Administración — ASubiela
====================================================
Ejecutar:
    playwright install
    pytest tests/test_admin_e2e.py -v

Variables de entorno opcionales:
    ADMIN_EMAIL     (por defecto: amm0246@alu.medac.es)
    ADMIN_PASSWORD  (por defecto: Anas1234)
    BASE_URL        (por defecto: http://127.0.0.1:5000)
"""

import os
import pytest
from playwright.sync_api import sync_playwright, expect


# =========================
# ⚙️ CONFIGURACIÓN
# =========================

BASE_URL       = os.getenv("BASE_URL", "http://127.0.0.1:5000")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL", "amm0246@alu.medac.es")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Anas1234")


# =========================
# 🧰 FIXTURES
# =========================

@pytest.fixture(scope="session")
def browser():
    """Abre el navegador una sola vez para toda la sesión de tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def admin_page(browser):
    """
    Página ya autenticada como admin.
    Reutilizada por todos los tests que necesiten sesión activa.
    """
    page = browser.new_page()
    page.goto(f"{BASE_URL}/login")

    # Rellenar formulario de login
    page.fill('input[name="email"]', ADMIN_EMAIL)
    page.fill('input[name="password"]', ADMIN_PASSWORD)
    page.click('form.form-register button.btn-primary')  # ← CORREGIDO

    # Esperar a que la redirección post-login termine
    page.wait_for_load_state("networkidle")

    yield page
    page.close()


# =========================
# 🧪 TESTS
# =========================

class TestLogin:

    def test_login_page_carga(self, browser):
        """La página de login es accesible y muestra el formulario."""
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login")
        assert page.title() is not None
        assert page.locator('input[name="email"]').is_visible()
        assert page.locator('input[name="password"]').is_visible()
        page.close()

    def test_login_credenciales_incorrectas(self, browser):
        """Un login con credenciales incorrectas no accede al panel."""
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "falso@ejemplo.com")
        page.fill('input[name="password"]', "contrasenawrong")
        page.click('form.form-register button.btn-primary')  # ← CORREGIDO
        page.wait_for_load_state("networkidle")

        # No debe redirigir al admin
        assert "/admin" not in page.url
        page.close()

    def test_login_admin_correcto(self, admin_page):
        """El admin puede autenticarse y llega a una página válida."""
        assert admin_page.url is not None
        assert "login" not in admin_page.url


class TestAccesoAdmin:

    def test_dashboard_admin_accesible(self, admin_page):
        """El admin accede al dashboard en /admin/."""
        admin_page.goto(f"{BASE_URL}/admin/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.url.startswith(f"{BASE_URL}/admin")

    def test_dashboard_muestra_bienvenida(self, admin_page):
        """El dashboard muestra el mensaje de bienvenida."""
        admin_page.goto(f"{BASE_URL}/admin/")
        admin_page.wait_for_load_state("networkidle")
        contenido = admin_page.content()
        assert "Bienvenido" in contenido or "Panel" in contenido

    def test_sidebar_visible(self, admin_page):
        """El sidebar del panel está presente."""
        admin_page.goto(f"{BASE_URL}/admin/")
        assert admin_page.locator("#sidebar").is_visible()

    def test_topbar_visible(self, admin_page):
        """El topbar del panel está presente."""
        admin_page.goto(f"{BASE_URL}/admin/")
        assert admin_page.locator("#topbar").is_visible()


class TestNavegacionModelos:

    def test_navegar_usuarios(self, admin_page):
        """El admin puede navegar a la lista de usuarios."""
        admin_page.goto(f"{BASE_URL}/admin/admin_users/")
        admin_page.wait_for_load_state("networkidle")
        assert "admin_users" in admin_page.url

    def test_navegar_oposiciones(self, admin_page):
        """El admin puede navegar a la lista de oposiciones."""
        admin_page.goto(f"{BASE_URL}/admin/admin_oposiciones/")
        admin_page.wait_for_load_state("networkidle")
        assert "admin_oposiciones" in admin_page.url

    def test_navegar_analytics(self, admin_page):
        """El admin puede navegar a la vista de analíticas."""
        admin_page.goto(f"{BASE_URL}/admin/analytics/")
        admin_page.wait_for_load_state("networkidle")
        assert "analytics" in admin_page.url

    def test_analytics_muestra_graficos(self, admin_page):
        """La página de analíticas contiene los canvas de Chart.js."""
        admin_page.goto(f"{BASE_URL}/admin/analytics/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("#chartDepts").count() > 0
        assert admin_page.locator("#chartEstudios").count() > 0
        assert admin_page.locator("#chartPopular").count() > 0


class TestControlAcceso:

    def test_admin_sin_sesion_redirige_login(self, browser):
        """Un usuario no autenticado es redirigido al login al intentar acceder al admin."""
        page = browser.new_page()
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_load_state("networkidle")

        # Debe redirigir al login o mostrar 403
        assert "login" in page.url or page.locator("body").inner_text().find("403") != -1
        page.close()

    def test_modelos_sin_sesion_redirigen(self, browser):
        """Un usuario no autenticado no puede acceder a ningún ModelView."""
        page = browser.new_page()
        for endpoint in ["admin_users", "admin_oposiciones", "admin_favoritas"]:
            page.goto(f"{BASE_URL}/admin/{endpoint}/")
            page.wait_for_load_state("networkidle")
            assert "login" in page.url or page.locator("body").inner_text().find("403") != -1
        page.close()


class TestExportCSV:

    def test_boton_export_visible_usuarios(self, admin_page):
        """El botón de exportar CSV está visible en la lista de usuarios."""
        admin_page.goto(f"{BASE_URL}/admin/admin_users/")
        admin_page.wait_for_load_state("networkidle")
        contenido = admin_page.content()
        assert "Export" in contenido or "export" in contenido

    def test_boton_export_visible_oposiciones(self, admin_page):
        """El botón de exportar CSV está visible en la lista de oposiciones."""
        admin_page.goto(f"{BASE_URL}/admin/admin_oposiciones/")
        admin_page.wait_for_load_state("networkidle")
        contenido = admin_page.content()
        assert "Export" in contenido or "export" in contenido