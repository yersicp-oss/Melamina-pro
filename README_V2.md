# MelaminaPro v2 — Catálogo visual

## Cambios
- Inicio y navegación superior por módulos.
- Catálogo agrupado por tipo: Tableros, Cantos, Herrajes, Consumibles y Otros.
- Tarjetas visuales por categoría, búsqueda, filtro y edición rápida de precios.
- Alta de materiales y edición masiva con validación.
- Cotizador original, despiece editable, optimización 2D, PDF e historial conservados.

## Instalación local
```
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud
Subir `app.py`, `engine.py`, `storage.py`, `pdf_export.py` y `requirements.txt` a la raíz de un repositorio y desplegar `app.py`. Los precios iniciales son de ejemplo.

**Aviso importante:** el almacenamiento SQLite local en Streamlit Community Cloud no es persistente; usa PostgreSQL externo antes de hacer cotizaciones comerciales en producción. El despiece y los patrones de corte deben revisarse por el fabricante antes de cortar.
