# Administración y roles

Resumen
- El sistema usa un campo `role` en la tabla `users` con valores autorizados: `admin`, `manager`, `viewer`.
- Comportamiento por defecto: los usuarios nuevos y los migrados reciben `viewer`.

Migración / backfill de roles
- Al arrancar la aplicación, se detecta si falta la columna `role`. Si falta, la migración añade la columna y asigna `viewer` a los usuarios existentes.
- El proceso es idempotente y seguro para SQLite (usa `ALTER TABLE` cuando es posible).

Creación del administrador inicial (seed)
- Para crear el primer administrador, usar el script `scripts/seed_admin.py`.
- Ejemplo (PowerShell):

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SEED_ADMIN_EMAIL = "admin@example.com"
$env:SEED_ADMIN_PASSWORD = "ContraseñaSegura123!"
venv\Scripts\python.exe seed_admin.py --non-interactive
```

Buenas prácticas
- No exponer campos de `role` en formularios públicos.
- Limitar la creación/edición de roles sólo a la UI admin o a procesos internos.
- Registrar cambios críticos en cuentas (pendiente: auditoría).

Comprobaciones recomendadas tras cambios
- Ejecutar tests:

```powershell
venv\Scripts\python.exe -m pytest -q
```

- Verificar que:
  - Usuarios existentes tienen `role` con un valor válido.
  - Registro crea `viewer`.
  - Admin puede acceder al panel admin.
  - No-admins no ven el enlace admin en la barra.

Notas sobre despliegue
- Configurar backend persistente para `Flask-Limiter` en producción.
- Si la base es SQLite en producción, planificar ventana de mantenimiento para cambios en esquema.
---

## UI del panel de administración (Anas)

### Plantilla base (`templates/admin/master.html`)

- **Sidebar fijo** con navegación agrupada por secciones: General / Modelos / Sistema.
- **Topbar fija** con breadcrumb, indicador de estado del sistema y botón de logout.
- **Bootstrap 5** como framework CSS con Bootstrap Icons y Google Fonts.
- **Variables CSS centralizadas** que unifican la paleta y permiten cambiar el tema con un solo atributo HTML.
- Overrides completos de componentes Flask-Admin y diseño responsive.

### Sistema de tema claro/oscuro

Funciona 100% en el cliente sin llamadas al servidor. Un script en el `<head>` lee `localStorage` y aplica `data-theme` antes de que el navegador pinte, evitando parpadeo. El botón llama a `toggleTheme()` que alterna entre `dark` y `light` y guarda la preferencia.

### Dashboard con datos reales (`/admin/`)

| Variable | Consulta |
|---|---|
| `stats.usuarios` | `session.query(User).count()` |
| `stats.oposiciones` | `session.query(Oposicion).count()` |
| `stats.favoritas` | `session.query(Favorita).count()` |
| `stats.visitas` | `session.query(Visita).count()` |
| `stats.suscripciones` | `session.query(Suscripcion).count()` |
| `ultimos_usuarios` | Últimos 5 usuarios por `id DESC` |
| `ultimas_oposiciones` | Últimas 5 oposiciones por `id DESC` |

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `templates/admin/master.html` | Plantilla base reescrita: Bootstrap 5, sidebar, topbar, tema claro/oscuro |
| `templates/admin/index.html` | Dashboard con stats reales y tablas de registros recientes |
| `app/admin/views.py` | `@expose('/')`, consultas SQLAlchemy y `self.render()` |
---

## Analíticas (Anas)

### Vista `AnalyticsView`

Clase que hereda de `BaseView` de Flask-Admin, con el mismo control de acceso que el resto del panel (`role == "admin"`). Registrada en `init_admin` con `endpoint="analytics"`.

### Consultas SQLAlchemy

| Variable | Consulta |
|---|---|
| `dept_stats` | Top 7 departamentos con más oposiciones agrupados por `Oposicion.departamento` |
| `estudios_stats` | Usuarios agrupados por `User.nivel_estudios` (excluye `None`) |
| `top_visitadas` | Top 5 oposiciones con más visitas via `JOIN` entre `Oposicion` y `Visita` |

### Gráficos Chart.js

- Cargado desde CDN en `{% block head_tail %}` para garantizar que el script esté disponible antes del DOM.
- `initCharts()` lee las variables CSS (`--accent`, `--text-muted`, `--border`) en cada llamada, por lo que los colores se adaptan automáticamente al tema activo.
- Un `MutationObserver` escucha cambios en `data-theme` del elemento `<html>` y llama a `initCharts()` destruyendo y recreando los gráficos al instante.

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `app/admin/views.py` | Añadida `AnalyticsView` con `@expose('/')` y 3 queries SQLAlchemy |
| `templates/admin/analytics.html` | Template con 3 gráficos Chart.js, `head_tail` block y observer de tema |
---

## Exportación CSV y acciones masivas (Anas)

### Exportación CSV
Activada en `SecureModelView` con dos atributos heredados por todos los modelos:
```python
can_export = True
export_types = ['csv']
```
Aparece como botón **Export** en la parte superior de cada lista.

### Acciones masivas
Implementadas con el decorador `@action` de `flask_admin.actions`.

| Acción | Disponible en | Descripción |
|---|---|---|
| `eliminar_seleccionados` | Todos los modelos | Elimina registros seleccionados con confirmación y rollback |
| `degradar_a_viewer` | Solo `UserModelView` | Cambia rol a `viewer` sin afectar a usuarios `admin` |