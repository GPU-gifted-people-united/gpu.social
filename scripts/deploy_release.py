#!/usr/bin/env python3
"""Server-installed forced SSH command: receive one reviewed release on stdin."""
import io,json,os,re,sqlite3,subprocess,sys,tarfile,time,urllib.request
from pathlib import Path
command=os.environ.get('SSH_ORIGINAL_COMMAND','')
if not re.fullmatch(r'deploy [a-f0-9]{40}',command):
    raise SystemExit('Only deploy COMMIT_SHA is allowed')
commit=command.split()[1]
base=Path('/opt/gpu-workshop');release=base/'releases'/('gh-'+commit)
data=sys.stdin.buffer.read(12_000_001)
if len(data)>12_000_000:raise SystemExit('Release too large')
allowed={'server.py','manage.py','projects.json','README.md','CONTRIBUTING.md','updates.json'}
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
    members=archive.getmembers()
    if sum(m.size for m in members)>30_000_000:raise SystemExit('Expanded release too large')
    for m in members:
        name=Path(m.name)
        if name.is_absolute() or '..' in name.parts or not (m.isfile() or m.isdir()):raise SystemExit('Unsafe archive')
        if not (str(name) in allowed or name.parts[0]=='public'):raise SystemExit('Unexpected path')
    if release.exists():raise SystemExit('Release already exists')
    release.mkdir(parents=True)
    for m in members:
        target=release/m.name
        if m.isdir():target.mkdir(parents=True,exist_ok=True)
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.extractfile(m).read());target.chmod(0o644)
for file in ['server.py','manage.py','projects.json','public/index.html','public/index-en.html','public/app.js','public/style.css']:
    if not (release/file).is_file():raise SystemExit('Incomplete release')
json.loads((release/'projects.json').read_text())
subprocess.run(['/usr/bin/python3','-m','py_compile',str(release/'server.py')],check=True)
backup=Path('/var/backups/gpu-workshop');backup.mkdir(mode=0o700,exist_ok=True)
with sqlite3.connect('/var/lib/gpu-workshop/workshop.sqlite3') as source:
    with sqlite3.connect(backup/(str(int(time.time()))+'-'+commit[:8]+'.sqlite3')) as target:source.backup(target)
for p in backup.glob('*.sqlite3'):p.chmod(0o600)
current=base/'current';previous=current.resolve();temporary=base/'next'
temporary.unlink(missing_ok=True);temporary.symlink_to(release);temporary.replace(current)
subprocess.run(['/usr/bin/systemctl','restart','gpu-workshop'],check=True)
for _ in range(20):
    try:
        with urllib.request.urlopen('http://127.0.0.1:9327/workshop/api/health',timeout=2) as r:
            if json.load(r).get('ok'):print('Deployed '+commit);break
    except Exception:time.sleep(.5)
else:
    temporary.symlink_to(previous);temporary.replace(current)
    subprocess.run(['/usr/bin/systemctl','restart','gpu-workshop'],check=True)
    raise SystemExit('Health check failed; restored previous release')
