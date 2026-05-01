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
venv\Scripts\python.exe scripts\seed_admin.py --non-interactive
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
