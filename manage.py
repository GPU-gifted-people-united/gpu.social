#!/usr/bin/env python3
"""Private moderation CLI. Run through SSH, never expose via HTTP."""
import argparse,json,time,uuid
from server import connect,init,valid_url
p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='action',required=True)
sub.add_parser('inbox')
a=sub.add_parser('show');a.add_argument('id')
a=sub.add_parser('close');a.add_argument('id')
a=sub.add_parser('publish');a.add_argument('id');a.add_argument('--status',choices=['live','archived'],required=True);a.add_argument('--category',required=True)
a=sub.add_parser('status');a.add_argument('id');a.add_argument('status',choices=['live','archived'])
a=sub.add_parser('edit');a.add_argument('id');a.add_argument('--title');a.add_argument('--description');a.add_argument('--url');a.add_argument('--author')
args=p.parse_args();init()
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
