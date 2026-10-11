import io
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from engine import Part,build_parts,optimize,estimate
from storage import materials,save_catalog,save_quote,quote_history
from pdf_export import create_pdf

st.set_page_config(page_title="MelaminaPro | Taller",page_icon="🪚",layout="wide",initial_sidebar_state="collapsed")
st.markdown("""<style>
:root{--ink:#142b41;--accent:#eaa343}
.block-container{max-width:1360px;padding-top:1rem;padding-bottom:3rem}
h1,h2,h3{color:#18344d;letter-spacing:-.025em}
[data-testid="stMetric"]{background:#f5f8fc;padding:13px 16px;border-radius:14px;border:1px solid #e6edf5}
div.stButton > button[kind="primary"]{background:#1c5f8d;border-color:#1c5f8d;border-radius:12px}
div.stButton button{border-radius:12px;min-height:43px}
.hero-card{background:linear-gradient(115deg,#143653,#2473a0);padding:26px 28px;border-radius:19px;color:#fff;margin-bottom:15px}
.hero-card h1{color:#fff;margin:0;font-size:2rem}.hero-card p{color:#dceefa;margin:.45rem 0 0}
.cat-tile{border:1px solid #d9e6f1;background:#f5f9fd;border-radius:16px;padding:16px;margin:5px 0;min-height:115px}
.cat-tile h3{font-size:1.05rem;margin:4px 0;color:#193c5a}.cat-tile p{color:#607c91;margin:0;font-size:.81rem}
.kicker{text-transform:uppercase;letter-spacing:.13em;font-size:.73rem;font-weight:700;color:#2e75a4}
@media(max-width:700px){.block-container{padding-left:.75rem;padding-right:.75rem}.hero-card{padding:18px}.hero-card h1{font-size:1.55rem}.cat-tile{min-height:95px;padding:10px}}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero-card"><div class="kicker" style="color:#9fd9f9">TALLER · PRESUPUESTOS</div><h1>🪚 MelaminaPro</h1><p>Cotiza muebles, revisa materiales por tipo y aprovecha mejor tus tableros.</p></div>',unsafe_allow_html=True)
page=st.segmented_control('Módulos',['🧮 Cotizador','🧱 Materiales','📚 Historial','ℹ️ Ayuda'],default='🧮 Cotizador',label_visibility='collapsed')
page={'🧮 Cotizador':'Cotizar mueble','🧱 Materiales':'Catálogo de materiales','📚 Historial':'Historial','ℹ️ Ayuda':'Información técnica'}.get(page,'Cotizar mueble')
rows=materials();pricing={r['name']:r for r in rows}

if page=='Catálogo de materiales':
 st.header('Catálogo visual de materiales')
 st.caption('Precios iniciales de ejemplo en S/. Agrupa por tipo, busca productos y actualiza costos en segundos.')
 groups={
  'Tableros':('🪵','Planchas de melamina, MDF y dimensiones'),
  'Cantos':('〰️','Tapacantos PVC y acabados'),
  'Herrajes':('🔩','Bisagras, correderas y tiradores'),
  'Consumibles':('🧰','Tornillos, adhesivos y pequeños insumos'),
  'Otros':('📦','Productos y servicios adicionales')}
 categories=list(groups)
 m1,m2,m3=st.columns(3)
 m1.metric('Productos registrados',len(rows))
 m2.metric('Tipos de materiales',len({r['category'] for r in rows}))
 m3.metric('Tableros disponibles',sum(r['category']=='Tableros' for r in rows))
 if 'catalog_category' not in st.session_state:st.session_state.catalog_category='Todos'
 st.markdown('#### Explorar por categoría')
 columns=st.columns(3)
 for idx,cat in enumerate(categories):
  emoji,desc=groups[cat]
  n=sum(r['category']==cat for r in rows)
  with columns[idx%3]:
   st.markdown(f'<div class="cat-tile"><div style="font-size:1.65rem">{emoji}</div><h3>{cat} · {n}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
   if st.button('Ver '+cat,key='cat_'+cat,use_container_width=True):st.session_state.catalog_category=cat;st.rerun()
 c1,c2=st.columns([2,1])
 search=c1.text_input('🔎 Buscar material',placeholder='Ejemplo: Melamina 18, bisagra, PVC...')
 selected=c2.selectbox('Tipo', ['Todos']+categories,index=(['Todos']+categories).index(st.session_state.catalog_category) if st.session_state.catalog_category in ['Todos']+categories else 0)
 st.session_state.catalog_category=selected
 filtered=[r for r in rows if (selected=='Todos' or r['category']==selected) and search.casefold() in r['name'].casefold()]
 st.markdown(f'#### {selected if selected != "Todos" else "Todos los materiales"} · {len(filtered)} productos')
 if not filtered:st.info('No se encontraron productos con estos filtros.')
 for r in filtered:
  with st.container(border=True):
   c1,c2,c3=st.columns([3,1.4,1.3],vertical_alignment='center')
   ico=groups.get(r['category'],('📦',''))[0]
   c1.markdown(f'**{ico} {r["name"]}**')
   if r['category']=='Tableros': c1.caption(f'{int(r["width"])} × {int(r["height"])} mm · {r["unit"]}')
   else:c1.caption(f'{r["category"]} · {r["unit"]}')
   c2.markdown(f'**S/ {float(r["price"]):,.2f}**')
   with c3.popover('Editar precio',use_container_width=True):
    with st.form('price_'+r['name']):
     price=st.number_input('Nuevo precio S/',min_value=0.0,value=float(r['price']),step=1.0,key='p_'+r['name'])
     if st.form_submit_button('Guardar',type='primary'):
      updated=[{**x,'price':price} if x['name']==r['name'] else x for x in rows]
      save_catalog(updated);st.rerun()
 with st.expander('➕ Agregar un material nuevo',expanded=False):
  with st.form('new_material',clear_on_submit=True):
   n1,n2=st.columns(2)
   name=n1.text_input('Nombre del producto')
   category=n2.selectbox('Categoría',categories)
   n3,n4,n5=st.columns(3)
   unit=n3.selectbox('Unidad',['plancha','m','unidad','par','lote','kg','otro'])
   price=n4.number_input('Precio en S/',min_value=0.0,value=0.0,step=1.0)
   width=n5.number_input('Ancho mm (tableros)',min_value=0,value=0,step=10)
   height=st.number_input('Largo mm (tableros)',min_value=0,value=0,step=10)
   if st.form_submit_button('Añadir al catálogo',type='primary'):
    if not name.strip():st.error('Escribe el nombre del producto.')
    elif any(x['name'].casefold()==name.strip().casefold() for x in rows):st.error('Ya existe un producto con ese nombre.')
    elif category=='Tableros' and (width==0 or height==0):st.error('Indica las medidas del tablero.')
    else:
     save_catalog(rows+[{'category':category,'name':name.strip(),'width':width,'height':height,'price':price,'unit':unit}]);st.success('Producto añadido');st.rerun()
 with st.expander('⚙️ Edición masiva del catálogo / eliminar materiales'):
  st.warning('Los cambios en los precios afectan cotizaciones futuras. Haz una copia antes de eliminar productos usados por tus plantillas.')
  editor=st.data_editor(pd.DataFrame(rows),num_rows='dynamic',hide_index=True,use_container_width=True,column_config={'category':st.column_config.SelectboxColumn('Tipo',options=categories)})
  if st.button('Guardar todos los cambios',type='primary'):
   try:save_catalog(editor.fillna({'width':0,'height':0,'price':0,'unit':'unidad'}).to_dict('records'));st.success('Catálogo actualizado');st.rerun()
   except Exception as e:st.error(str(e))
 st.download_button('⬇ Exportar catálogo CSV',pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig'),'catalogo_melaminapro.csv','text/csv')

elif page=='Cotizar mueble':
 st.header('Nueva cotización')
 st.caption('Introduce las medidas y revisa los cálculos en tiempo real. El despiece sigue siendo editable.')
 client=st.text_input('Cliente / referencia',placeholder='Nombre del cliente')
 types=['Ropero / clóset','Cocina / gabinete','Escritorio','Repisero','Mueble de TV','Personalizado']
 kind=st.selectbox('Tipo de mueble',types)
 c1,c2,c3=st.columns(3)
 w=c1.number_input('Ancho total (mm)',min_value=200,max_value=6000,value=1800,step=50)
 h=c2.number_input('Alto total (mm)',min_value=200,max_value=6000,value=2100,step=50)
 d=c3.number_input('Fondo total (mm)',min_value=150,max_value=6000,value=550,step=25)
 a,b,c,e=st.columns(4)
 thickness=a.selectbox('Espesor (mm)',[18,15,25])
 doors=b.number_input('Puertas',0,10,2)
 drawers=c.number_input('Cajones',0,12,3)
 shelves=e.number_input('Repisas',0,15,2)
 back=st.checkbox('Incluir fondo posterior MDF de 3 mm',value=True)
 st.subheader('Costos y criterios de fabricación')
 k1,k2,k3=st.columns(3)
 labor=k1.number_input('Mano de obra (S/)',0.0,20000.0,300.0,step=25.0)
 transport=k2.number_input('Transporte e instalación (S/)',0.0,20000.0,90.0,step=10.0)
 consumables=k3.number_input('Otros consumibles (S/)',0.0,20000.0,30.0,step=5.0)
 k4,k5,k6=st.columns(3)
 waste=k4.number_input('Imprevistos (%)',0.0,50.0,5.0,step=1.0)
 margin=k5.number_input('Margen bruto (%)',0.0,90.0,25.0,step=1.0)
 tax=k6.selectbox('IGV aplicado al precio',options=[0,18],format_func=lambda x:f'{x}%')
 z1,z2=st.columns(2)
 kerf=z1.number_input('Ancho de corte / sierra (mm)',0,15,4)
 border=z2.number_input('Margen de seguridad por lado (mm)',0,50,10)
 try:
  parts=build_parts(kind,w,h,d,thickness,doors,drawers,shelves,back)
  st.subheader('📐 Despiece automático — editable')
  df=pd.DataFrame([vars(p) for p in parts])
  edited=st.data_editor(df,num_rows='dynamic',hide_index=True,use_container_width=True,column_config={'name':'Pieza','width':'Ancho (mm)','height':'Largo (mm)','qty':'Cantidad','material':st.column_config.SelectboxColumn('Material',options=[r['name'] for r in rows if r['category']=='Tableros']),'edge_ml':'Canto por pieza (m)','grain':'Veta fija'})
  newparts=[]
  for r in edited.fillna({'qty':1,'edge_ml':0,'grain':False}).to_dict('records'):
   if not str(r.get('name','')).strip():continue
   p=Part(str(r['name']),int(r['width']),int(r['height']),int(r['qty']),str(r['material']),float(r['edge_ml']),bool(r['grain']))
   if p.width<=0 or p.height<=0 or p.qty<1 or p.qty>100 or p.edge_ml<0:raise ValueError(f'Pieza inválida: {p.name}')
   newparts.append(p)
  specs={r['name']:r for r in rows if r['category']=='Tableros'}
  layout,issues=optimize(newparts,specs,kerf,border)
  if issues:
   for issue in issues:st.error(issue)
  else:
   calc=estimate(newparts,layout,pricing,labor,transport,consumables,waste,margin,tax)
   st.subheader('💰 Resumen de cotización')
   c1,c2,c3=st.columns(3)
   c1.metric('Costo estimado',f'S/ {calc["costo"]:,.2f}')
   c2.metric('Precio de venta',f'S/ {calc["precio_final"]:,.2f}')
   c3.metric('Utilidad bruta estimada',f'S/ {calc["utilidad"]:,.2f}')
   breakdown=pd.DataFrame([{'Concepto':k.replace('_',' ').title(),'S/':round(calc[k],2)} for k in ['tableros','cantos','herrajes','mano_obra','transporte','consumibles','imprevistos','igv']])
   st.dataframe(breakdown,hide_index=True,use_container_width=True)
   st.subheader('🪵 Planos de corte y aprovechamiento')
   for mat,g in layout.items():
    st.markdown(f'**{mat}: {g["qty"]} tablero(s)** — aprovechamiento aproximado {g["efficiency"]:.1%}')
    sw,sh=g['size']
    for si,s in enumerate(g['sheets']):
     fig,ax=plt.subplots(figsize=(7,5))
     ax.set_xlim(0,sw);ax.set_ylim(sh,0);ax.set_aspect('equal');ax.add_patch(plt.Rectangle((0,0),sw,sh,fill=False,linewidth=2))
     for j,p in enumerate(s['placements']):
      ax.add_patch(plt.Rectangle((p['x'],p['y']),p['width'],p['height'],fill=True,alpha=.28,edgecolor='black'))
      ax.text(p['x']+p['width']/2,p['y']+p['height']/2,p['name'][:17],ha='center',va='center',fontsize=7,clip_on=True)
     ax.set_title(f'{mat} — tablero {si+1} ({sw} × {sh} mm)');ax.set_xlabel('mm');ax.set_ylabel('mm')
     st.pyplot(fig);plt.close(fig)
   st.caption('Plan orientativo: respeta veta y separación de sierra, pero requiere revisión de taller; no optimiza globalmente todos los patrones posibles.')
   dims=f'{w} × {h} × {d}'
   pdf=create_pdf(client,kind,dims,newparts,calc,False)
   st.download_button('📄 Descargar cotización PDF',data=pdf,file_name='cotizacion_melaminapro.pdf',mime='application/pdf',type='primary')
   st.download_button('📋 Descargar despiece CSV',data=edited.to_csv(index=False).encode('utf-8-sig'),file_name='despiece.csv',mime='text/csv')
   if st.button('Guardar cotización en historial'):
    qid=save_quote(client,kind,{'dimensiones':dims,'piezas':[vars(p) for p in newparts],'costos':calc},calc['precio_final']);st.success(f'Cotización #{qid} guardada en base local')
 except Exception as err:st.error(f'Revisa los parámetros: {err}')

elif page=='Historial':
 st.header('Historial de cotizaciones')
 h=quote_history()
 if h:
  st.dataframe(pd.DataFrame(h),hide_index=True,use_container_width=True)
  st.download_button('Descargar historial CSV',pd.DataFrame(h).to_csv(index=False).encode('utf-8-sig'),'historial.csv','text/csv')
 else:st.info('Todavía no hay cotizaciones guardadas.')
else:
 st.header('Información técnica y límites')
 st.markdown('''**Importante antes de fabricar:** Este es un sistema de presupuestación preliminar, no un programa CAD/CAM ni un plano de taller certificado. Los modelos asumen cajas sencillas con tableros horizontales entre laterales, puertas sobrepuestas aproximadas y holguras orientativas. Revisa cantos, tapas, uniones, fondos, herrajes, bisagras, correderas, veta, tolerancias, espesores reales, estabilidad y condiciones de instalación.\n\n**Optimización:** algoritmo de espacios rectangulares tipo guillotina (heurístico), que permite múltiples tableros y evita rotación cuando hay veta fija. No garantiza consumo mínimo, ni modela secuenciación real de cortes de máquina.\n\n**Precios:** catálogo inicial solo ilustrativo en soles peruanos. Margen aplicado sobre el precio de venta, IGV opcional separado.\n\n**Persistencia:** SQLite local. En Streamlit Community Cloud puede perderse la información al reiniciar o desplegar; para trabajo real usa PostgreSQL gestionado o un servidor con disco persistente. No almacenes aquí datos empresariales sensibles sin resolver autenticación, backups y acceso.\n\n**Personalizado:** la plantilla genera una caja base; usa la tabla editable para agregar/quitar piezas según el diseño específico.''')
