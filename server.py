#!/usr/bin/env python3
"""GPU workshop: standard-library HTTP service + persistent SQLite."""
import argparse, hashlib, json, os, re, sqlite3, time, uuid
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
ROOT=Path(__file__).parent
DB=Path(os.environ.get('GPU_DB',str(ROOT/'data/workshop.sqlite3')))
BASE='/workshop'
EN_PROJECTS={
 'price-monitor':('B2B','A price monitoring system deployed for a regional liquor store chain. It collects prices from four competitors, compares the price index, supports price approval by the commercial team, and checks updated prices against 1C data.'),
 'pinock-space':('Graphic content','An AI art gallery that automatically creates cosmic images. Explore, download, and edit them.'),
 'aiconic-space':('Written content','A stream of AI articles about tools and automation, with links to sources.'),
 'actor-replacement-studio':('Video and voice','A web studio for replacing a character and voice in a video. Try the public version.'),
 'codex-limits':('Tools','A macOS widget for monitoring Codex usage across separate accounts, including weekly remaining limits and reset times. Open source.'),
 'a5ed425d-f006-435e-ae60-0e9319e1b6c7':('Finance','Explore routes for cross-border transfers using estimates from public market data.'),
 'yukaresearch':('Research','Explore Kickstarter electronics projects, compare funding, and find ideas to investigate.'),
 'logo-maker':('Graphic content','A logo concept generator from a brand description. The old page is unavailable; you can ask to bring it back.')
}

def connect():
 db=sqlite3.connect(DB,timeout=15); db.row_factory=sqlite3.Row; return db

def init():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with connect() as d:
  d.executescript('''PRAGMA journal_mode=WAL;
  CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL,category TEXT NOT NULL,status TEXT NOT NULL,url TEXT NOT NULL,author TEXT NOT NULL,created INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS submissions(id TEXT PRIMARY KEY,kind TEXT NOT NULL,project_id TEXT,title TEXT NOT NULL,description TEXT NOT NULL,contact TEXT NOT NULL,url TEXT NOT NULL,author TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS limits(ip TEXT NOT NULL,created INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS interests(project_id TEXT NOT NULL,contact_hash TEXT NOT NULL,submission_id TEXT NOT NULL,UNIQUE(project_id,contact_hash));''')
  for p in json.loads((ROOT/'projects.json').read_text()):
   d.execute('INSERT OR IGNORE INTO projects VALUES(?,?,?,?,?,?,?,?)',(p['id'],p['title'],p['description'],p['category'],p['status'],p['url'],p['author'],int(time.time())))

def valid_url(v):
 p=urlparse(v); return p.scheme in ('https','http') and bool(p.hostname) and not p.username and not p.password

def valid_linkedin(v):
 p=urlparse(v)
 return p.scheme=='https' and p.hostname in ('linkedin.com','www.linkedin.com') and bool(re.fullmatch(r'/(in|pub)/[A-Za-z0-9_%.-]+/?',p.path)) and not p.username and not p.password

class Handler(BaseHTTPRequestHandler):
 def setup(self):
  super().setup(); self.connection.settimeout(15)
 def log_message(self,*args): pass
 def send(self,status,data,kind='application/json; charset=utf-8'):
  if isinstance(data,(dict,list)): data=json.dumps(data,ensure_ascii=False).encode()
  elif isinstance(data,str): data=data.encode()
  self.send_response(status); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(data)))
  self.send_header('Cache-Control','no-store' if 'json' in kind else 'no-cache')
  self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' https://www.googletagmanager.com; style-src 'self'; img-src 'self' data: https://www.google-analytics.com https://region1.google-analytics.com https://analytics.google.com https://www.google.com; connect-src 'self' https://www.google-analytics.com https://region1.google-analytics.com https://analytics.google.com https://www.google.com; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
  self.end_headers(); self.wfile.write(data)
 def do_GET(self):
  path=urlparse(self.path).path
  if path in (BASE+'/api/projects','/en/api/projects'):
   with connect() as d: rows=[dict(r) for r in d.execute("SELECT * FROM projects WHERE status IN ('live','archived','development') ORDER BY created,id")]
   if path.startswith('/en/'):
    for row in rows:
     category,description=EN_PROJECTS.get(row['id'],(row['category'],row['description']))
     row['category'],row['description']=category,description
     if row['id']=='price-monitor':row['title'],row['author']='Price Monitor','Andrey'
   return self.send(200,rows)
  if path==BASE+'/api/health': return self.send(200,{'ok':True})
  routes={'/':'index.html','/en':'index-en.html','/en/':'index-en.html',BASE:'index.html',BASE+'/':'index.html',BASE+'/style.css':'style.css',BASE+'/app.js':'app.js',BASE+'/analytics.js':'analytics.js',BASE+'/favicon.svg':'favicon.svg'}
  f=routes.get(path)
  if not f:return self.send(404,{'error':'Страница не найдена'})
  types={'html':'text/html; charset=utf-8','css':'text/css; charset=utf-8','js':'text/javascript; charset=utf-8','svg':'image/svg+xml'}
  return self.send(200,(ROOT/'public'/f).read_bytes(),types[f.rsplit('.',1)[1]])
 def do_POST(self):
  if urlparse(self.path).path!=BASE+'/api/submissions':return self.send(404,{'error':'Не найдено'})
  origin=self.headers.get('Origin',''); allowed={'https://gpu.social','http://127.0.0.1:9327','http://localhost:9327'}
  if origin not in allowed:return self.send(403,{'error':'Отправьте заявку через форму на сайте.'})
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=16000:return self.send(413,{'error':'Заявка слишком большая.'})
   if not self.headers.get('Content-Type','').startswith('application/json'):return self.send(415,{'error':'Неверный формат.'})
   obj=json.loads(self.rfile.read(length))
   if not isinstance(obj,dict):raise ValueError()
   if obj.get('website'):return self.send(400,{'error':'Не удалось отправить форму.'})
   vals={k:str(obj.get(k,'')).strip() for k in ['kind','project_id','title','description','contact','url','author']}
   if vals['kind'] not in ('idea','project','revive','contact'):raise ValueError()
   if not 10<=len(vals['description'])<=3000 or not 3<=len(vals['contact'])<=180:raise ValueError()
   if not (re.fullmatch(r'@[A-Za-z0-9_]{5,32}',vals['contact']) or re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',vals['contact']) or valid_linkedin(vals['contact'])):
    return self.send(400,{'error':'Укажите email, Telegram @username или ссылку на профиль LinkedIn.'})
   if len(vals['title'])>120 or len(vals['author'])>100 or len(vals['url'])>1000:raise ValueError()
   if vals['url'] and not valid_url(vals['url']):return self.send(400,{'error':'Ссылка должна начинаться с https:// или http://.'})
   if vals['kind'] not in ('revive','contact') and len(vals['title'])<3:raise ValueError()
   if vals['kind']=='project' and len(vals['author'])<2:raise ValueError()
   if obj.get('consent') is not True:return self.send(400,{'error':'Нужно согласие на обработку заявки.'})
  except (ValueError,TypeError,json.JSONDecodeError):return self.send(400,{'error':'Проверьте обязательные поля и длину описания.'})
  now=int(time.time()); sid=str(uuid.uuid4())
  # Caddy overwrites X-Forwarded-For; service binds only to loopback.
  peer=self.headers.get('X-Forwarded-For',self.client_address[0]).split(',')[-1].strip()
  ip=hashlib.sha256((str(now//86400)+peer).encode()).hexdigest()
  with connect() as d:
   d.execute('BEGIN IMMEDIATE'); d.execute('DELETE FROM limits WHERE created<?',(now-3600,))
   if d.execute('SELECT count(*) FROM limits WHERE ip=?',(ip,)).fetchone()[0]>=8:return self.send(429,{'error':'Слишком много заявок. Попробуйте через час.'})
   if vals['kind'] in ('revive','contact'):
    project=d.execute("SELECT title FROM projects WHERE id=? AND status IN ('live','archived','development')",(vals['project_id'],)).fetchone()
    if not project:return self.send(400,{'error':'Проект не найден.'})
    vals['title']=project['title']; h=hashlib.sha256(vals['contact'].lower().encode()).hexdigest()
    if d.execute('SELECT 1 FROM interests WHERE project_id=? AND contact_hash=?',(vals['project_id'],h)).fetchone():return self.send(200,{'ok':True,'duplicate':True})
    d.execute('INSERT INTO interests VALUES(?,?,?)',(vals['project_id'],h,sid))
   d.execute('INSERT INTO submissions(id,kind,project_id,title,description,contact,url,author,created) VALUES(?,?,?,?,?,?,?,?,?)',(sid,)+tuple(vals[k] for k in ['kind','project_id','title','description','contact','url','author'])+(now,))
   d.execute('INSERT INTO limits VALUES(?,?)',(ip,now))
  return self.send(201,{'ok':True,'id':sid})

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=9327);args=parser.parse_args();init();ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
