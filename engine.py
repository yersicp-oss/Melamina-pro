"""Motor de despiece y corte 2D (heurística guillotina; no óptimo garantizado). Dimensiones mm."""
from dataclasses import dataclass, asdict
from math import ceil

@dataclass
class Part:
    name:str
    width:int
    height:int
    qty:int=1
    material:str='Melamina 18 mm'
    edge_ml:float=0.0
    grain:bool=True


def build_parts(kind,w,h,d,t=18,doors=2,drawers=0,shelves=2,back=True):
    """Modelos preliminares de mueble tipo caja; validar sistema constructivo y holguras en taller."""
    w,h,d,t=map(int,(w,h,d,t)); doors=int(doors);drawers=int(drawers);shelves=int(shelves)
    if min(w,h,d)<150 or max(w,h,d)>6000 or t not in (15,18,25):
        raise ValueError('Dimensiones fuera del rango permitido o espesor inválido')
    if w <= 2*t+30 or h <= 2*t+30: raise ValueError('Dimensiones insuficientes')
    main=f'Melamina {t} mm'; inner_w=w-2*t
    p=[Part('Lateral',d,h,2,main,(d+h)/1000,True),
       Part('Tapa superior',inner_w,d,1,main,inner_w/1000,True),
       Part('Base inferior',inner_w,d,1,main,inner_w/1000,True)]
    if kind=='Escritorio':
        p=[Part('Tablero de escritorio',w,d,1,main,(w+2*d)/1000,True),
           Part('Pata lateral',d,h-t,2,main,(d+h-t)/1000,True),
           Part('Faldón trasero',inner_w,250,1,main,inner_w/1000,True)]
    elif kind=='Repisero':
        p += [Part('Repisa interior',inner_w,d-15,shelves,main,inner_w/1000,True)] if shelves else []
    else:
        if shelves: p.append(Part('Repisa interior',inner_w,d-15,shelves,main,inner_w/1000,True))
        if kind=='Ropero / clóset':
            p.append(Part('División vertical',d-15,h-2*t,1,main,(h-2*t)/1000,True))
        if doors:
            # Holguras aproximadas de puerta sobrepuesta, junta 3 mm
            usable=w-6-(doors-1)*3
            door_w=usable//doors
            p.append(Part('Puerta',door_w,h-6,doors,main,2*(door_w+h-6)/1000,True))
    if drawers:
        # Caja orientativa, no reemplaza especificación de correderas
        drawer_w=max(120,(inner_w-26)//max(1,min(drawers,2)))
        for j in range(drawers):
            p.extend([Part(f'Cajón {j+1} frente',drawer_w,180,1,main,(drawer_w+180)/1000,True),
                      Part(f'Cajón {j+1} costado',max(150,d-55),130,2,main,0,False),
                      Part(f'Cajón {j+1} posterior',max(100,drawer_w-2*t),130,1,main,0,False)])
    if back and kind!='Escritorio': p.append(Part('Fondo posterior',w,h,1,'MDF 3 mm',0,False))
    return p


def optimize(parts, sheet_specs, kerf=4, margin=10):
    """Packing con espacios libres rectangulares, sin girar piezas con veta; no busca óptimo global."""
    result={}; unfit=[]
    for material in sorted({p.material for p in parts}):
        spec=sheet_specs.get(material)
        if not spec: unfit.append(f'Sin tablero configurado: {material}');continue
        SW,SH=int(spec['width']),int(spec['height']); usable_w=SW-2*margin;usable_h=SH-2*margin
        if usable_w<=0 or usable_h<=0: unfit.append(f'Tablero inválido: {material}');continue
        expanded=[{'part':p.name,'width':p.width,'height':p.height,'edge_ml':p.edge_ml/p.qty if False else p.edge_ml,'grain':p.grain} for p in parts if p.material==material for _ in range(p.qty)]
        expanded.sort(key=lambda x:x['width']*x['height'],reverse=True)
        sheets=[]
        for item in expanded:
            candidates=[]
            for si,s in enumerate(sheets):
                for fi,(fx,fy,fw,fh) in enumerate(s['free']):
                    for rotated in ([item['height'] > item['width']] if item['grain'] else [False,True]):
                        pw,ph=(item['height'],item['width']) if rotated else (item['width'],item['height'])
                        if pw<=fw and ph<=fh: candidates.append((fw*fh-pw*ph,si,fi,pw,ph,rotated))
            if not candidates:
                candidates0=[]
                for rot in ([item['height'] > item['width']] if item['grain'] else [False,True]):
                    pw,ph=(item['height'],item['width']) if rot else (item['width'],item['height'])
                    if pw<=usable_w and ph<=usable_h: candidates0.append((pw,ph,rot))
                if not candidates0:
                    unfit.append(f"{material}: {item['part']} {item['width']} × {item['height']} no cabe en tablero {SW} × {SH}")
                    continue
                sheets.append({'free':[(margin,margin,usable_w,usable_h)],'placements':[]})
                si=len(sheets)-1;fi=0;pw,ph,rotated=candidates0[0]
            else:
                _,si,fi,pw,ph,rotated=min(candidates)
            s=sheets[si]; x,y,fw,fh=s['free'].pop(fi)
            s['placements'].append({'x':x,'y':y,'width':pw,'height':ph,'name':item['part'],'rotated':rotated})
            # separación de sierra; dos rectángulos disjuntos (guillotina)
            right=(x+pw+kerf,y,fw-pw-kerf,ph)
            below=(x,y+ph+kerf,fw,fh-ph-kerf)
            for r in (right,below):
                if r[2]>0 and r[3]>0:s['free'].append(r)
        area=sum(i['width']*i['height'] for i in expanded if not any(i['part'] in u for u in unfit))
        result[material]={'sheets':sheets,'size':(SW,SH),'qty':len(sheets),'area_m2':area/1e6,'efficiency':(area/(len(sheets)*SW*SH) if sheets else 0)}
    return result,unfit


def estimate(parts, layouts, prices, labor, transport, consumables, waste_pct, margin_pct, tax_pct=0):
    board_cost=sum(group['qty']*float(prices.get(mat,{}).get('price',0)) for mat,group in layouts.items())
    edge=sum(p.edge_ml*p.qty for p in parts)*float(prices.get('Canto PVC',{}).get('price',0))
    hardware=sum(p.qty*float(prices.get('Bisagra',{}).get('price',0))* (ceil(p.height/750) if p.name=='Puerta' else 0) for p in parts)
    hardware+=sum(1 for p in parts if 'Cajón' in p.name and 'frente' in p.name)*float(prices.get('Corredera',{}).get('price',0))
    base=board_cost+edge+hardware+float(labor)+float(transport)+float(consumables)
    waste=base*float(waste_pct)/100
    total_cost=base+waste
    if margin_pct>=100: raise ValueError('El margen debe ser inferior a 100 %')
    sale=total_cost/(1-margin_pct/100)
    return dict(tableros=board_cost,cantos=edge,herrajes=hardware,mano_obra=float(labor),transporte=float(transport),consumibles=float(consumables),imprevistos=waste,costo=total_cost,precio_sin_igv=sale,igv=sale*tax_pct/100,precio_final=sale*(1+tax_pct/100),utilidad=sale-total_cost)
