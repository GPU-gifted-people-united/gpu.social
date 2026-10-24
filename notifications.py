"""Opt-in email updates. Private SQLite state, local SMTP, one locked worker."""
import base64,fcntl,hashlib,hmac,json,os,re,secrets,smtplib,ssl,time,uuid
from datetime import datetime,timezone
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formatdate
from html import escape as esc
from urllib.parse import parse_qs,urlparse

SITE='https://gpu.social'

def init(app):
 with app.connect() as d:
  d.executescript('''CREATE TABLE IF NOT EXISTS subscribers(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,language TEXT NOT NULL,status TEXT NOT NULL,created INTEGER NOT NULL,confirmed INTEGER NOT NULL DEFAULT 0,version INTEGER NOT NULL DEFAULT 1,last_request INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS notification_jobs(id TEXT PRIMARY KEY,subscriber_id TEXT NOT NULL,update_id TEXT NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,next_attempt INTEGER NOT NULL DEFAULT 0,sent INTEGER,last_error TEXT,UNIQUE(subscriber_id,update_id,kind));
  CREATE TABLE IF NOT EXISTS notification_state(key TEXT PRIMARY KEY,value TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS subscription_limits(peer TEXT NOT NULL,created INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS runtime_updates(id TEXT PRIMARY KEY,data TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS announced_projects(project_id TEXT PRIMARY KEY,update_id TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS update_posts(update_id TEXT NOT NULL,platform TEXT NOT NULL,url TEXT NOT NULL,created INTEGER NOT NULL,UNIQUE(update_id,url));
  CREATE INDEX IF NOT EXISTS subscription_rate ON subscription_limits(peer,created);''')
  d.execute('INSERT OR IGNORE INTO notification_state VALUES(?,?)',('announcement_baseline',str(int(time.time()))))

def enabled():
 return bool(os.environ.get('GPU_SUBSCRIBE_SECRET') and os.environ.get('GPU_SMTP_HOST') and os.environ.get('GPU_MAIL_FROM'))

def token(sub,kind):
 payload=f'{sub["id"]}.{sub["version"]}.{int(time.time())}.{kind}'
 signature=hmac.new(os.environ['GPU_SUBSCRIBE_SECRET'].encode(),payload.encode(),hashlib.sha256).hexdigest()
 return payload+'.'+signature

def validate(app,value,kind):
 try:
  sid,version,issued,action,signature=value.split('.')
  payload='.'.join([sid,version,issued,action]);secret=os.environ['GPU_SUBSCRIBE_SECRET']
  if action!=kind or not hmac.compare_digest(signature,hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()):return None
  if kind=='confirm' and not 0<=int(time.time())-int(issued)<=172800:return None
  with app.connect() as d:row=d.execute('SELECT * FROM subscribers WHERE id=?',(sid,)).fetchone()
  if row and row['version']==int(version):return dict(row)
 except (ValueError,KeyError,TypeError):pass
 return None

def private_page(app,en,title,text,form=''):
 import public_pages
 main=f'<main id="main" class="news-page"><h1>{esc(title)}</h1><p class="lead">{esc(text)}</p>{form}</main>'
 html=public_pages.page(app,main,title+' — GPU',text,'/workshop/subscribe/','/en/subscribe/',en)
 html=re.sub(r'<script[^>]+src="[^"]*(?:googletagmanager|analytics\.js)[^"]*"[^>]*></script>','',html)
 return html.replace('</head>','<meta name="robots" content="noindex,nofollow"></head>')

def response(app,path,query):
 import public_pages
 if path in ('/workshop/subscribe/','/en/subscribe/'):
  en=path.startswith('/en/');title='Get GPU updates' if en else 'Получать новинки GPU'
  if enabled():
   form=f'''<form id="subscribe-form" class="subscription-form"><label>Email<input type="email" name="email" autocomplete="email" maxlength="254" required></label><label>{'Language' if en else 'Язык'}<select name="language"><option value="ru" {'selected' if not en else ''}>Русский</option><option value="en" {'selected' if en else ''}>English</option></select></label><div class="trap" aria-hidden="true"><input name="website" tabindex="-1" autocomplete="off"></div><label class="consent"><input type="checkbox" name="consent" required><span>{'Email me new GPU projects. I can unsubscribe at any time.' if en else 'Хочу получать новые проекты GPU по email. Смогу отписаться в любой момент.'}</span></label><button class="button" type="submit">{'Subscribe' if en else 'Подписаться'}</button><p role="status" id="subscribe-status"></p></form>'''
  else:form='<p>'+('Email updates are being connected. Follow our RSS feed for now.' if en else 'Email-рассылка подключается. Пока можно следить через RSS.')+'</p><a class="text-button" href="/workshop/feed.xml">RSS ↗</a>'
  main=f'<main id="main" class="news-page"><h1>{title}</h1><p class="lead">'+('Only new, approved projects and community updates. No empty daily emails.' if en else 'Только новые одобренные проекты и новости сообщества. Без пустых ежедневных писем.')+f'</p>{form}<p class="muted">'+('Confirm your address by email. Every update includes an unsubscribe link.' if en else 'Подтвердите адрес письмом. В каждой подборке есть ссылка отписки.')+f'</p><a class="text-button" href="https://t.me/GiftedPeopleUnited" target="_blank" rel="noopener noreferrer">'+('GPU community on Telegram' if en else 'Коммьюнити GPU в Telegram')+' ↗</a></main>'
  return 200,public_pages.page(app,main,title+' — GPU',title,'/workshop/subscribe/','/en/subscribe/',en),'text/html; charset=utf-8'
 if path in ('/workshop/subscription/confirm','/workshop/subscription/unsubscribe'):
  kind=path.rsplit('/',1)[1];value=parse_qs(query).get('token',[''])[0];sub=validate(app,value,kind);en=sub is not None and sub['language']=='en'
  if not sub:return 400,private_page(app,False,'Ссылка недействительна','Запросите новое письмо подтверждения на странице подписки.'),'text/html; charset=utf-8'
  title=('Confirm subscription' if en else 'Подтвердить подписку') if kind=='confirm' else ('Unsubscribe' if en else 'Отписаться')
  text=('Receive new GPU projects by email.' if en else 'Получать новые проекты GPU по email.') if kind=='confirm' else ('Stop GPU email updates.' if en else 'Перестать получать письма с новинками GPU.')
  form=f'<form action="{path}" method="post"><input type="hidden" name="token" value="{esc(value,quote=True)}"><button class="button" type="submit">{title}</button></form>'
  return 200,private_page(app,en,title,text,form),'text/html; charset=utf-8'
 return None

def post(handler,app,path):
 if path not in ('/workshop/api/subscribe','/workshop/subscription/confirm','/workshop/subscription/unsubscribe'):return False
 try:
  size=int(handler.headers.get('Content-Length','0'))
  if not 0<size<=4096:raise ValueError()
  raw=handler.rfile.read(size)
  obj=json.loads(raw) if handler.headers.get('Content-Type','').startswith('application/json') else {k:v[0] for k,v in parse_qs(raw.decode()).items()}
  if not isinstance(obj,dict):raise ValueError()
 except (ValueError,UnicodeError,TypeError):handler.send(400,{'error':'Invalid request'});return True
 if path!='/workshop/api/subscribe':
  kind=path.rsplit('/',1)[1];sub=validate(app,str(obj.get('token','')),kind)
  if not sub:handler.send(400,{'error':'Invalid or expired link'});return True
  en=sub['language']=='en';now=int(time.time())
  with app.connect() as d:
   d.execute('BEGIN IMMEDIATE')
   current=d.execute('SELECT version FROM subscribers WHERE id=?',(sub['id'],)).fetchone()
   if not current or current['version']!=sub['version']:handler.send(400,{'error':'Invalid or expired link'});return True
   if kind=='confirm':
    d.execute("UPDATE subscribers SET status='active',confirmed=? WHERE id=? AND status='pending'",(now,sub['id']))
   else:
    d.execute("UPDATE subscribers SET status='unsubscribed',version=version+1 WHERE id=?",(sub['id'],))
    d.execute("UPDATE notification_jobs SET status='cancelled' WHERE subscriber_id=? AND status IN ('pending','retry')",(sub['id'],))
  title=('Subscription confirmed' if en else 'Подписка подтверждена') if kind=='confirm' else ('You are unsubscribed' if en else 'Вы отписались')
  handler.send(200,private_page(app,en,title,'We’ll email you when there is news.' if kind=='confirm' and en else 'Напишем, когда появятся новости.' if kind=='confirm' else 'GPU email updates have been stopped.' if en else 'Письма с новинками GPU больше не придут.'),'text/html; charset=utf-8');return True
 if handler.headers.get('Origin','') not in {'https://gpu.social','http://127.0.0.1:9327','http://localhost:9327'}:handler.send(403,{'error':'Use the subscription form on GPU.'});return True
 if not enabled():handler.send(503,{'error':'Email updates are not configured yet.'});return True
 email=str(obj.get('email','')).strip().lower();lang=obj.get('language','en')
 if obj.get('website') or obj.get('consent') is not True or lang not in ('ru','en') or len(email)>254 or not email.isascii() or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',email):handler.send(400,{'error':'Check your email and consent.'});return True
 now=int(time.time());peer=handler.headers.get('X-Forwarded-For',handler.client_address[0]).split(',')[-1].strip();peer=hashlib.sha256((str(now//86400)+peer).encode()).hexdigest()
 with app.connect() as d:
  d.execute('BEGIN IMMEDIATE');d.execute('DELETE FROM subscription_limits WHERE created<?',(now-3600,))
  if d.execute('SELECT count(*) FROM subscription_limits WHERE peer=?',(peer,)).fetchone()[0]>=5:handler.send(429,{'error':'Please try again later.'});return True
  d.execute('INSERT INTO subscription_limits VALUES(?,?)',(peer,now))
  sub=d.execute('SELECT * FROM subscribers WHERE email=?',(email,)).fetchone()
  if not sub:
   sid=str(uuid.uuid4());d.execute("INSERT INTO subscribers VALUES(?,?,?,'pending',?,0,1,?)",(sid,email,lang,now,now));version=1
  elif sub['status']=='active' or now-sub['last_request']<300:
   handler.send(200,{'ok':True});return True
  else:
   sid=sub['id'];version=sub['version']+1;d.execute("UPDATE subscribers SET status='pending',language=?,version=?,last_request=? WHERE id=?",(lang,version,now,sid))
   d.execute("UPDATE notification_jobs SET status='cancelled' WHERE subscriber_id=? AND kind='confirm' AND status IN ('pending','retry')",(sid,))
  d.execute('INSERT INTO notification_jobs(id,subscriber_id,update_id,kind) VALUES(?,?,?,?)',(str(uuid.uuid4()),sid,str(version),'confirm'))
 handler.send(200,{'ok':True});return True

def auto_announce(app):
 """Group newly published projects after a quiet 15-minute batching window."""
 import public_pages
 now=int(time.time());editorial=public_pages.news(app)
 known={urlparse(u).path.rstrip('/').split('/')[-1] for i in editorial for u in i.get('project_urls',[])}
 with app.connect() as d:
  baseline=int(d.execute("SELECT value FROM notification_state WHERE key='announcement_baseline'").fetchone()[0])
  rows=[dict(r) for r in d.execute(f"SELECT * FROM projects WHERE status IN {public_pages.VISIBLE} AND created>? AND id NOT IN (SELECT project_id FROM announced_projects) ORDER BY created,id",(baseline,)) if r['id'] not in known]
  if not rows or now-max(p['created'] for p in rows)<900:return
  batch=rows[:12];uid='projects-'+str(batch[0]['created'])+'-'+batch[0]['id'];english=[dict(p) for p in batch]
  for p in english:app.localize_english_project(p)
  item={'id':uid,'date_published':datetime.fromtimestamp(now,timezone.utc).isoformat().replace('+00:00','Z'),'title':'Новые проекты в GPU','title_en':'New projects on GPU','summary':' · '.join(p['title'] for p in batch),'summary_en':' · '.join(p['title'] for p in english),'project_urls':[SITE+public_pages.project_url(p) for p in batch]}
  d.execute('INSERT OR IGNORE INTO runtime_updates VALUES(?,?)',(uid,json.dumps(item,ensure_ascii=False)))
  for p in batch:d.execute('INSERT OR IGNORE INTO announced_projects VALUES(?,?)',(p['id'],uid))

def enqueue(app):
 import public_pages
 with app.connect() as d:
  subs=d.execute("SELECT * FROM subscribers WHERE status='active'").fetchall()
  for item in public_pages.news(app):
   published=int(datetime.fromisoformat(item['date_published'].replace('Z','+00:00')).timestamp())
   for sub in subs:
    if published>=sub['confirmed']:
     d.execute('INSERT OR IGNORE INTO notification_jobs(id,subscriber_id,update_id,kind) VALUES(?,?,?,?)',(str(uuid.uuid4()),sub['id'],item['id'],'news'))

def send_email(to,subject,body,message_id,unsubscribe=None):
 msg=EmailMessage(policy=SMTP);msg['From']=os.environ['GPU_MAIL_FROM'];msg['To']=to;msg['Subject']=subject;msg['Message-ID']=f'<{message_id}@agent.gpu.social>';msg['Date']=formatdate(localtime=False)
 if unsubscribe:
  msg['List-Unsubscribe']='<'+unsubscribe+'>';msg['List-Unsubscribe-Post']='List-Unsubscribe=One-Click'
 msg.set_content(body)
 host=os.environ['GPU_SMTP_HOST'];port=int(os.environ.get('GPU_SMTP_PORT','25'))
 if host not in ('127.0.0.1','localhost','::1') and os.environ.get('GPU_SMTP_SSL')!='1' and os.environ.get('GPU_SMTP_STARTTLS')!='1':raise RuntimeError('External SMTP requires TLS')
 cls=smtplib.SMTP_SSL if os.environ.get('GPU_SMTP_SSL')=='1' else smtplib.SMTP
 with cls(host,port,timeout=15) as smtp:
  if os.environ.get('GPU_SMTP_STARTTLS')=='1':smtp.starttls(context=ssl.create_default_context())
  if os.environ.get('GPU_SMTP_USER'):smtp.login(os.environ['GPU_SMTP_USER'],os.environ['GPU_SMTP_PASSWORD'])
  if smtp.send_message(msg):raise RuntimeError('Recipient refused')

def deliver(app,job,sub,items):
 import public_pages
 en=sub['language']=='en'
 if job['kind']=='confirm':
  if sub['status']!='pending' or str(sub['version'])!=job['update_id']:return False
  url=SITE+'/workshop/subscription/confirm?token='+token(sub,'confirm')
  subject='Confirm your GPU subscription' if en else 'Подтвердите подписку на GPU'
  body=('Confirm your email to receive new GPU projects:\n\n' if en else 'Подтвердите email, чтобы получать новые проекты GPU:\n\n')+url+('\n\nIf you did not subscribe, ignore this email. This link expires in 48 hours.' if en else '\n\nЕсли вы не подписывались, просто проигнорируйте письмо. Ссылка действует 48 часов.')
  send_email(sub['email'],subject,body,job['id']);return True
 if sub['status']!='active':return False
 item=items.get(job['update_id'])
 if not item:return False
 title=item.get('title_en',item['title']) if en else item['title'];summary=item.get('summary_en',item['summary']) if en else item['summary']
 unsubscribe=SITE+'/workshop/subscription/unsubscribe?token='+token(sub,'unsubscribe')
 body=public_pages.post_text(app,item,en)
 for post in item.get('social_posts',[]):body+='\n\n'+('Support on ' if en else 'Поддержать в ')+post.get('platform','LinkedIn')+': '+post['url']
 body+='\n\n'+('Unsubscribe: ' if en else 'Отписаться: ')+unsubscribe
 send_email(sub['email'],'GPU · '+title,body,job['id'],unsubscribe);return True

def run(app):
 import public_pages
 if not enabled():raise RuntimeError('Email is not configured')
 lock=open(app.DB.parent/'notifications.lock','a')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:lock.close();return {'busy':True}
 try:
  auto_announce(app);enqueue(app);items={i['id']:i for i in public_pages.news(app)};result={'sent':0,'failed':0,'cancelled':0}
  with app.connect() as d:jobs=[dict(r) for r in d.execute("SELECT * FROM notification_jobs WHERE status IN ('pending','retry') AND next_attempt<=? AND attempts<5 ORDER BY rowid LIMIT 50",(int(time.time()),))]
  for job in jobs:
   with app.connect() as d:row=d.execute('SELECT * FROM subscribers WHERE id=?',(job['subscriber_id'],)).fetchone()
   if not row:continue
   try:
    sent=deliver(app,job,dict(row),items);status='sent' if sent else 'cancelled'
    with app.connect() as d:d.execute('UPDATE notification_jobs SET status=?,sent=?,last_error=NULL WHERE id=?',(status,int(time.time()),job['id']))
    result[status]+=1
   except Exception as error:
    # Never log addresses, tokens, SMTP responses, or message content.
    with app.connect() as d:d.execute("UPDATE notification_jobs SET status='retry',attempts=attempts+1,next_attempt=?,last_error=? WHERE id=?",(int(time.time())+min(86400,300*2**job['attempts']),type(error).__name__,job['id']))
    result['failed']+=1
  return result
 finally:lock.close()
