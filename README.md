

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
  - [�️ Migración a SQLAlchemy (2026-04-28)](#-migración-a-sqlalchemy-2026-04-28)
  - [�📋 Requisitos previos](#-requisitos-previos)
  - [🚀 Instalación y configuración](#-instalación-y-configuración)
    - [Puesta en marcha rápida](#puesta-en-marcha-rápida)
      - [1. Clonar o descargar el proyecto](#1-clonar-o-descargar-el-proyecto)
      - [2. Ejecutar el script de bootstrap](#2-ejecutar-el-script-de-bootstrap)
      - [3. Activar el entorno virtual (si no usaste el bootstrap)](#3-activar-el-entorno-virtual-si-no-usaste-el-bootstrap)
      - [4. Ejecutar la aplicación](#4-ejecutar-la-aplicación)
    - [Configuración y variables de entorno](#configuración-y-variables-de-entorno)
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
- **📊 Seguimiento de actividad**: Cada click marca visitas y favoritos para personalizar las tarjetas.
- **🎨 Tema claro/oscuro** y subida de foto de perfil almacenada en `static/uploads/profiles`.
- **🍪 Banner de cookies**: Aviso de política de cookies con preferencias granulares, persistido en `localStorage`.
- **⚖️ Cumplimiento legal básico**: Enlaces permanentes en footer a política de cookies, política de privacidad y aviso legal.
- **🌐 Selector de idioma**: Botón EN / ES en la cabecera que traduce toda la interfaz estática al instante sin recargar la página.
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
| `GROQ_API_KEY`      | API Key para respuestas IA del endpoint `/api/chatbot` | *(sin valor por defecto)*     |

**⚠️ IMPORTANTE:** En producción define estas variables antes de arrancar (`set VAR=...` en Windows o `export VAR=...` en Linux/macOS).

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
- `como hacer una paella?` -> bloqueo por fuera de dominio.
- `resumen del boe-a-2026-8444` -> respuesta directa orientada a resumen de referencia.
- `Busca oposiciones en Madrid para hoy` -> respuesta IA (requiere `GROQ_API_KEY`).
- `resumen del artículo 5 de esa norma` -> no bloquea y aplica fallback si falta contexto.

---

## 🏗️ Arquitectura del proyecto

```
app/
  __init__.py          # Crea la app, registra blueprints, filtros y temas.
  chatbot.py           # Cliente Groq + selector de system prompt (v1/v2).
  config.py            # Configuración centralizada.
  db.py                # Conexiones y migraciones SQLite.
  models.py            # Modelo User (Flask-Login).
  services/
    chat_skills.py     # Capa de skills: bloqueo de dominio + ruteo de intención.
  email_utils.py       # Helpers para enviar newsletters.
  chatbot.py           # Función principal del chatbot (llama a Groq API).
  scraping/
    boe_scraper.py     # Lógica de scraping y sincronización del BOE.
  routes/
    main.py            # Landing, scraping, estadísticas y páginas legales.
    auth.py            # Autenticación (login, registro, logout).
    user.py            # Panel del usuario, filtros, favoritos y perfil.
    chat.py            # Endpoint /chatbot/api y ruta /chat.
  services/
    ai_client.py       # Cliente unificado de IA (Groq + proveedores alternativos).
    chat_skills.py     # Habilidades del chatbot: detección de intención y búsqueda en BD.
static/                # CSS, imágenes y uploads de perfiles.
templates/             # Base + vistas (index, login, registro, user_*, chat ...).
run.py                 # Punto de entrada (crea la app y lanza Flask).
bootstrap.(bat|sh)     # Scripts para preparar el entorno.
requirements.txt       # Dependencias de Python.
tests/
  test_chat_skills.py  # Pruebas unitarias de las habilidades del chatbot.
```

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
- El botón muestra `EN` cuando el idioma activo es español, y `ES` cuando es inglés.

**Elementos traducidos:**

| Zona | Textos traducidos |
|---|---|
| Navbar | Menú de usuario, login, registro, cerrar sesión |
| Panel de accesibilidad | Título, descripciones y todos los botones |
| Chatbot | Título, saludo de bienvenida, placeholder y botón Enviar |
| Banner de cookies | Texto informativo, botones y modal de configuración |

**Implementación técnica:**

- Sistema i18n 100% client-side en `templates/base.html` (sin librerías externas).
- Los elementos a traducir llevan el atributo `data-i18n="clave"` (o `data-i18n-placeholder` para inputs).
- El diccionario de traducciones vive en un objeto JS con las claves `es` y `en`.
- El atributo `lang` del elemento `<html>` se actualiza automáticamente al cambiar de idioma.
- El contenido dinámico (oposiciones del BOE) permanece en español al provenir de la base de datos.

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

- Añadidas ModelViews para:
  - Oposiciones
  - Favoritas
  - Visitas
  - Suscripciones

- Integración con relaciones de SQLAlchemy
- Acceso restringido solo a usuarios con rol `admin`
- Panel completamente funcional para administración

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
- **Vista dedicada**: Página completa del chat disponible en `/chat` (`templates/chat.html`).

**Arquitectura del chatbot:**

```
app/
  chatbot.py               # Función principal que llama a Groq API
  services/
    ai_client.py           # Cliente unificado (Groq + fallback a otros proveedores)
    chat_skills.py         # Habilidades: búsqueda en BD, detección de intención, filtrado
  routes/
    chat.py                # Blueprint /chatbot/api (POST) y ruta /chat (GET)
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
│   │   └── chat.py          # Endpoint /chatbot/api y vista /chat
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
│   ├── politica_cookies.html
│   ├── politica_privacidad.html
│   ├── aviso_legal.html
│   └── emails/
│       └── nuevas_oposiciones.html
├── tests/
│   └── test_chat_skills.py  # Pruebas unitarias de las habilidades del chatbot
├── bootstrap.bat            # Script de bootstrap (Windows)
├── bootstrap.sh             # Script de bootstrap (Linux/macOS)
├── run.py                   # Punto de entrada de la aplicación
├── requirements.txt         # Dependencias Python
├── oposiciones.db           # Base de datos de oposiciones
└── usuarios.db              # Base de datos de usuarios
```

---

## 🔮 Próximos pasos recomendados

- ✅ Migrar a PostgreSQL para producción (mejor rendimiento con múltiples workers).
- ✅ Añadir tests unitarios y de integración.
- ✅ Implementar rate limiting.
- ✅ Configurar monitoreo y logging (Sentry, Loggly, etc.).
- ✅ Añadir CI/CD con GitHub Actions o GitLab CI.
- ✅ Mejorar la interfaz de usuario con más filtros y opciones de búsqueda.
- ✅ Implementar sistema de roles y permisos (admin, usuario, etc.).

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
