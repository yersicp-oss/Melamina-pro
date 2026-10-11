import io
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from engine import Part,build_parts,optimize,estimate
from storage import materials,save_catalog,save_quote,quote_history
from pdf_export import create_pdf

st.set_page_config(page_title='MelaminaPro | Cotizaciones',page_icon='🪚',layout='wide')
st.markdown('''<style>h1,h2,h3{color:#163657}.block-container{padding-top:1.3rem} @media(max-width:650px){.block-container{padding-left:1rem;padding-right:1rem}}</style>''',unsafe_allow_html=True)
st.title('🪚 MelaminaPro')
st.caption('Cotizaciones, despiece y aprovechamiento de tableros | Precios de ejemplo: actualízalos según tus proveedores.')
page=st.sidebar.radio('Navegación',['Cotizar mueble','Catálogo de materiales','Historial','Información técnica'])
rows=materials();pricing={r['name']:r for r in rows}

if page=='Catálogo de materiales':
 st.header('Catálogo de materiales y precios')
 st.info('Los importes son ilustrativos, NO precios verificados de tiendas. Edítalos antes de cotizar.')
 categories=sorted({r['category'] for r in rows})
 cat=st.selectbox('Filtrar por tipo',['Todos']+categories)
 filtered=[r for r in rows if cat=='Todos' or r['category']==cat]
 st.dataframe(pd.DataFrame(filtered).rename(columns={'category':'Categoría','name':'Material','width':'Ancho mm','height':'Largo mm','price':'Precio S/','unit':'Unidad'}),hide_index=True,use_container_width=True)
 st.subheader('Editar catálogo completo')
 edited=st.data_editor(pd.DataFrame(rows),num_rows='dynamic',hide_index=True,use_container_width=True,column_config={'category':st.column_config.SelectboxColumn('Tipo',options=['Tableros','Cantos','Herrajes','Consumibles','Otros'])})
 if st.button('Guardar catálogo',type='primary'):
  try:save_catalog(edited.fillna({'width':0,'height':0,'price':0,'unit':'unidad'}).to_dict('records'));st.success('Catálogo actualizado');st.rerun()
  except Exception as e:st.error(str(e))
 st.caption('Puedes agregar nuevos herrajes o tableros; el motor de corte usa los materiales definidos en las piezas.')

elif page=='Cotizar mueble':
 st.header('Nueva cotización')
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
  st.subheader('Despiece automático — editable')
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
   st.subheader('Resultado económico')
   c1,c2,c3=st.columns(3)
   c1.metric('Costo estimado',f'S/ {calc["costo"]:,.2f}')
   c2.metric('Precio de venta',f'S/ {calc["precio_final"]:,.2f}')
   c3.metric('Utilidad bruta estimada',f'S/ {calc["utilidad"]:,.2f}')
   breakdown=pd.DataFrame([{'Concepto':k.replace('_',' ').title(),'S/':round(calc[k],2)} for k in ['tableros','cantos','herrajes','mano_obra','transporte','consumibles','imprevistos','igv']])
   st.dataframe(breakdown,hide_index=True,use_container_width=True)
   st.subheader('Plan de corte por tablero')
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
