# Montor

App web de control de gastos e ingresos en pesos, dólares y euros, pensada para
Argentina (cotización oficial BNA, inflación INDEC). Incluye viajes con
seguimiento en dólares, presupuestos, gastos recurrentes, un bot de WhatsApp
que interpreta mensajes en lenguaje natural con IA (Gemini), y un resumen
mensual también generado con IA.

[![Tests](https://github.com/nicolasploskinos/montor_app/actions/workflows/tests.yml/badge.svg)](https://github.com/nicolasploskinos/montor_app/actions/workflows/tests.yml)

## Stack

- **Backend**: Flask (Python), sesiones propias con contraseñas hasheadas (no usa Supabase Auth)
- **Base de datos**: Supabase (Postgres), accedida vía la API REST con la key `anon`
- **IA**: Google Gemini (`google-genai`) — interpretación de mensajes de WhatsApp, chat de preguntas, resumen mensual
- **Pagos**: MercadoPago (suscripciones recurrentes, mensual o anual)
- **Frontend**: en migración a React + TypeScript (Vite). Las páginas ya migradas
  viven en `frontend/`; las que faltan siguen siendo Jinja + JS vanilla en `templates/`
- **Hosting**: PythonAnywhere

## Frontend (migración a React)

El frontend está pasando de Jinja + JS vanilla a **React + TypeScript**, página
por página. Las dos formas conviven: Flask sirve el cascarón `templates/spa.html`
para las rutas ya migradas y las plantillas Jinja de siempre para el resto. El
backend no cambia — todo sale de los mismos endpoints JSON de `/api/montor/…`.

**Migrado hasta ahora:** `/montor/analisis`.
**Pendiente:** `/montor` (panel), `/montor/viajes`, login y landing.

```
frontend/
  src/
    api/          cliente HTTP tipado + hooks de TanStack Query
    components/   piezas compartidas (barra lateral, header)
    features/     una carpeta por página; la lógica pura va en su .ts aparte
    hooks/        preferencias (tema/idioma), animaciones
    i18n/         textos ES/EN
    styles/       tokens de color y estilos base
```

### Cómo trabajar

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, con proxy de /api al Flask local
npm run build      # compila a ../static/app/ (esto es lo que se despliega)
npm run typecheck  # TypeScript sin generar nada
```

> **Importante:** PythonAnywhere no corre Node, así que el resultado del build
> (`static/app/`) **se commitea**. Después de tocar cualquier cosa dentro de
> `frontend/`, hay que correr `npm run build` y commitear también `static/app/`,
> si no el deploy sigue sirviendo el bundle viejo. Flask le agrega `?v=<mtime>`
> al `<script>` para invalidar la cache del navegador en cada deploy.

Para que el frontend sepa quién es el usuario y qué plan tiene sin depender de
variables de Jinja, existe `GET /api/montor/me`. Es la única ruta con sesión que
contesta **401 con JSON** en vez de redirigir al login: quien la llama es un
`fetch`, y un 302 a HTML no le sirve.

## Estructura del proyecto

El backend está separado por área en vez de vivir en un único archivo:

```
montor_server.py     # "core": Flask app, cliente de Supabase/Gemini, helpers
                        # compartidos (auth, moneda, WhatsApp, stats), y el
                        # registro de los blueprints de abajo
routes_paginas.py       # páginas HTML (landing, dashboard, login)
routes_auth.py          # login / registro
routes_montor.py        # transacciones, export, import, presupuestos,
                        # recurrentes, stats, resumen con IA
routes_viajes.py        # viajes (gastos con seguimiento en USD/EUR)
routes_whatsapp.py      # vinculación y webhook del bot de WhatsApp
routes_pagos.py         # suscripción Pro vía MercadoPago
```

Cada `routes_*.py` accede a lo compartido (`db`, `genai`, helpers, caches) vía
`import montor_server as core` — nunca `from montor_server import x` — para
que los tests puedan seguir reemplazando esos atributos con mocks
(`monkeypatch.setattr(app_module, "db", fake_db)`, etc.) sin importar en qué
archivo termine viviendo el código que los usa.

`montor_desktop.py`, en la raíz, es una app de escritorio (Tkinter) separada —
un cliente alternativo, no forma parte de la app web.

## Levantar el proyecto local

```bash
pip install -r requirements-dev.txt
python montor_server.py
```

Necesita un archivo `.env` en la raíz con, como mínimo:

| Variable | Para qué |
|---|---|
| `SUPABASE_URL`, `SUPABASE_KEY` | Conexión a la base (Postgres vía Supabase) |
| `SECRET_KEY` | Firma de las cookies de sesión de Flask |

Y, opcionalmente, según qué features quieras probar:

| Variable | Feature |
|---|---|
| `GEMINI_API_KEY` | Resumen mensual con IA, interpretación de WhatsApp, chat de preguntas |
| `MP_ACCESS_TOKEN` | Suscripción Pro (MercadoPago) |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_DISPLAY_NUMBER`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET` | Bot de WhatsApp (Meta Cloud API) |
| `BASE_URL` | URL pública del sitio (para webhooks de Meta/MercadoPago); si no está, se infiere del request |

Sin esas variables opcionales, esas features fallan de forma controlada (mensajes
de error claros) en vez de romper el resto de la app.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Los tests nunca tocan la base de datos ni ninguna API externa (Supabase, Gemini,
MercadoPago, WhatsApp) — todo se reemplaza por mocks en `tests/conftest.py` y en
cada archivo de test. Corren en menos de 10 segundos.

## Linter

```bash
ruff check .
```

Config en `ruff.toml`. Corre automáticamente en cada push/PR vía GitHub Actions
(`.github/workflows/tests.yml`), junto con los tests.

## Seguridad

- Contraseñas hasheadas con `werkzeug.security` (nunca en texto plano)
- Rate limiting en login: 5 intentos fallidos por usuario bloquean 15 minutos
- Cookies de sesión con `Secure`, `HttpOnly` y `SameSite=Lax`
- Row Level Security habilitado en todas las tablas de Supabase
- El bot de WhatsApp está restringido a una sola cuenta (la app de Meta está en
  modo desarrollo, sin Business Verification — ver comentario en
  `montor_server.py` junto a `_WHATSAPP_USER_ID`)

## Deploy

Corre en PythonAnywhere. No hay deploy automático: hay que hacer `git pull` en
una consola de PythonAnywhere y recargar la web app desde su dashboard (o vía
su API) después de cada push a `main`.
