# GELETRIC — prototipo Django

Versión Django del prototipo de Inicio de GELETRIC (software de gestión para
cooperativas eléctricas — CEYSA / Cooperativa San Manuel). Convierte el
prototipo HTML/CSS/JS a un proyecto Django corrible, con la misma UI pero
servida por vistas y templates reales.

Es intencionalmente un **scaffold sin modelos todavía**: los datos del
dashboard (estadísticas, tareas, novedades, estado de la red, serie de
consumo) están hardcodeados en `core/sample_data.py`, tal como estaban en el
HTML original, pero ahora del lado del servidor. La idea es que sirva de
punto de partida para conectar los módulos reales a medida que se cierren las
Historias de Usuario correspondientes (ver la guía de diseño de San Manuel).

## Arrancar

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abrir http://127.0.0.1:8000/

## Estructura

```
geletric/                  proyecto Django (settings, urls raíz)
core/                       la única app por ahora
  modules_data.py           los 10 módulos (slug, ícono, color, funcionalidades) — fuente única
  sample_data.py            datos de ejemplo del dashboard (stats, tareas, novedades, red, consumo)
  context_processors.py     inyecta `modules` en todos los templates (para el menú lateral)
  views.py                  home() y module_detail(slug)
  urls.py                   / y /modulos/<slug>/
  templates/core/
    base.html                shell: sidebar + topbar + sprite de íconos SVG
    home.html                el dashboard de Inicio
    module.html               placeholder de módulo (reutilizado por los 10 módulos)
  static/core/
    css/dashboard.css        toda la UI (tokens de color claro/oscuro, layout, componentes)
    js/dashboard.js           menú mobile, gráfico de línea y donut (leen datos vía json_script)
```

## Cómo agregar un módulo real

1. El listado y las funcionalidades de cada módulo viven en
   `core/modules_data.py` — es la única fuente de verdad para el menú
   lateral, los accesos rápidos y `/modulos/<slug>/`. Ajustarlo a medida que
   el catálogo funcional (`catalogo-funcional-10-modulos.md`) se vaya
   confirmando por Historia de Usuario.
2. Cuando un módulo tenga modelos reales, agregar una app Django propia (por
   ejemplo `asociados/`) con sus modelos, migraciones y vistas, y apuntar la
   URL de ese módulo (`core/urls.py` o una nueva ruta) a esa app en vez de al
   `module_detail` genérico. `module.html` sigue sirviendo como placeholder
   para los módulos que todavía no tienen pantalla propia.
3. Los datos del Inicio (`core/sample_data.py`) están pensados para
   reemplazarse función por función por consultas al ORM — la vista
   (`core/views.py`) no necesita cambiar de forma, solo de dónde saca los
   datos.

## Convenciones de diseño

- **Colores por módulo**: cada módulo tiene un color fijo (`--mod-<color>` y
  `--mod-<color>-bg` en `dashboard.css`) que se usa en ícono, badge y acento
  en toda la interfaz — nunca un color plano ad hoc.
- **Claro/oscuro**: los tokens de color están separados de los componentes;
  `dashboard.css` ya soporta `prefers-color-scheme: dark` además de
  `data-theme="dark"` explícito.
- **"A confirmar"**: la guía de diseño de San Manuel define borde punteado +
  asterisco para funcionalidades que vienen del sistema actual pero no están
  confirmadas por una Historia de Usuario. Ese tratamiento visual todavía no
  está implementado acá — agregarlo en `module.html`/`dashboard.css` cuando
  se necesite marcar ítems así.

## Qué falta a propósito

- Sin autenticación real (el usuario "Juan Pérez" del topbar es estático).
- Sin base de datos de negocio (solo las tablas por defecto de Django:
  auth, sessions, admin).
- Sin la ventana con solapas de "Ficha del asociado" (8 solapas) — es una
  pantalla aparte, ya prototipada en HTML, que no se migró en esta primera
  vuelta.
