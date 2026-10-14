#!/usr/bin/env python3
"""Smoke checks for auth, access isolation and admin-only backup preview."""
import json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error, http.cookiejar
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tmp=Path(tempfile.mkdtemp(prefix='duarte-repay-test-'))
env=os.environ.copy(); env.update({'DATA_DIR':str(tmp),'REEMBOLSO_DB_PATH':str(tmp/'test.sqlite3'),'REEMBOLSO_UPLOAD_DIR':str(tmp/'receipts'),'PORT':'18771','COOKIE_SECURE':'0','SESSION_SECRET':'smoke-secret-not-for-production','ADMIN_BOOTSTRAP_PASSWORD':'AdminTeste-2026!','ADMIN_BOOTSTRAP_CPF':'12345678901','ADMIN_BOOTSTRAP_NAME':'Admin de teste'})
p=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base='http://127.0.0.1:18771'
def req(path,method='GET',data=None,cookie=None,headers=None):
    h=dict(headers or {})
    if cookie:h['Cookie']=cookie
    if data is not None:h['Content-Type']='application/json'
    q=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers=h,method=method)
    try:
        with urllib.request.urlopen(q,timeout=5) as r:return r.status,r.headers, r.read()
    except urllib.error.HTTPError as e:return e.code,e.headers,e.read()
def wait():
    for _ in range(50):
        try:
            if req('/api/health')[0]==200:return
        except Exception:pass
        time.sleep(.1)
    raise AssertionError('Server did not start')
try:
    wait()
    assert req('/')[0]==200
    status,headers,body=req('/api/login','POST',{'login':'12345678901','password':'AdminTeste-2026!'})
    assert status==200,(status,body)
    cookie=headers.get('Set-Cookie').split(';',1)[0]
    assert req('/api/summary',cookie=cookie)[0]==200
    status,_,body=req('/api/register','POST',{'name':'Colaborador teste','cpf':'98765432100','phone':'11912345678','email':'teste@example.org','password':'Colaborador-Teste-1'})
    assert status==201,(status,body)
    status,headers,body=req('/api/login','POST',{'login':'98765432100','password':'Colaborador-Teste-1'})
    assert status==200
    worker=headers.get('Set-Cookie').split(';',1)[0]
    status,_,body=req('/api/reimbursements','POST',{'description':'Teste ambiente','category':'OUTROS','costCenter':'ADMINISTRATIVO','amount':12.34,'date':'2026-10-14'},worker)
    assert status==201,(status,body)
    assert req('/api/reimbursements',cookie=worker)[0]==200
    assert req('/api/import/confirm','POST',{'previewToken':'abc','confirm':True},worker)[0]==403
    assert req('/api/reimbursements?owner=98765432100',cookie=cookie)[0]==200
    assert req('/static/logo.png')[0]==200
    print('OK: servidor, login admin/colaborador, sessão, cadastro, solicitação, controle de acesso e arquivos estáticos.')
finally:
    p.terminate()
    try:p.wait(timeout=3)
    except:p.kill()
