#!/usr/bin/env python3
"""Private moderation CLI. Run through SSH, never expose via HTTP."""
import argparse,json,time,uuid,sys
import server,notifications,public_pages
from server import connect,init,valid_url
p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='action',required=True)
sub.add_parser('inbox')
sub.add_parser('notify')
sub.add_parser('newsletter-status')
a=sub.add_parser('posts');a.add_argument('update_id');a.add_argument('--lang',choices=['ru','en'],default='ru')
a=sub.add_parser('social');a.add_argument('update_id');a.add_argument('--platform',choices=['LinkedIn','Telegram'],required=True);a.add_argument('--url',required=True)
a=sub.add_parser('approve-update');a.add_argument('id');a.add_argument('--content',required=True,help='Reviewed JSON with title, title_en, summary, summary_en; optional external_url')
a=sub.add_parser('show');a.add_argument('id')
a=sub.add_parser('close');a.add_argument('id')
a=sub.add_parser('publish');a.add_argument('id');a.add_argument('--status',choices=['live','archived','development'],required=True);a.add_argument('--category',required=True)
a=sub.add_parser('status');a.add_argument('id');a.add_argument('status',choices=['live','archived','development','hidden'])
a=sub.add_parser('edit');a.add_argument('id');a.add_argument('--title');a.add_argument('--description');a.add_argument('--url');a.add_argument('--author')
args=p.parse_args();init()
if args.action=='approve-update':
 from pathlib import Path
 try:print(server.publish_update(args.id,json.loads(Path(args.content).read_text())))
 except (ValueError,OSError) as error:raise SystemExit(str(error))
 raise SystemExit()
if args.action=='notify':
 result=notifications.run(server);print(json.dumps(result));raise SystemExit(1 if result.get('failed') else 0)
if args.action in ('posts','social'):
 item=next((i for i in public_pages.news(server) if i['id']==args.update_id),None)
 if not item:raise SystemExit('Update not found')
 if args.action=='posts':print(public_pages.post_text(server,item,args.lang=='en'));raise SystemExit()
 from urllib.parse import urlparse
 url=urlparse(args.url)
 if url.scheme!='https' or url.hostname not in ({'www.linkedin.com','linkedin.com','lnkd.in'} if args.platform=='LinkedIn' else {'t.me'}):raise SystemExit('Use a public LinkedIn or Telegram post URL')
 with connect() as d:d.execute('INSERT OR IGNORE INTO update_posts VALUES(?,?,?,?)',(args.update_id,args.platform,args.url,int(time.time())))
 print('Post linked');raise SystemExit()
if args.action=='newsletter-status':
 with connect() as d:
  print(json.dumps({'subscribers':dict(d.execute('SELECT status,count(*) FROM subscribers GROUP BY status').fetchall()),'jobs':dict(d.execute('SELECT status,count(*) FROM notification_jobs GROUP BY status').fetchall())}))
 raise SystemExit()
with connect() as d:
 if args.action=='inbox':
  for r in d.execute("SELECT id,kind,title,created FROM submissions WHERE status='pending' ORDER BY created"):print(json.dumps(dict(r),ensure_ascii=False))
 elif args.action=='show':
  r=d.execute('SELECT * FROM submissions WHERE id=?',(args.id,)).fetchone()
  if not r:raise SystemExit('Not found')
  print(json.dumps(dict(r),ensure_ascii=False,indent=2))
 elif args.action=='close':
  d.execute("UPDATE submissions SET status='closed' WHERE id=?",(args.id,))
 elif args.action=='publish':
  r=d.execute("SELECT * FROM submissions WHERE id=? AND kind='project' AND status='pending'",(args.id,)).fetchone()
  if not r:raise SystemExit('No pending project with this id')
  if args.status=='live' and not valid_url(r['url']):raise SystemExit('A live project needs a valid URL')
  pid=str(uuid.uuid4())
  d.execute('INSERT INTO projects VALUES(?,?,?,?,?,?,?,?)',(pid,r['title'],r['description'],args.category,args.status,r['url'],r['author'],int(time.time())))
  d.execute("UPDATE submissions SET status='published' WHERE id=?",(args.id,));print(pid)
 elif args.action=='status':
  r=d.execute('SELECT url FROM projects WHERE id=?',(args.id,)).fetchone()
  if not r:raise SystemExit('Not found')
  if args.status=='live' and not valid_url(r['url']):raise SystemExit('Set a valid URL first')
  d.execute('UPDATE projects SET status=? WHERE id=?',(args.status,args.id))
 elif args.action=='edit':
  for key in ['title','description','url','author']:
   val=getattr(args,key)
   if val is not None:
    if key=='url' and val and not valid_url(val):raise SystemExit('Invalid URL')
    d.execute('UPDATE projects SET '+key+'=? WHERE id=?',(val,args.id))
