import sqlite3,json
from pathlib import Path
DB=Path('melaminapro.db')
DEFAULT=[('Tableros','Melamina 18 mm',2440,1830,185,'plancha'),('Tableros','Melamina 15 mm',2440,1830,160,'plancha'),('Tableros','Melamina 25 mm',2440,1830,245,'plancha'),('Tableros','MDF 3 mm',2440,1830,55,'plancha'),('Cantos','Canto PVC',0,0,2.5,'m'),('Herrajes','Bisagra',0,0,5,'unidad'),('Herrajes','Corredera',0,0,22,'par'),('Herrajes','Tirador',0,0,8,'unidad'),('Consumibles','Tornillos/adhesivos',0,0,20,'lote')]
def connect():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS catalog(category TEXT,name TEXT PRIMARY KEY,width INTEGER,height INTEGER,price REAL,unit TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS quotes(id INTEGER PRIMARY KEY AUTOINCREMENT,created TEXT,client TEXT,kind TEXT,details TEXT,total REAL)')
 if not c.execute('SELECT COUNT(*) FROM catalog').fetchone()[0]:
  c.executemany('INSERT INTO catalog VALUES (?,?,?,?,?,?)',DEFAULT)
 c.commit();return c
def materials():
 with connect() as c:return [dict(x) for x in c.execute('SELECT * FROM catalog ORDER BY category,name')]
def save_catalog(rows):
 names=set()
 with connect() as c:
  for r in rows:
   name=str(r['name']).strip()
   if not name or name in names:raise ValueError('Nombres vacíos o repetidos en el catálogo')
   names.add(name)
   price=float(r['price']);w=int(r['width']);h=int(r['height'])
   if price<0 or w<0 or h<0:raise ValueError('Precio o medidas negativas')
  c.execute('DELETE FROM catalog')
  c.executemany('INSERT INTO catalog VALUES (?,?,?,?,?,?)',[(r['category'],r['name'],int(r['width']),int(r['height']),float(r['price']),r['unit']) for r in rows]);c.commit()
def save_quote(client,kind,details,total):
 from datetime import datetime
 with connect() as c:
  cur=c.execute('INSERT INTO quotes(created,client,kind,details,total) VALUES (?,?,?,?,?)',(datetime.now().isoformat(timespec='seconds'),client,kind,json.dumps(details,ensure_ascii=False),total));c.commit();return cur.lastrowid
def quote_history():
 with connect() as c:return [dict(x) for x in c.execute('SELECT id,created,client,kind,total FROM quotes ORDER BY id DESC')]
