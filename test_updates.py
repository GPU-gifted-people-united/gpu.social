import json,os,re,tempfile,threading,time,unittest,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree
import server,notifications,public_pages

class Updates(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.previous_db=server.DB;server.DB=Path(cls.temp.name)/'updates.sqlite3'
  cls.env=patch.dict(os.environ,{'GPU_SUBSCRIBE_SECRET':'test-secret-not-a-production-key','GPU_SMTP_HOST':'127.0.0.1','GPU_MAIL_FROM':'GPU <news@example.com>'});cls.env.start()
  server.init();cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.base='http://127.0.0.1:'+str(cls.http.server_port)
  cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.thread.join();server.DB=cls.previous_db;cls.env.stop();cls.temp.cleanup()
 def setUp(self):
  with server.connect() as d:
   for table in ['notification_jobs','subscribers','subscription_limits','runtime_updates','announced_projects','update_posts','projects']:d.execute('DELETE FROM '+table)
   for pid,status,url in [('aufix','live','https://aufix.app'),('secret-hidden','hidden','https://hidden.example')]:
    d.execute('INSERT INTO projects VALUES(?,?,?,?,?,?,?,?)',(pid,'Aufix' if pid=='aufix' else 'Hidden project','Public description','B2B',status,url,'Maker',0))
 def req(self,path,data=None,origin='http://localhost:9327'):
  request=urllib.request.Request(self.base+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json','Origin':origin})
  try:
   with urllib.request.urlopen(request) as response:return response.status,response.read().decode()
  except urllib.error.HTTPError as error:return error.code,error.read().decode()
 def subscribe(self):return self.req('/workshop/api/subscribe',{'email':'reader@example.com','language':'en','consent':True})
 def add_update(self,uid):
  item={'id':uid,'date_published':datetime.now(timezone.utc).isoformat(),'title':'Новая подборка','title_en':'New collection','summary':'Публичные проекты','summary_en':'Public projects','project_urls':['https://gpu.social/workshop/projects/aufix/']}
  with server.connect() as d:d.execute('INSERT INTO runtime_updates VALUES(?,?)',(uid,json.dumps(item)))
 def test_public_discovery_and_ssr(self):
  code,home=self.req('/');self.assertEqual(code,200);self.assertIn('/workshop/projects/aufix/',home);self.assertIn('Public description',home);self.assertNotIn('Hidden project',home)
  self.assertIn('hreflang="en"',home);self.assertIn('rel="canonical" href="https://gpu.social/"',home)
  code,page=self.req('/en/projects/aufix/');self.assertIn('href="https://aufix.app"',page);self.assertIn('Visit website',page);self.assertIn('Maxim',page)
  schema=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',page,re.S)[1]);self.assertEqual(schema['@type'],'SoftwareApplication');self.assertEqual(schema['sameAs'],'https://aufix.app')
  code,sitemap=self.req('/sitemap.xml');self.assertEqual(code,200);ElementTree.fromstring(sitemap);self.assertIn('/workshop/projects/aufix/',sitemap);self.assertNotIn('secret-hidden',sitemap)
  self.assertIn('Sitemap: https://gpu.social/sitemap.xml',self.req('/robots.txt')[1]);self.assertEqual(self.req('/en/projects/secret-hidden/')[0],404)
 def test_category_pages_languages_and_hidden_projects(self):
  with server.connect() as d:
   for pid,title in [('baattle-royale','Baattle Royale'),('callimate','CalliMate')]:
    d.execute('INSERT INTO projects VALUES(?,?,?,?,?,?,?,?)',(pid,title,'Public example','Игры' if pid=='baattle-royale' else 'Обучение','live','https://example.com','Maker',0))
  api=json.loads(self.req('/en/api/projects')[1]);byid={p['id']:p for p in api}
  self.assertEqual(byid['aufix']['category'],'B2B')
  self.assertEqual(byid['aufix']['category_label'],'For business')
  self.assertEqual(byid['baattle-royale']['category_id'],'games')
  self.assertEqual(byid['callimate']['category_label'],'Learning')
  home=self.req('/')[1]
  self.assertIn('data-category="games"',home);self.assertNotIn('b2b-cards',home)
  code,html=self.req('/en/categories/games/');self.assertEqual(code,200)
  self.assertIn('Browser and party games',html)
  self.assertIn('canonical" href="https://gpu.social/en/categories/games/"',html)
  self.assertIn('hreflang="ru" href="https://gpu.social/workshop/categories/games/"',html)
  schema=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',html,re.S)[1])
  self.assertEqual(schema['mainEntity']['numberOfItems'],1)
  self.assertEqual(schema['mainEntity']['itemListElement'][0]['name'],'Baattle Royale')
  self.assertNotIn('/en/projects/aufix/',html);self.assertNotIn('Hidden project',html)
  self.assertEqual(self.req('/workshop/categories/nonexistent/')[0],404)
  self.assertEqual(self.req('/en/categories/content/')[0],404)
  sitemap=self.req('/sitemap.xml')[1]
  self.assertIn('/en/categories/games/',sitemap);self.assertIn('/workshop/categories/games/',sitemap)
  self.assertNotIn('/categories/content/',sitemap)
  business=self.req('/en/projects/aufix/')[1]
  self.assertIn('data-project-category="B2B"',business)
  self.assertIn('Contact the developers',business)
  self.assertIn('href="/en/categories/business/"',business)

 def test_linked_post_news_and_feed(self):
  uid='gpu-new-projects-2026-10-19';code,page=self.req('/en/news/'+uid+'/');self.assertEqual(code,200);self.assertIn('Support on LinkedIn',page);self.assertIn('news-post-text',page)
  with server.connect() as d:d.execute('INSERT INTO update_posts VALUES(?,?,?,?)',(uid,'Telegram','https://t.me/GiftedPeopleUnited/42',int(time.time())))
  feed=json.loads(self.req('/workshop/feed.json')[1]);item=next(i for i in feed['items'] if i['id']==uid)
  self.assertIn('/workshop/news/',item['url']);self.assertIn('https://t.me/GiftedPeopleUnited/42',item['content_text']);self.assertIn('date_modified',item)
  self.assertNotIn('reader@example.com',json.dumps(feed));self.assertNotIn('subscriber',json.dumps(feed));ElementTree.fromstring(self.req('/workshop/feed.xml')[1])
 def test_email_lifecycle_and_no_duplicate_deliveries(self):
  with patch.object(notifications,'send_email') as mail:
   self.assertEqual(self.subscribe()[0],200);self.assertEqual(self.subscribe()[0],200)
   notifications.run(server);self.assertEqual(mail.call_count,1)
   link=re.search(r'https://gpu.social/workshop/subscription/confirm\?token=([^\s]+)',mail.call_args.args[2])[1]
   code,page=self.req('/workshop/subscription/confirm?token='+link);self.assertEqual(code,200);self.assertNotIn('googletagmanager',page);self.assertNotIn('analytics.js',page);self.assertIn('noindex,nofollow',page)
   with server.connect() as d:self.assertEqual(d.execute('SELECT status FROM subscribers').fetchone()[0],'pending')
   self.assertEqual(self.req('/workshop/subscription/confirm',{'token':link})[0],200)
   self.add_update('test-delivery');notifications.run(server);self.assertEqual(mail.call_count,2)
   notifications.run(server);self.assertEqual(mail.call_count,2)
   unsub=mail.call_args.args[4];token=unsub.split('token=')[1]
   self.req('/workshop/subscription/unsubscribe?token='+token)
   with server.connect() as d:self.assertEqual(d.execute('SELECT status FROM subscribers').fetchone()[0],'active')
   self.assertEqual(self.req('/workshop/subscription/unsubscribe',{'token':token})[0],200)
   self.add_update('test-after-unsubscribe');notifications.run(server);self.assertEqual(mail.call_count,2)
   self.assertEqual(self.req('/workshop/subscription/confirm',{'token':link})[0],400)
 def test_subscription_validation_and_errors_are_private(self):
  data={'email':'reader@example.com','language':'en','consent':True}
  self.assertEqual(self.req('/workshop/api/subscribe',data,origin='https://evil.example')[0],403)
  for changes in [{'consent':False},{'email':'bad\nBcc: person@example.com'},{'language':'bogus'},{'website':'bot'}]:self.assertEqual(self.req('/workshop/api/subscribe',{**data,**changes})[0],400)
  with patch.dict(os.environ,{'GPU_SMTP_HOST':''}):self.assertEqual(self.subscribe()[0],503)
  self.subscribe()
  with patch.object(notifications,'send_email',side_effect=RuntimeError('private provider response reader@example.com')):
   self.assertEqual(notifications.run(server)['failed'],1)
  with server.connect() as d:
   row=d.execute('SELECT attempts,status,last_error FROM notification_jobs').fetchone();self.assertEqual(tuple(row),(1,'retry','RuntimeError'))
  self.assertNotIn('reader@example.com',self.req('/workshop/feed.json')[1])
 def test_new_approved_projects_batch_once(self):
  now=int(time.time())
  with server.connect() as d:
   d.execute("UPDATE notification_state SET value=? WHERE key='announcement_baseline'",(str(now-7200),))
   for pid in ['batch-a','batch-b']:
    d.execute('INSERT INTO projects VALUES(?,?,?,?,?,?,?,?)',(pid,pid,'Published details','Tools','live','https://example.com','Public maker',now-1800))
  notifications.auto_announce(server);notifications.auto_announce(server)
  with server.connect() as d:
   self.assertEqual(d.execute('SELECT count(*) FROM runtime_updates').fetchone()[0],1);self.assertEqual(d.execute('SELECT count(*) FROM announced_projects').fetchone()[0],2)
  item=next(i for i in public_pages.news(server) if i['id'].startswith('projects-'))
  self.assertEqual(len(item['project_urls']),2);self.assertIn('batch-a',public_pages.post_text(server,item,True))
 def test_unsubscribe_email_headers(self):
  with patch.object(notifications.smtplib,'SMTP') as smtp:
   smtp.return_value.__enter__.return_value.send_message.return_value={}
   notifications.send_email('reader@example.com','GPU test','Public content','test-id','https://gpu.social/workshop/subscription/unsubscribe?token=test')
   message=smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
   self.assertEqual(message['List-Unsubscribe-Post'],'List-Unsubscribe=One-Click');self.assertIn('https://gpu.social/',message['List-Unsubscribe']);self.assertIn('test-id',message['Message-ID'])

if __name__=='__main__':unittest.main()
