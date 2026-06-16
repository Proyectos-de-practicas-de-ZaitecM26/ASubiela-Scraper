# 📚 BOE Oposiciones – Web Scraping y Portal de Usuarios

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


Aplicación Flask que sincroniza diariamente la sección 2B del BOE (oposiciones), la guarda en SQLite y ofrece un panel para que cada usuario pueda filtrar oportunidades, marcarlas como favoritas o visitadas, configurar alertas por email y mantener su perfil actualizado.
---
---

## 📑 Tabla de Contenidos

- [📚 BOE Oposiciones – Web Scraping y Portal de Usuarios](#-boe-oposiciones--web-scraping-y-portal-de-usuarios)
  - [📑 Tabla de Contenidos](#-tabla-de-contenidos)
  - [✨ Características principales](#-características-principales)
  - [🗄️ Migración a SQLAlchemy (2026-04-28)](#-migración-a-sqlalchemy-2026-04-28)
  - [📋 Requisitos previos](#-requisitos-previos)
  - [🚀 Instalación y configuración](#-instalación-y-configuración)
    - [Puesta en marcha rápida](#puesta-en-marcha-rápida)
      - [1. Clonar o descargar el proyecto](#1-clonar-o-descargar-el-proyecto)
      - [2. Ejecutar el script de bootstrap](#2-ejecutar-el-script-de-bootstrap)
      - [3. Activar el entorno virtual (si no usaste el bootstrap)](#3-activar-el-entorno-virtual-si-no-usaste-el-bootstrap)
      - [4. Ejecutar la aplicación](#4-ejecutar-la-aplicación)
  - [Configuración y variables de entorno](#configuración-y-variables-de-entorno)
  - [💳 Pagos (Stripe)]
  - [🔐 reCAPTCHA (login)]
  - [☁️ Despliegue en Vercel]
  - [🏗️ Arquitectura del proyecto](#️-arquitectura-del-proyecto)
  - [🧪 Guía corta: probar el chatbot en local](#-guía-corta-probar-el-chatbot-en-local)
  - [⚙️ Funcionalidades](#️-funcionalidades)
    - [Flujo de scraping](#flujo-de-scraping)
    - [Gestión de usuarios](#gestión-de-usuarios)
    - [Subida de fotos de perfil](#subida-de-fotos-de-perfil)
    - [Envío de emails](#envío-de-emails)
  - [🍪 Banner de política de cookies](#-banner-de-política-de-cookies)
  - [⚖️ Páginas legales y enlaces en footer](#️-páginas-legales-y-enlaces-en-footer)
  - [🌐 Selector de idioma (ES / EN)](#-selector-de-idioma-es--en)
  - [♿ Panel de accesibilidad visual](#-panel-de-accesibilidad-visual)
  - [🤖 Chatbot asistente BOE](#-chatbot-asistente-boe)
  - [🧪 Tests](#-tests)
    - [Pruebas unitarias del chatbot](#pruebas-unitarias-del-chatbot)
    - [Pruebas E2E del panel de administración](#pruebas-e2e-del-panel-de-administración)
  - [📊 Página de estadísticas](#-página-de-estadísticas)
  - [🛠️ Scripts útiles](#️-scripts-útiles)
  - [📁 Estructura de archivos](#-estructura-de-archivos)
  - [🔮 Próximos pasos recomendados](#-próximos-pasos-recomendados)
  - [🤝 Contribución](#-contribución)
  - [📄 Licencia](#-licencia)
  - [📞 Contacto](#-contacto)

---

## ✨ Características principales

- **🔍 Scraping automático del BOE**: Descarga nuevas oposiciones usando `BeautifulSoup` y `requests`, normaliza provincias y elimina duplicados por `url_html`.
- **💾 Dos bases de datos SQLite**:
  - `oposiciones.db` con las publicaciones del BOE.
  - `usuarios.db` con credenciales, perfil, visitas, favoritos y suscripciones.
- **👤 Gestión de usuarios**: Registro con campos avanzados, login con `Flask-Login`, edición completa del perfil y cambio de contraseña.
- **📧 Alertas y newsletters**: Configuración de alertas diarias o por favoritos y envío de emails con `Flask-Mail`.
- **📊 Seguimiento de actividad**: Cada click marca visitas y favoritos para personalizar las tarjetas. Las visitas se registran tanto para usuarios autenticados como anónimos.
- **📋 Log de actividad**: Panel de administración con registro automático de `login`, `logout` y eventos internos, con fecha legible, badges por acción y detalles compactos.
- **📈 Página de estadísticas**: Vista pública en `/estadisticas` con gráfico de barras por departamento, resumen desglosado de visitas autenticadas, anónimas y total combinado.
- **🎨 Tema claro/oscuro** y subida de foto de perfil almacenada en `static/uploads/profiles`.
- **🍪 Banner de cookies**: Aviso de política de cookies con preferencias granulares, persistido en `localStorage`.
- **⚖️ Cumplimiento legal básico**: Enlaces permanentes en footer a política de cookies, política de privacidad y aviso legal.
- **🌐 Selector de idioma con banderas**: Botón dinámico `🇬🇧 EN` / `🇪🇸 ES` en la cabecera que traduce al instante tanto contenido estático como mensajes dinámicos del frontend, sin recargar.
- **♿ Panel de accesibilidad visual**: Botón flotante que despliega controles para ajustar tamaño de texto, contraste y otros filtros visuales; persistidos en `localStorage`.
- **🤖 Chatbot asistente BOE**: Asistente conversacional integrado con Groq (LLaMA 3.3 70B), con voz (TTS/STT), historial persistente y habilidades especializadas en búsqueda y filtrado del BOE.

---

## 🗄️ Migración a SQLAlchemy (2026-04-28)

Esta sección documenta los cambios realizados el 28 de abril de 2026 para migrar de SQLite nativo a SQLAlchemy.

### Cambios implementados

#### 1. Consolidación de bases de datos
- **Antes**: Dos bases de datos SQLite separadas (`oposiciones.db` y `usuarios.db`).
- **Después**: Una única base de datos `boe_scraper.db` gestionada con SQLAlchemy.
- La configuración se centraliza en `app/config.py` con `SQLALCHEMY_DATABASE_URI`.
- La nueva base de datos está ubicada en la carpeta `instance`, al mismo nivel que la carpeta `app`

#### 2. Nuevos modelos de datos
Se han creado los siguientes modelos en `app/data/models.py`:
- `Oposicion` - Oposiciones del BOE
- `User` - Usuarios del sistema (hereda de `UserMixin` de Flask-Login)
- `Visita` - Registro de visitas de usuarios a oposiciones
- `Favorita` - Oposiciones marcadas como favoritas por usuarios
- `Suscripcion` - Suscripciones a alertas diarias

#### 3. Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `app/__init__.py` | Eliminado import de `db.py` y `teardown_appcontext` |
| `app/config.py` | Añadida configuración SQLAlchemy, eliminadas rutas de BBDD antiguas |
| `app/db.py` | **Eliminado** - Funciones de conexión SQLite nativas |
| `app/models.py` | **Eliminado** - Modelo User antiguo basado en SQLite |
| `app/data/models.py` | Actualizado para incluir `UserMixin` |
| `app/data/migrar_datos.py` | Cambiados `print` por `logger`, añadido logging de migración |
| `app/routes/main.py` | Migrado a consultas SQLAlchemy |
| `app/routes/auth.py` | Migrada autenticación completa a SQLAlchemy |
| `app/routes/user.py` | Migradas todas las funciones de usuario a SQLAlchemy |
| `app/email_utils.py` | Migrada función `all_user_emails()` a SQLAlchemy |
| `app/scraping/boe_scraper.py` | Completamente migrado a SQLAlchemy |
| `daily_task.py` | Migrado a SQLAlchemy para gestión de tareas diarias |
| `templates/user_oposiciones.html` | Ajustado para recibir listas en lugar de diccionarios |

#### 4. Beneficios de la migración

- **Código más limpio**: Eliminación de consultas SQL raw en favor de queries tipadas.
- **Mantenibilidad**: Uso del ORM de SQLAlchemy facilita futuras migraciones a otras BBDD.
- **Relaciones definidas**: Backrefs configurados entre modelos (`User.visitas`, `User.favoritas`, etc.).
- **Logging**: Sustitución de `print` por `current_app.logger` para mejor trazabilidad.
- **Gestión de errores**: Mejor manejo de transacciones con `rollback()` en caso de errores.

#### 5. Migración automática

Al iniciar la aplicación por primera vez después de esta migración:
1. Se detectan las bases de datos antiguas (`usuarios.db` y `oposiciones.db`).
2. Se ejecuta automáticamente la migración de datos a la nueva estructura.
3. Se muestra un mensaje en la consola indicando que la migración ha finalizado.
4. Los archivos antiguos pueden eliminarse manualmente tras verificar la migración.

---

## 📋 Requisitos previos

- **Python 3.11+** (con acceso a `venv`).
- **Acceso a Internet** para el scraping del BOE y el envío de emails.
- **(Opcional)** Credenciales propias para Gmail u otro SMTP configurando variables de entorno.

---

## 🚀 Instalación y configuración

### Puesta en marcha rápida

#### 1. Clonar o descargar el proyecto

```bash
git clone <repo>
cd I_S25_Web_Scraping-1/I_S25_Web_Scraping
```

#### 2. Ejecutar el script de bootstrap

**Windows (PowerShell o CMD):**
```powershell
.\bootstrap.bat
```

**Linux / macOS:**
```bash
bash bootstrap.sh
```

El script crea/activa `.venv`, instala dependencias y garantiza la carpeta `static/uploads/profiles`.

#### 3. Activar el entorno virtual (si no usaste el bootstrap)

**Windows:**
```powershell
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

#### 4. Ejecutar la aplicación

```bash
.venv/bin/python run.py
```

Por defecto se levanta en `http://127.0.0.1:5000/`.

### Configuración y variables de entorno

Puedes sobrescribir los valores definidos en `app/config.py`:

| Variable            | Descripción                                             | Valor por defecto             |
|---------------------|---------------------------------------------------------|-------------------------------|
| `SECRET_KEY`        | Clave para sesiones Flask                               | `cambia-esto-en-produccion`   |
| `USERS_DB_PATH`     | Ruta al SQLite de usuarios                              | `usuarios.db`                 |
| `BOE_DB_PATH`       | Ruta al SQLite con oposiciones                          | `oposiciones.db`              |
| `MAIL_USERNAME`     | Cuenta SMTP para `Flask-Mail`                           | `notificaciones.scraper@...`  |
| `MAIL_PASSWORD`     | Password o app-password del SMTP                        | `sqoj zfue ovcf dlhz`         |
| `GROQ_API_KEY`      | API Key para respuestas IA del endpoint `/api/chatbot`  | *(sin valor por defecto)*              
| `STRIPE_SECRET_KEY`   clave secreta Stripe                                                                    |
| `RECAPTCHA_SITE_KEY`  clave pública reCAPTCHA                                                                 |
| `RECAPTCHA_SECRET_KEY`clave secreta reCAPTCHA                                                                 |
| `ADMIN_EMAIL / ADMIN_PASSWORD`    solo para entornos de desarrollo (si procede)                               | 

**⚠️ IMPORTANTE:** En producción define estas variables antes de arrancar (`set VAR=...` en Windows o `export VAR=...` en Linux/macOS).Asegurar que las variables sensibles se definen en el entorno de despliegue.

---

## 🧪 Guía corta: probar el chatbot en local

El chatbot usa siempre el prompt completo del BOE. Cada compañero solo necesita su propia `GROQ_API_KEY` para hacer pruebas locales.

1. **Activa el entorno virtual** y arranca la app:

```powershell
venv\Scripts\activate
$env:GROQ_API_KEY="tu_api_key"
python run.py
```

2. **Haz una prueba rápida al endpoint**:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/api/chatbot" -ContentType "application/json" -Body '{"message":"resumen del boe-a-2026-8444"}'
```

3. **Verifica comportamiento esperado**:
- Tema BOE: responde normalmente.
- Fuera de BOE: bloquea/redirige al dominio BOE.
- Si falta contexto: aplica fallback y no inventa datos.

4. **Casos recomendados de validación rápida**:
- `como hacer una paella?` → bloqueo por fuera de dominio.
- `resumen del boe-a-2026-8444` → respuesta directa orientada a resumen de referencia.
- `Busca oposiciones en Madrid para hoy` → respuesta IA (requiere `GROQ_API_KEY`).
- `resumen del artículo 5 de esa norma` → no bloquea y aplica fallback si falta contexto.

---

## 💳 Pagos (Stripe)

Rutas clave:
- app/routes/payments.py — inicia checkout (crea sesión Stripe).
- app/routes/stripe_pay.py — maneja confirmaciones y webhooks.

Plantillas:
- templates/pagos.html — formulario/botón de inicio de pago.
- templates/success.html — página de éxito del pago.
- templates/cancel.html — página de cancelación.

Recomendaciones:
Configurar STRIPE_SECRET_KEY y validar eventos entrantes.
Añadir pruebas E2E del flujo de pago (usando el modo test de Stripe).


---

## 🔐 reCAPTCHA (login)

1. Frontend: widget incluido en templates/login.html usando RECAPTCHA_SITE_KEY.
2. Backend: verificación del token con la API de Google en app/routes/auth.py antes de autenticar.
3. Habilitar/deshabilitar según exista la configuración RECAPTCHA_SITE_KEY/RECAPTCHA_SECRET_KEY.
4. Asegura protección contra bots en endpoints de autenticación.

---

## ☁️ Despliegue en Vercel

1. vercel.json incluido con pasos de build y rewrites.
2. Definir variables de entorno en el panel de Vercel:
  SECRET_KEY, SQLALCHEMY_DATABASE_URI, STRIPE_, RECAPTCHA_, GROQ_API_KEY, MAIL_

- Para persistencia en producción se recomienda usar un servicio de BBDD (Postgres) y almacenamiento externo para uploads.
- Revisar límites de tiempo/ejecución en Vercel si se ejecutan tareas largas; considerar externalizar tareas de scraping o usar jobs programados.


---

## 🏗️ Arquitectura del proyecto

```
app/
  data/
    models.py
  routes/
    init.py
    admin.py
    auth.py            # Autenticación (login, registro, logout).
    chat.py            # Endpoint /chatbot/api.
    filters.py
    main.py            # Landing, scraping, estadísticas y páginas legales.
    user.py            # Panel del usuario, filtros, favoritos y perfil.
    payments.py
    policies.py       
    stripe_pay.py 
    theme.py    
  services/
    ai_client.py       # Cliente unificado de IA (Groq + proveedores alternativos).
    chatbot.py
  scraping/
    boe_scraper.py  
  __init__.py          # Crea la app, registra blueprints, filtros y temas.
  audit_utils.py
  auth_utils.py
  config.py            # Configuración centralizada.
  email_utils.py       # Helpers para enviar newsletters.
  extensions.py
  file_utils.py
  backend/
    vercel.json
  instance/
    boe_scraper.db
static/                # CSS, imágenes y uploads de perfiles.
templates/             # Base + vistas (index, login, registro, user, chat ...).
bootstrap.(bat|sh)     # Scripts para preparar el entorno.
requirements.txt       # Dependencias de Python, Flask, Stripe, etc necesarias para el proyecto.
run.py                 # Punto de entrada (crea la app y lanza Flask).

---

## ⚙️ Funcionalidades

### Flujo de scraping

1. Cada visita a `/` llama a `sync_boe_hasta_hoy`, que:
   - Detecta la última fecha guardada.
   - Descarga los días que falten hasta hoy (máx. 30 si está vacío).
   - Limpia registros con más de 30 días.
2. Los administradores pueden forzar la sincronización desde `/admin/sync_boe` o cargar los últimos 30 días con `/admin/scrape_ultimos_30`.
3. Los datos quedan accesibles en `oposiciones.db`, listos para filtros/paginación.

### Gestión de usuarios

- **Registro**: Formulario completo con validación de campos obligatorios.
- **Login/Logout**: Sistema de autenticación con `Flask-Login`.
- **Perfil**: Edición completa de datos personales, dirección, formación académica, etc.
- **Cambio de contraseña**: Validación de contraseña actual antes de actualizar.
- **Favoritos y visitas**: Seguimiento personalizado de oposiciones de interés.

### Subida de fotos de perfil

- Las imágenes se almacenan dentro de `static/uploads/profiles/`.
- El nombre se normaliza como `user_<id>_<timestamp>.<ext>` usando `secure_filename`.
- Se aceptan extensiones `png`, `jpg`, `jpeg`, `gif`, `webp`.
- El campo `users.foto_perfil` guarda la ruta relativa (`/static/uploads/profiles/...`) usada en las plantillas.

### Envío de emails

`app/email_utils.py` monta un HTML sencillo y usa `Flask-Mail`. Configura `MAIL_USERNAME` y `MAIL_PASSWORD` con un app password de Gmail o un SMTP propio antes de enviar correos reales.

### Asistente IA BOE

- Endpoint backend: `POST /api/chatbot` en `app/routes/main.py`.
- Prompt único y completo en `app/chatbot.py`.
- Skills de control en `app/services/chat_skills.py`:
  - bloqueo de temas fuera de BOE,
  - detección de referencias BOE,
  - soporte de preguntas de seguimiento legal (`artículo`, `norma`, `disposición`, `fecha límite`, etc.).
- Frontend: se dejó solo el chat nuevo integrado en `templates/base.html` (se retiró el chat legacy para pruebas).

---

## 🍪 Banner de política de cookies

La aplicación muestra un banner en la parte inferior de todas las páginas la primera vez que un usuario visita el sitio, cumpliendo con la normativa europea de cookies (RGPD/LSSI).

**Comportamiento:**

- El banner aparece únicamente si el usuario **no ha guardado previamente** una preferencia (se comprueba contra `localStorage` bajo la clave `boe_cookie_consent`).
- Una vez elegida una opción, el banner no vuelve a mostrarse en visitas posteriores desde el mismo navegador.

**Opciones disponibles:**

| Botón | Acción |
|---|---|
| **Aceptar todas** | Activa cookies esenciales, analíticas y de personalización. |
| **Solo esenciales** | Activa únicamente las cookies imprescindibles para el funcionamiento. |
| **Configurar** | Abre un modal con toggles individuales por categoría. |

**Categorías de cookies:**

- **Esenciales** – Siempre activas; necesarias para sesiones y autenticación.
- **Analíticas** – Permiten medir el uso de la web (desactivadas por defecto al elegir «Solo esenciales»).
- **Personalización** – Recuerdan preferencias como el tema claro/oscuro (desactivadas por defecto al elegir «Solo esenciales»).

**Implementación técnica:**

- HTML y lógica JS incluidos en `templates/base.html` (sin dependencias externas).
- Estilos integrados en `static/css/style.css` con soporte completo de **tema oscuro**.
- Accesible: roles ARIA (`dialog`, `aria-modal`), cierre con tecla `Escape` y gestión de foco.
- El enlace «Más información» apunta a `/politica-cookies`.

---

## ⚖️ Páginas legales y enlaces en footer

Además del banner de cookies, la aplicación incorpora páginas legales accesibles desde el pie de página global.

**Enlaces visibles en el footer:**

- `Politica de Cookies` → `/politica-cookies`
- `Politica de Privacidad` → `/politica-privacidad`
- `Aviso Legal` → `/aviso-legal`
- Los tres enlaces se muestran en blanco para mantener una coloración uniforme en el footer.

**Implementación técnica:**

- Los enlaces se renderizan desde `templates/base.html` para estar disponibles en todas las vistas.
- Las rutas están definidas en `app/routes/main.py`.
- Las plantillas correspondientes son:
  - `templates/politica_cookies.html`
  - `templates/politica_privacidad.html`
  - `templates/aviso_legal.html`

**Nota:**

El contenido actual de estas páginas está pensado como base informativa. Antes de publicar en producción, conviene revisarlo con asesoría legal para adaptarlo a los datos reales del titular y al tratamiento efectivo de datos/cookies.

---

## 🌐 Selector de idioma (ES / EN)

Botón visible en la cabecera de navegación que permite cambiar el idioma de toda la interfaz entre español e inglés sin recargar la página.

**Comportamiento:**

- La preferencia se guarda en `localStorage` bajo la clave `boe_lang_v1` y se aplica automáticamente en cada visita.
- El botón muestra `🇬🇧 EN` cuando el idioma activo es español, y `🇪🇸 ES` cuando es inglés.

**Elementos traducidos:**

| Zona | Textos traducidos |
|---|---|
| Navbar y footer | Menú de usuario, login/registro, enlaces legales |
| Portada, resultados y tablas | Filtros, cabeceras, botones, estados (`Nuevo`, `Visitada`) |
| Perfil y formularios | Login, registro, recuperación/reset de contraseña, configuración y newsletter |
| Legales y cookies | Política de cookies, privacidad, aviso legal y modal/banner de cookies |
| Chatbot | Título, saludo, placeholder, envío, estados de voz y errores de conexión |

**Implementación técnica:**

- Sistema i18n 100% client-side en `templates/base.html` (sin librerías externas).
- Los elementos a traducir usan `data-i18n`, `data-i18n-placeholder`, `data-i18n-title` y `data-i18n-aria-label`.
- El diccionario de traducciones vive en un objeto JS con claves `es` y `en`, más helper global `window.__boeI18n`.
- Se emite el evento `boe:lang-changed` para refrescar textos que se renderizan dinámicamente por JavaScript.
- El atributo `lang` del elemento `<html>` se actualiza automáticamente al cambiar de idioma.

---

## ♿ Panel de accesibilidad visual

Botón flotante con icono de accesibilidad universal, visible en todas las páginas, que despliega un panel lateral con herramientas de ajuste visual pensadas para personas con dificultades visuales.

**Controles disponibles:**

| Control | Descripción |
|---|---|
| **Tamaño de texto** | Botones `A-`, `A` (reset) y `A+` para reducir, restaurar o ampliar la tipografía base. |
| **Alto contraste** | Aplica una paleta de alto contraste sobre toda la interfaz. |
| **Escala de grises** | Desactiva el color de la página para personas con daltonismo o fotosensibilidad. |
| **Subrayar enlaces** | Fuerza el subrayado de todos los hipervínculos para facilitar su identificación. |
| **Espacio entre letras** | Aumenta el espaciado de caracteres para mejorar la legibilidad. |
| **Restablecer todo** | Revierte todos los ajustes a los valores por defecto. |

**Implementación técnica:**

- HTML, CSS y JS incluidos en `templates/base.html` y `static/css/style.css`, sin dependencias externas.
- Las preferencias se persisten en `localStorage` bajo la clave `boe_a11y_prefs` y se aplican al cargar cada página.
- Totalmente accesible: roles ARIA (`region`, `group`), cierre con `Escape` y gestión de foco al abrir/cerrar.
- Soporte completo de **tema oscuro** y diseño **responsive**.
- Traducible mediante el sistema i18n integrado (atributos `data-i18n`).

---

## 🧩 Panel de Administración (Isidro)

- Integración de Flask-Admin en la aplicación (`/admin`)
- Creación de ModelViews para la gestión de datos
- Implementación de CRUD completo en las entidades

- Desarrollo de `UserModelView` con:
  - Columnas configuradas
  - Búsqueda por email, nombre y apellidos
  - Filtro por rol
  - Ordenación de registros
  - Ocultación de contraseña

- Validación de roles (`admin`, `manager`, `viewer`)

- Moderación manual de imágenes (Flask-Admin):
  - En el listado de usuarios se muestra una **miniatura (50px)** de `foto_perfil` para detectar contenido ofensivo rápidamente.
  - Acción masiva **"Moderar Imagen"**: elimina la imagen de perfil (`foto_perfil = None`) de los usuarios seleccionados.

- Añadidas ModelViews para:
  - Oposiciones
  - Favoritas
  - Log de actividad
  - Visitas
  - Suscripciones

- Integración con relaciones de SQLAlchemy
- Acceso restringido solo a usuarios con rol `admin`
- Panel completamente funcional para administración

### ✨ UI, Dashboard y Tema (Anas)

#### Plantilla base personalizada (`templates/admin/master.html`)

Se ha sobrescrito la plantilla base de Flask-Admin para reemplazar su interfaz genérica por un diseño moderno basado en **Bootstrap 5**. Los elementos principales son:

- **Sidebar fijo** con navegación a todos los modelos, agrupada por secciones (General / Modelos / Sistema).
- **Topbar fija** con breadcrumb de navegación, indicador de estado del sistema y botón de logout.
- **Sistema de tema claro/oscuro** gestionado 100% en el cliente mediante `localStorage` (clave `theme`), sin ninguna llamada al servidor.
- Variables CSS (`--bg-base`, `--accent`, `--text-primary`, etc.) que unifican toda la paleta de colores.
- Overrides completos de los componentes de Flask-Admin: tablas, botones, formularios, paginación, alertas, modales y dropdowns.

#### Dashboard con datos reales (`templates/admin/index.html` + `app/admin/views.py`)

- **5 tarjetas de estadísticas** con conteos reales de la BD (`COUNT(*)` sobre cada tabla), enlazando a su `ModelView`.
- **Tabla de últimos 5 usuarios** con badges de color por rol (`admin` / `manager` / `viewer`).
- **Tabla de últimas 5 oposiciones** scrapeadas con identificador y fecha.

#### Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `templates/admin/master.html` | Plantilla base reescrita con Bootstrap 5, sidebar, topbar y tema claro/oscuro |
| `templates/admin/index.html` | Dashboard con tarjetas de stats reales y tablas de registros recientes |
| `app/admin/views.py` | Añadido `@expose('/')` con consultas SQLAlchemy y `self.render()` |

### 📊 Analíticas (Anas)

- Vista personalizada (`BaseView`) accesible en `/admin/analytics` desde el sidebar del panel.
- **Gráfico de dona** con el reparto de oposiciones por departamento (Top 7).
- **Gráfico de barras vertical** con el perfil de nivel de estudios de los usuarios registrados.
- **Gráfico de barras horizontal** con las 5 oposiciones más visitadas.
- Los gráficos se redibujan automáticamente al cambiar entre tema claro y oscuro.

| Archivo | Cambios |
|---------|---------|
| `app/admin/views.py` | Añadida clase `AnalyticsView` con queries SQLAlchemy y registrada en `init_admin` |
| `templates/admin/analytics.html` | Template con 3 gráficos Chart.js adaptados al tema claro/oscuro |

### 📤 Exportación CSV y acciones masivas (Anas)

- Exportación a CSV habilitada en todos los `ModelView` con el botón **Export** en la parte superior de cada lista.
- **Acción masiva general** — "Eliminar seleccionados": elimina los registros marcados con confirmación previa y rollback automático si algo falla. Disponible en todos los modelos.
- **Acción masiva específica de usuarios** — "Cambiar rol a Viewer": cambia el rol de los usuarios seleccionados a `viewer`, protegiendo siempre a los `admin`.

| Archivo | Cambios |
|---------|---------|
| `app/admin/views.py` | `can_export = True`, `export_types = ['csv']` en `SecureModelView` y dos acciones `@action` |

---

## 🤖 Chatbot asistente BOE

Asistente conversacional flotante especializado en el contenido del BOE, accesible desde cualquier página de la aplicación.

**Características:**

- **Motor de IA**: Groq API con el modelo `llama-3.3-70b-versatile` (temperatura 0.3, máx. 450 tokens).
- **Habilidades integradas** (`app/services/chat_skills.py`): El chatbot detecta la intención del usuario y puede ejecutar búsquedas reales contra la base de datos local antes de pasar la consulta al modelo de lenguaje:
  - Búsqueda por provincia
  - Búsqueda por departamento / ministerio
  - Listado de oposiciones recientes
  - Consulta de estadísticas (total de registros, etc.)
- **Filtrado de temas**: Responde únicamente preguntas relacionadas con el BOE; rechaza cualquier otra temática.
- **Voz (TTS / STT)**: Lectura en voz alta de las respuestas (Web Speech API) y dictado por voz para escribir preguntas.
- **Historial persistente**: El hilo de conversación se guarda en `localStorage` (`boe_chat_messages_v1`) y se restaura al reabrir el chat.
- **Borrador automático**: El texto en curso se guarda en `localStorage` (`boe_chat_draft_v1`) para no perderlo si se cierra el panel.
- **Vista dedicada**: `templates/chat.html` se integró con la plantilla base para heredar navbar, selector ES/EN y traducciones globales.

**Arquitectura del chatbot:**

```
app/
  chatbot.py               # Función principal que llama a Groq API
  services/
    ai_client.py           # Cliente unificado (Groq + fallback a otros proveedores)
    chat_skills.py         # Habilidades: búsqueda en BD, detección de intención, filtrado
  routes/
    chat.py                # Blueprint /chatbot/api (POST)
templates/
  chat.html                # Vista de pantalla completa del chatbot
tests/
  test_chat_skills.py      # Pruebas unitarias de las habilidades del chatbot
```

**Variable de entorno requerida:**

| Variable | Descripción |
|---|---|
| `GROQ_API_KEY` | API key de [Groq](https://console.groq.com/). También se acepta `GROQ_KEY`. |

**Proveedores de IA alternativos incluidos** (disponibles pero no activos por defecto):

- `app/gemini_chat.py` – Google Gemini
- `app/nvidia_chat.py` – NVIDIA NIM
- `app/elephant_chat.py` – ElephantSQL / modelos propios
- `app/groq_chat.py` – Wrapper alternativo de Groq

## 🔐 CAPTCHA en el sistema de login

Se ha integrado Google reCAPTCHA en el sistema de inicio de sesión para mejorar la seguridad y prevenir accesos automatizados.

🧠 Cambios realizados
Implementación de reCAPTCHA v2 (“No soy un robot”) en el formulario de login.
Añadido el widget en el frontend (login.html) mediante data-sitekey.
Validación del token de reCAPTCHA en el backend con Flask.
Uso de variables de entorno (.env) para almacenar las claves de forma segura.
⚙️ Backend
Verificación del reCAPTCHA mediante la API de Google antes de autenticar al usuario.
Uso de requests para validar la respuesta del usuario.
🔒 Seguridad
Protección contra bots en el inicio de sesión.
Separación de claves sensibles usando variables de entorno.
Mejora general del sistema de autenticación.

---

## 🛠️ Scripts útiles

- **`bootstrap.bat` / `bootstrap.sh`**: Crea venv, instala dependencias y carpetas necesarias.
- **`makefile`**: (Linux/macOS) Contiene atajos equivalentes (`make bootstrap`, `make run`).

---

## 📁 Estructura de archivos

```
I_S25_Web_Scraping/
├── app/
│   ├── __init__.py          # Factory de la aplicación Flask
│   ├── config.py            # Configuración centralizada
│   ├── db.py                # Gestión de bases de datos SQLite
│   ├── models.py            # Modelo User (Flask-Login)
│   ├── email_utils.py       # Utilidades para envío de emails
│   ├── chatbot.py           # Función principal del chatbot (Groq API)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Rutas principales (index, scraping, estadísticas y legales)
│   │   ├── auth.py          # Autenticación (login, registro, logout)
│   │   ├── user.py          # Panel de usuario (perfil, favoritos, alertas)
│   │   └── chat.py          # Endpoint /chatbot/api
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_client.py     # Cliente unificado de IA
│   │   └── chat_skills.py   # Habilidades del chatbot y detección de intención
│   └── scraping/
│       ├── __init__.py
│       └── boe_scraper.py   # Lógica de scraping del BOE
├── static/
│   ├── css/
│   │   └── style.css        # Estilos CSS
│   ├── img/                 # Imágenes estáticas
│   └── uploads/
│       └── profiles/        # Fotos de perfil de usuarios
├── templates/
│   ├── base.html            # Plantilla base (navbar, chatbot, accesibilidad, cookies, i18n)
│   ├── index.html           # Página principal
│   ├── login.html           # Formulario de login
│   ├── register.html        # Formulario de registro
│   ├── user.html            # Panel de usuario
│   ├── user_configuracion.html
│   ├── user_oposiciones.html
│   ├── user_newsletter.html
│   ├── tarjeta.html         # Vista de oposiciones por departamento
│   ├── chat.html            # Vista de pantalla completa del chatbot
│   ├── estadisticas.html    # Página de estadísticas de visitas
│   ├── politica_cookies.html
│   ├── politica_privacidad.html
│   ├── aviso_legal.html
│   └── emails/
│       └── nuevas_oposiciones.html
├── tests/
│   ├── test_chat_skills.py  # Pruebas unitarias de las habilidades del chatbot
│   └── test_admin_e2e.py    # Pruebas E2E del panel de administración (Playwright)
├── bootstrap.bat            # Script de bootstrap (Windows)
├── bootstrap.sh             # Script de bootstrap (Linux/macOS)
├── run.py                   # Punto de entrada de la aplicación
├── requirements.txt         # Dependencias Python
├── oposiciones.db           # Base de datos de oposiciones
└── usuarios.db              # Base de datos de usuarios
```

---

## � Página de estadísticas

Vista pública accesible desde el menú de navegación en `/estadisticas` que muestra el uso de la plataforma.

**Contenido:**

| Sección | Descripción |
|---|---|
| Gráfico de barras | Top departamentos ordenados por número de visitas (Chart.js) |
| Resumen global | Visitas autenticadas, visitas anónimas y total combinado |
| Tabla de detalle | Listado completo de departamentos con su contador de visitas |

**Cómo se registran las visitas:**

- **Usuarios autenticados**: Al hacer clic en el título o PDF de una oposición se llama a `POST /marcar_visitada/<id>` y se guarda en la tabla `visitas` de `usuarios.db`.
- **Usuarios anónimos**: El mismo endpoint, sin sesión, incrementa un contador en la tabla `visitas_global` de `usuarios.db`.
- Las estadísticas combinan ambas fuentes para mostrar el total real de interacciones.

**Implementación técnica:**

- Ruta: `GET /estadisticas` en `app/routes/main.py`.
- Enlace en el navbar con soporte de traducción ES/EN (`nav.stats`).
- Plantilla: `templates/estadisticas.html`.
- Nueva tabla SQLite: `visitas_global (oposicion_id, total_visitas, fecha_ultima_visita)`.

---

## �🔮 Próximos pasos recomendados

- ✅ Migrar a PostgreSQL para producción (mejor rendimiento con múltiples workers).
    - Migrado a Neon (PostgreSQL)
- ✅ Mejorar la interfaz de usuario con más filtros y opciones de búsqueda.
    - Filtros de búsqueda, análisis de usuarios, etc
- ✅ Implementar sistema de roles y permisos (admin, usuario, etc.).
    - Sistema de roles y permisos (admin, viewer) implementado

---

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 📞 Contacto

Si tienes preguntas o sugerencias, no dudes en abrir un issue en el repositorio.

---

**⭐ Si este proyecto te resulta útil, considera darle una estrella en GitHub.**