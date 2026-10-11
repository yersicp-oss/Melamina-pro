# MelaminaPro — Cotización, despiece y corte

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en Streamlit Community Cloud
Subir `app.py`, `engine.py`, `storage.py`, `pdf_export.py` y `requirements.txt` al mismo nivel del repositorio y elegir `app.py` como archivo principal.

## Advertencias
- Los precios iniciales son ejemplos y deben editarse.
- El despiece es preliminar; validar diseño, herrajes, holguras y estabilidad antes de fabricar.
- El algoritmo de corte 2D es heurístico, **no** garantiza óptimo y la disposición no es necesariamente una secuencia de cortes ejecutable en una máquina.
- SQLite es local y no persistente de manera fiable en Streamlit Community Cloud. Para un uso profesional migrar a DB administrada persistente, autenticación y backups.
- Catálogo: tipos Tableros/Cantos/Herrajes/Consumibles/Otros. El cálculo automático incluye tableros, canto PVC, bisagras estimadas y correderas por cajón; otros accesorios se incorporan mediante consumibles u otros ajustes manuales.
