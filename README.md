

# 📚 BOE Oposiciones – Web Scraping y Portal de Usuarios

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


Aplicación Flask que sincroniza diariamente la sección 2B del BOE (oposiciones), la guarda en SQLite y ofrece un panel para que cada usuario pueda filtrar oportunidades, marcarlas como favoritas o visitadas, configurar alertas por email y mantener su perfil actualizado.

---

## 📑 Tabla de Contenidos

- [📚 BOE Oposiciones – Web Scraping y Portal de Usuarios](#-boe-oposiciones--web-scraping-y-portal-de-usuarios)
  - [📑 Tabla de Contenidos](#-tabla-de-contenidos)
  - [✨ Características principales](#-características-principales)
  - [📋 Requisitos previos](#-requisitos-previos)
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

El script crea/activa `venv`, instala dependencias y garantiza la carpeta `static/uploads/profiles`.

#### 3. Activar el entorno virtual (si no usaste el bootstrap)

**Windows:**
```powershell
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Ejecutar la aplicación

```bash
python run.py
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
  scraping/
    boe_scraper.py     # Lógica de scraping y sincronización del BOE.
  routes/
    main.py            # Landing, sincronización y estadísticas.
    auth.py            # Registro, login, logout y cambio de contraseña.
    user.py            # Panel del usuario, filtros, favoritos y perfil.
static/                # CSS, imágenes y uploads de perfiles.
templates/             # Base + vistas (index, login, registro, user_* ...).
run.py                 # Punto de entrada (crea la app y lanza Flask).
bootstrap.(bat|sh)     # Scripts para preparar el entorno.
requirements.txt       # Dependencias de Python.
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
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Rutas principales (index, scraping)
│   │   ├── auth.py          # Autenticación (login, registro, logout)
│   │   └── user.py          # Panel de usuario (perfil, favoritos, alertas)
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
│   ├── base.html            # Plantilla base
│   ├── index.html           # Página principal
│   ├── login.html           # Formulario de login
│   ├── register.html        # Formulario de registro
│   ├── user.html            # Panel de usuario
│   ├── user_configuracion.html
│   ├── user_oposiciones.html
│   ├── user_newsletter.html
│   ├── tarjeta.html         # Vista de oposiciones por departamento
│   └── emails/
│       └── nuevas_oposiciones.html
├── bootstrap.bat            # Script de bootstrap (Windows)
├── bootstrap.sh             # Script de bootstrap (Linux/macOS)
├── run.py                   # Punto de entrada de la aplicación
├── requirements.txt         # Dependencias Python
├── oposiciones.db          # Base de datos de oposiciones
└── usuarios.db             # Base de datos de usuarios
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
