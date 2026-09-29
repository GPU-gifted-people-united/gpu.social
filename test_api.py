import os,sys,tempfile,unittest,threading,json,urllib.request,urllib.error,sqlite3
os.environ['GPU_DB']=tempfile.mkdtemp()+'/test.sqlite3'
import server
class API(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  server.init()
  with server.connect() as d:
   for pid in ['logo-maker','fixture-2','fixture-3']:
    d.execute('INSERT INTO projects VALUES(?,?,?,?,?,?,?,?)',(pid,'Fixture','Test project','Test','archived','','Test',0))
  cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.base='http://127.0.0.1:'+str(cls.http.server_port);threading.Thread(target=cls.http.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):cls.http.shutdown();cls.http.server_close()
 def req(self,data=None,origin='http://localhost:9327',path='/workshop/api/submissions'):
  r=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json','Origin':origin})
  try:
   with urllib.request.urlopen(r) as x:return x.status,json.loads(x.read())
  except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
 def test_forms_persist_and_stay_private(self):
  with server.connect() as d: before=d.execute('SELECT count(*) FROM submissions').fetchone()[0]
  for kind in ['project','idea','revive','contact']:
   status,obj=self.req({'kind':kind,'project_id':'logo-maker','title':'Test project','description':'This is a test submission with a useful description.','contact':kind+'@example.com','author':'Test','url':'https://example.com','consent':True})
   self.assertEqual(status,201)
  with server.connect() as d:self.assertEqual(d.execute('SELECT count(*) FROM submissions').fetchone()[0],before+4)
  status,rows=self.req(path='/workshop/api/projects');self.assertEqual(status,200);self.assertEqual(len(rows),3);self.assertNotIn('example.com',json.dumps(rows));self.assertNotIn('contact',json.dumps(rows))
  self.assertEqual(self.req(path='/workshop/data/workshop.sqlite3')[0],404)
  status,english=self.req(path='/en/api/projects');self.assertEqual(status,200);logo=next(x for x in english if x['id']=='logo-maker');self.assertEqual(logo['category'],'Graphic content');self.assertNotIn('Генератор',logo['description'])
 def test_analytics_on_both_languages(self):
  for path in ('/','/en/'):
   with urllib.request.urlopen(self.base+path) as response:
    html=response.read().decode();policy=response.headers['Content-Security-Policy']
   self.assertIn('G-5QYC5M3TD3',html)
   self.assertIn('www.googletagmanager.com',policy)
  with urllib.request.urlopen(self.base+'/workshop/analytics.js') as response:
   self.assertIn("gtag('config', 'G-5QYC5M3TD3')",response.read().decode())
 def test_bad_inputs_and_origin(self):
  data={'kind':'idea','title':'Test','description':'Test description','contact':'x@example.com','consent':True}
  self.assertEqual(self.req(data,origin='https://evil.example')[0],403)
  self.assertEqual(self.req({**data,'consent':False})[0],400)
  self.assertEqual(self.req({**data,'contact':'invalid'})[0],400)
  self.assertEqual(self.req({**data,'contact':'https://www.linkedin.com/in/test-person/'})[0],201)
  self.assertEqual(self.req({**data,'contact':'https://evil.example/in/test-person/'})[0],400)
  self.assertEqual(self.req({**data,'url':'javascript:alert(1)'})[0],400)
  self.assertEqual(self.req({**data,'kind':'revive','project_id':'missing'})[0],400)
  self.assertEqual(self.req({**data,'kind':'contact','project_id':'missing'})[0],400)
 def test_deduplication(self):
  data={'kind':'revive','project_id':'logo-maker','description':'Would use it for my project','contact':'duplicate@example.com','consent':True}
  self.assertEqual(self.req(data)[0],201);status,obj=self.req(data);self.assertEqual(status,200);self.assertTrue(obj['duplicate'])
if __name__=='__main__':unittest.main()
