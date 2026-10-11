from io import BytesIO
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from xml.sax.saxutils import escape

def create_pdf(client,kind,dimensions,parts,estimate,show_breakdown=False):
 out=BytesIO();doc=SimpleDocTemplate(out,pagesize=(210*mm,297*mm),leftMargin=16*mm,rightMargin=16*mm)
 styles=getSampleStyleSheet();story=[]
 story.append(Paragraph('MELAMINAPRO | COTIZACIÓN',styles['Title']))
 story.append(Paragraph('Presupuesto referencial sujeto a verificación de medidas y especificaciones.',styles['Normal']));story.append(Spacer(1,10))
 for label,val in [('Cliente',client or 'Sin nombre'),('Mueble',kind),('Dimensiones (mm)',dimensions)]:story.append(Paragraph(f'<b>{label}:</b> {escape(str(val))}',styles['Normal']))
 story.append(Spacer(1,12))
 story.append(Paragraph(f'<b>PRECIO TOTAL: S/ {estimate["precio_final"]:,.2f}</b>',styles['Heading2']))
 if show_breakdown:
  data=[['Concepto','Importe S/']]+[[label,f'{estimate[key]:,.2f}'] for label,key in [('Tableros','tableros'),('Cantos','cantos'),('Herrajes','herrajes'),('Mano de obra','mano_obra'),('Transporte','transporte'),('Consumibles','consumibles'),('Imprevistos','imprevistos')]]
  t=Table(data,colWidths=[110*mm,60*mm]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf2fb')),('GRID',(0,0),(-1,-1),.25,colors.grey),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([Spacer(1,14),t])
 story.append(Spacer(1,15));story.append(Paragraph('Incluye presupuesto preliminar. No constituye plano de fabricación. Precio y validez sujetos a confirmación.',styles['Normal']))
 doc.build(story);return out.getvalue()
