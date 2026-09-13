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
  for kind in ['project','idea','revive']:
   status,obj=self.req({'kind':kind,'project_id':'logo-maker','title':'Test project','description':'This is a test submission with a useful description.','contact':kind+'@example.com','author':'Test','url':'https://example.com','consent':True})
   self.assertEqual(status,201)
  with server.connect() as d:self.assertEqual(d.execute('SELECT count(*) FROM submissions').fetchone()[0],before+3)
  status,rows=self.req(path='/workshop/api/projects');self.assertEqual(status,200);self.assertEqual(len(rows),3);self.assertNotIn('example.com',json.dumps(rows));self.assertNotIn('contact',json.dumps(rows))
  self.assertEqual(self.req(path='/workshop/data/workshop.sqlite3')[0],404)
 def test_bad_inputs_and_origin(self):
  data={'kind':'idea','title':'Test','description':'Test description','contact':'x@example.com','consent':True}
  self.assertEqual(self.req(data,origin='https://evil.example')[0],403)
  self.assertEqual(self.req({**data,'consent':False})[0],400)
  self.assertEqual(self.req({**data,'contact':'invalid'})[0],400)
  self.assertEqual(self.req({**data,'url':'javascript:alert(1)'})[0],400)
  self.assertEqual(self.req({**data,'kind':'revive','project_id':'missing'})[0],400)
 def test_deduplication(self):
  data={'kind':'revive','project_id':'logo-maker','description':'Would use it for my project','contact':'duplicate@example.com','consent':True}
  self.assertEqual(self.req(data)[0],201);status,obj=self.req(data);self.assertEqual(status,200);self.assertTrue(obj['duplicate'])
if __name__=='__main__':unittest.main()
