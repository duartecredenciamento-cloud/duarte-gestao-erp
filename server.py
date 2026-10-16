#!/usr/bin/env python3
"""Duarte Repay — servidor WSGI-free com SQLite, cookies assinados e sessões no banco."""
from __future__ import annotations
import os, re, io, csv, json, time, hmac, hashlib, secrets, sqlite3, mimetypes, zipfile, html, base64, subprocess, tempfile, shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'
DATA_DIR = Path(os.environ.get('DATA_DIR', str(ROOT / 'data'))).resolve()
DB_PATH = Path(os.environ.get('REEMBOLSO_DB_PATH', str(DATA_DIR / 'duarte_repay.sqlite3'))).resolve()
UPLOAD_DIR = Path(os.environ.get('REEMBOLSO_UPLOAD_DIR', str(DATA_DIR / 'comprovantes'))).resolve()
PORT = int(os.environ.get('PORT', '8080'))
MAX_UPLOAD = 50 * 1024 * 1024
SESSION_DAYS = 7
SECRET = os.environ.get('SESSION_SECRET', '')
if not SECRET:
    SECRET = secrets.token_urlsafe(48)
    print('AVISO: SESSION_SECRET não definida; sessões serão invalidadas ao reiniciar. Configure uma chave secreta persistente.')

CATEGORIES = ['LIMPEZA','REMUNERAÇÃO SÓCIOS','ALIMENTAÇÃO','TELEFONIA E INTERNET','SOFTWARE E LICENÇAS - INFORMÁTICA','TRANSPORTES / LOGÍSTICA','COMBUSTÍVEL','MATERIAL DE ESCRITÓRIO','EQUIPAMENTOS DE INFORMÁTICA','ESTACIONAMENTO','MÓVEIS E UTENSÍLIOS','DESPESAS DE VIAGENS','MÁQUINAS E EQUIPAMENTOS','HOSPEDAGEM','OUTROS']
COST_CENTERS = ['CREDENCIAMENTO','REDE','DIRETORIA','DUARTE GESTÃO','MARKETING','FINANCEIRO','TECNOLOGIA DA INFORMAÇÃO','RECURSOS HUMANOS - RH','ADMINISTRATIVO','OUTROS']
STATUSES = {'PENDENTE','APROVADO','PAGO','NEGADO'}

DATA_DIR.mkdir(parents=True, exist_ok=True); UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@contextmanager
def db():
    c=sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA busy_timeout=20000')
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()

def init_db():
    with db() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,password_hash TEXT NOT NULL,email TEXT NOT NULL DEFAULT '',role TEXT NOT NULL DEFAULT 'usuario',full_name TEXT NOT NULL,cpf TEXT NOT NULL UNIQUE,phone TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reimbursements(id INTEGER PRIMARY KEY AUTOINCREMENT,owner TEXT NOT NULL,description TEXT NOT NULL,category TEXT NOT NULL,cost_center TEXT NOT NULL,amount_cents INTEGER NOT NULL,status TEXT NOT NULL,date TEXT NOT NULL,receipt_name TEXT NOT NULL DEFAULT '',receipt_path TEXT NOT NULL DEFAULT '',denial_reason TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,source_key TEXT UNIQUE,FOREIGN KEY(owner) REFERENCES users(username));
        CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL,message TEXT NOT NULL,is_read INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,FOREIGN KEY(username) REFERENCES users(username));
        CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,actor TEXT NOT NULL,action TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,username TEXT NOT NULL,expires_at INTEGER NOT NULL,FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS import_batches(id INTEGER PRIMARY KEY AUTOINCREMENT,fingerprint TEXT NOT NULL UNIQUE,filename TEXT NOT NULL,imported_by TEXT NOT NULL,imported_at TEXT NOT NULL,row_count INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_reimbursements_owner ON reimbursements(owner,id DESC);
        CREATE INDEX IF NOT EXISTS idx_reimbursements_status ON reimbursements(status);
        CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(username,is_read,id DESC);
        ''')
        # One-time admin bootstrap. Never seed built-in credentials or import live data implicitly.
        pw=os.environ.get('ADMIN_BOOTSTRAP_PASSWORD','')
        if pw and not c.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone():
            cpf=''.join(ch for ch in os.environ.get('ADMIN_BOOTSTRAP_CPF','00000000000') if ch.isdigit())
            name=os.environ.get('ADMIN_BOOTSTRAP_NAME','Administrador Duarte')
            email=os.environ.get('ADMIN_BOOTSTRAP_EMAIL','')
            c.execute('INSERT OR IGNORE INTO users(username,password_hash,email,role,full_name,cpf,phone,created_at) VALUES(?,?,?,?,?,?,?,?)',('admin',hash_password(pw),email,'admin',name,cpf,os.environ.get('ADMIN_BOOTSTRAP_PHONE',''),now()))

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def hash_password(password, salt=None):
    salt=salt or secrets.token_bytes(16)
    derived=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,310000)
    return 'pbkdf2_sha256$310000$'+salt.hex()+'$'+derived.hex()
def verify_password(password, stored):
    try:
        scheme,rounds,salt,digest=stored.split('$')
        if scheme!='pbkdf2_sha256': return False
        test=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),int(rounds)).hex()
        return hmac.compare_digest(test,digest)
    except Exception: return False
def clean_cpf(v): return ''.join(ch for ch in str(v or '') if ch.isdigit())
def money(cents): return round(int(cents)/100,2)
def log(c,actor,action): c.execute('INSERT INTO audit_log(actor,action,created_at) VALUES(?,?,?)',(actor,action,now()))
def public_user(u): return {'username':u['username'],'name':u['full_name'],'role':u['role'],'email':u['email']}
def safe_name(name): return Path(str(name).replace(chr(92), '/')).name[:180]

def parse_money_token(raw):
    """Converte um valor monetário reconhecível para centavos, sem arredondar OCR incerto."""
    s=str(raw or '').strip().replace(' ','').replace('O','0').replace('o','0')
    s=re.sub(r'(?<=\d)[Il](?=[\d.,]|$)','1',s)
    m=re.fullmatch(r'(\d+)(?:[.,](\d{1,2}))?',s)
    if not m:return None
    whole=int(m.group(1)); frac=(m.group(2) or '0').ljust(2,'0')
    cents=whole*100+int(frac)
    return cents if cents>0 else None

def monetary_candidates(text):
    """Retorna valores encontrados junto a rótulos de valor/total ou moeda."""
    text=str(text or '').replace('\n',' ')
    marker=re.compile(r'(?i)(?:VALOR(?:\s+TOTAL)?|VLR\.?\s*TOTAL|TOTAL\s*(?:R\$)?|R\$)')
    # Exige casas decimais para evitar ler datas e códigos como valores monetários.
    number=re.compile(r'(?<![A-Za-z0-9])([0-9OoIl]{1,7}\s*[.,]\s*[0-9OoIl]{1,2})(?![A-Za-z0-9])')
    found=set()
    for mark in marker.finditer(text):
        window=text[mark.end():mark.end()+42]
        candidates=[]
        for m in number.finditer(window):
            cents=parse_money_token(m.group(1).strip())
            if cents is not None and cents<=100_000_000:candidates.append((m.start(),cents))
        if candidates:found.add(min(candidates,key=lambda x:x[0])[1])
    return found

def read_receipt_amount(filename, content):
    """OCR local opcional no servidor; retorna centavos somente se o texto for legível."""
    suffix=Path(filename).suffix.lower()
    with tempfile.TemporaryDirectory(prefix='duarte-ocr-') as td:
        source=Path(td)/('receipt'+suffix); source.write_bytes(content)
        pages=[]
        if suffix=='.pdf':
            if not shutil.which('pdftoppm') or not shutil.which('pdftotext'):
                return None,'ocr_unavailable'
            try:
                text=subprocess.run(['pdftotext','-f','1','-l','2','-layout',str(source),'-'],capture_output=True,text=True,timeout=12,check=False).stdout
            except (subprocess.TimeoutExpired,OSError):text=''
            values=monetary_candidates(text)
            if len(values)==1:return next(iter(values)),'read'
            if len(values)>1:return None,'multiple_values'
            try:
                subprocess.run(['pdftoppm','-f','1','-l','2','-r','140','-jpeg','-scale-to','1600',str(source),str(Path(td)/'page')],capture_output=True,timeout=15,check=False)
                pages=list(Path(td).glob('page-*.jpg'))
            except (subprocess.TimeoutExpired,OSError):pages=[]
        elif suffix in ('.jpg','.jpeg','.png'):
            if not shutil.which('tesseract'):return None,'ocr_unavailable'
            pages=[source]
        else:return None,'unsupported'
        values=set()
        for page in pages[:2]:
            try:
                text=subprocess.run(['tesseract',str(page),'stdout','-l','por+eng','--psm','11'],capture_output=True,text=True,timeout=12,check=False).stdout
                values.update(monetary_candidates(text))
                # Alternativa de segmentação: diferenças só são aceitas se ambas chegarem ao mesmo valor.
                alternate=subprocess.run(['tesseract',str(page),'stdout','-l','por+eng','--psm','6'],capture_output=True,text=True,timeout=12,check=False).stdout
                alternate_values=monetary_candidates(alternate)
                primary_values=monetary_candidates(text)
                # Divergência entre segmentações vira ambiguidade; só usar valor lido por ambas.
                if primary_values and alternate_values:
                    values.update(primary_values & alternate_values)
                    if not primary_values.intersection(alternate_values):
                        values.update(primary_values)
                        values.update(alternate_values)
                else:
                    values.update(primary_values or alternate_values)
            except (subprocess.TimeoutExpired,OSError):continue
        if len(values)==1:return next(iter(values)),'read'
        if len(values)>1:return None,'multiple_values'
        return None,'unreadable'

class App(BaseHTTPRequestHandler):
    server_version='DuarteRepay/1.0'
    def log_message(self,fmt,*args): print('%s - %s'%(self.address_string(),fmt%args))
    def send_json(self,status,obj,headers=None):
        b=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','same-origin'); self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(b)
    def fail(self,status,msg): self.send_json(status,{'error':msg})
    def read_body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>MAX_UPLOAD: raise ValueError('Arquivo excede o limite de 50 MB.')
        return self.rfile.read(n)
    def body_json(self): return json.loads(self.read_body() or b'{}')
    def session(self):
        cookie=self.headers.get('Cookie','')
        m=re.search(r'(?:^|;\s*)dr_session=([^;]+)',cookie)
        if not m:return None
        token=m.group(1).split('.',1)[0]
        with db() as c:
            row=c.execute('SELECT u.* FROM sessions s JOIN users u ON u.username=s.username WHERE s.token_hash=? AND s.expires_at>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
            return row
    def require(self,admin=False):
        u=self.session()
        if not u: self.fail(401,'Sua sessão expirou. Entre novamente.'); return None
        if admin and u['role']!='admin': self.fail(403,'Acesso restrito ao perfil administrador.'); return None
        return u
    def set_cookie(self,token,exp):
        signed=token+'.'+hmac.new(SECRET.encode(),token.encode(),hashlib.sha256).hexdigest()
        secure='; Secure' if os.environ.get('COOKIE_SECURE','1')!='0' else ''
        return {'Set-Cookie':f'dr_session={signed}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_DAYS*86400}{secure}'}
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/health': return self.send_json(200,{'ok':True,'service':'duarte-repay'})
        if p.startswith('/api/'):
            u=self.require()
            if not u:return
            if p=='/api/me': return self.send_json(200,{'user':public_user(u)})
            if p=='/api/summary': return self.summary(u)
            if p=='/api/reimbursements': return self.list_reimbursements(u,parse_qs(urlparse(self.path).query))
            if p=='/api/notifications': return self.notifications(u)
            if p.startswith('/api/reimbursements/') and p.endswith('/receipt'):
                try: rid=int(p.split('/')[-2])
                except: return self.fail(404,'Solicitação não encontrada.')
                return self.receipt(u,rid)
            return self.fail(404,'Endereço de API não encontrado.')
        if p=='/' or p=='/index.html': return self.static('index.html')
        if p.startswith('/static/'): return self.static(p.removeprefix('/static/'))
        return self.fail(404,'Página não encontrada.')
    def static(self,name):
        name=safe_name(name)
        target=(STATIC/name).resolve()
        if not target.is_relative_to(STATIC.resolve()) or not target.is_file(): return self.fail(404,'Arquivo não encontrado.')
        b=target.read_bytes(); self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(str(target))[0] or 'application/octet-stream'); self.send_header('Content-Length',str(len(b))); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Cache-Control','no-cache'); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        p=urlparse(self.path).path
        # Multipart upload needs its own parser; do not attempt JSON decoding first.
        if p=='/api/import/preview':
            u=self.require(admin=True)
            if not u:return
            return self.import_preview(u)
        try: data=self.body_json()
        except (ValueError,json.JSONDecodeError) as e:return self.fail(400,str(e) or 'Requisição inválida.')
        if p=='/api/login': return self.login(data)
        if p=='/api/register': return self.register(data)
        if p=='/api/recover': return self.recover(data)
        if p.startswith('/api/'):
            u=self.require()
            if not u:return
            if p=='/api/logout':
                cookie=self.headers.get('Cookie',''); m=re.search(r'(?:^|;\s*)dr_session=([^;]+)',cookie)
                if m:
                    token=m.group(1).split('.',1)[0]
                    with db() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
                return self.send_json(200,{'ok':True},{'Set-Cookie':'dr_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0'})
            if p=='/api/reimbursements': return self.create_reimbursement(u,data)
            if p=='/api/notifications/read': return self.mark_notifications(u)
            if p=='/api/import/preview': return self.import_preview(u)
            if p=='/api/import/confirm': return self.import_confirm(u,data)
            if p.startswith('/api/reimbursements/') and p.endswith('/status'): return self.change_status(u,p,data)
            if p.startswith('/api/reimbursements/') and p.endswith('/edit'): return self.edit_reimbursement(u,p,data)
            if p.startswith('/api/reimbursements/') and p.endswith('/delete'): return self.delete_reimbursement(u,p,data)
        return self.fail(404,'Endereço não encontrado.')
    def login(self,d):
        login=str(d.get('login','')).strip(); password=str(d.get('password',''))
        with db() as c:
            u=c.execute('SELECT * FROM users WHERE username=? OR cpf=?',(login,clean_cpf(login))).fetchone()
            if not u or not verify_password(password,u['password_hash']): return self.fail(401,'CPF/login ou senha inválidos.')
            token=secrets.token_urlsafe(32); exp=int(time.time())+SESSION_DAYS*86400
            c.execute('INSERT INTO sessions(token_hash,username,expires_at) VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),u['username'],exp)); log(c,u['username'],'LOGIN')
        return self.send_json(200,{'user':public_user(u)},{'Set-Cookie':self.set_cookie(token,exp)['Set-Cookie']})
    def register(self,d):
        cpf=clean_cpf(d.get('cpf')); name=str(d.get('name','')).strip(); phone=clean_cpf(d.get('phone')); email=str(d.get('email','')).strip().lower(); pw=str(d.get('password',''))
        if len(cpf)<11 or not name or '@' not in email or len(pw)<10:return self.fail(400,'Informe nome, CPF válido, e-mail e senha com pelo menos 10 caracteres.')
        username=cpf
        try:
            with db() as c:c.execute('INSERT INTO users(username,password_hash,email,role,full_name,cpf,phone,created_at) VALUES(?,?,?,?,?,?,?,?)',(username,hash_password(pw),email,'usuario',name,cpf,phone,now())); log(c,username,'CADASTRO')
        except sqlite3.IntegrityError:return self.fail(409,'Já existe cadastro com esse CPF/login.')
        return self.send_json(201,{'ok':True,'message':'Cadastro realizado. Entre com seu CPF e senha.'})
    def recover(self,d):
        cpf=clean_cpf(d.get('cpf')); email=str(d.get('email','')).strip().lower(); phone=clean_cpf(d.get('phone')); pw=str(d.get('password',''))
        if not cpf or not email or not phone or len(pw)<10:return self.fail(400,'Preencha CPF, e-mail, telefone e senha nova (mínimo 10 caracteres).')
        with db() as c:
            u=c.execute('SELECT username FROM users WHERE cpf=? AND lower(email)=? AND phone=?',(cpf,email,phone)).fetchone()
            if not u:return self.fail(403,'Os dados não conferem. Use o suporte para recuperar o acesso.')
            c.execute('UPDATE users SET password_hash=? WHERE username=?',(hash_password(pw),u['username'])); c.execute('DELETE FROM sessions WHERE username=?',(u['username'],)); log(c,u['username'],'REDEFINIU SENHA')
        return self.send_json(200,{'ok':True,'message':'Senha atualizada. Entre novamente.'})
    def summary(self,u):
        with db() as c:
            where='' if u['role']=='admin' else ' WHERE owner=?'; params=() if u['role']=='admin' else (u['username'],)
            rows=c.execute('SELECT status,COUNT(*) n,COALESCE(SUM(amount_cents),0) cents FROM reimbursements'+where+' GROUP BY status',params).fetchall()
            unread=c.execute('SELECT COUNT(*) FROM notifications WHERE username=? AND is_read=0',(u['username'],)).fetchone()[0]
            own_count=c.execute('SELECT COUNT(*) FROM reimbursements WHERE owner=?',(u['username'],)).fetchone()[0]
            totals={x:{'count':0,'cents':0} for x in STATUSES}
            for r in rows: totals[r['status']]={'count':r['n'],'cents':r['cents']}
            return self.send_json(200,{'totals':totals,'ownCount':own_count,'unread':unread,'role':u['role']})
    def list_reimbursements(self,u,q):
        status=q.get('status',[''])[0].upper(); search=q.get('q',[''])[0][:120]; owner=q.get('owner',[''])[0][:80]
        sql='SELECT r.*,u.full_name owner_name'+(',u.phone owner_phone' if u['role']=='admin' else '')+' FROM reimbursements r LEFT JOIN users u ON u.username=r.owner WHERE 1=1'; args=[]
        if u['role']!='admin':sql+=' AND r.owner=?';args.append(u['username'])
        elif owner:sql+=' AND (r.owner=? OR u.full_name LIKE ?)';args.extend([owner,'%'+owner+'%'])
        if status in STATUSES:sql+=' AND r.status=?';args.append(status)
        if search:sql+=' AND (r.description LIKE ? OR r.category LIKE ? OR r.cost_center LIKE ? OR CAST(r.id AS TEXT)=?)';args.extend(['%'+search+'%']*3+[search.lstrip('#')])
        sql+=' ORDER BY r.id DESC LIMIT 500'
        with db() as c: rows=c.execute(sql,args).fetchall()
        return self.send_json(200,{'items':[self.present(r) for r in rows]})
    def present(self,r):
        item={'id':r['id'],'owner':r['owner'],'ownerName':r['owner_name'] or r['owner'],'description':r['description'],'category':r['category'],'costCenter':r['cost_center'],'amount':money(r['amount_cents']),'status':r['status'],'date':r['date'],'hasReceipt':bool(r['receipt_path'] and Path(r['receipt_path']).is_file()),'denialReason':r['denial_reason']}
        if 'owner_phone' in r.keys(): item['ownerPhone']=r['owner_phone'] or ''
        return item
    def notifications(self,u):
        with db() as c:rows=c.execute('SELECT id,message,is_read,created_at FROM notifications WHERE username=? ORDER BY id DESC LIMIT 15',(u['username'],)).fetchall()
        return self.send_json(200,{'items':[dict(r) for r in rows]})
    def mark_notifications(self,u):
        with db() as c:c.execute('UPDATE notifications SET is_read=1 WHERE username=?',(u['username'],))
        return self.send_json(200,{'ok':True})
    def receipt(self,u,rid):
        with db() as c:r=c.execute('SELECT owner,receipt_path,receipt_name FROM reimbursements WHERE id=?',(rid,)).fetchone()
        if not r:return self.fail(404,'Solicitação não encontrada.')
        if u['role']!='admin' and r['owner']!=u['username']:return self.fail(403,'Acesso negado.')
        f=Path(r['receipt_path']).resolve()
        if not r['receipt_path'] or not f.is_relative_to(UPLOAD_DIR) or not f.is_file():return self.fail(404,'Comprovante indisponível.')
        b=f.read_bytes();typ=mimetypes.guess_type(r['receipt_name'])[0] or 'application/octet-stream';self.send_response(200);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(b)));self.send_header('Content-Disposition',f"inline; filename*=UTF-8''{quote(r['receipt_name'])}");self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
    def create_reimbursement(self,u,d):
        desc=str(d.get('description','')).strip()[:500]; cat=str(d.get('category','')).strip().upper()[:120]; cc=str(d.get('costCenter','')).strip().upper()[:120]
        try: cents=int(round(float(d.get('amount',0))*100))
        except: cents=0
        day=str(d.get('date') or datetime.now().date().isoformat())
        if not desc or not cat or not cc or cents<=0 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):return self.fail(400,'Revise descrição, categoria, centro de custo, valor e data.')
        receipt_name='';receipt_path=''
        if d.get('receiptData'):
            try:
                import base64
                receipt_name=safe_name(d.get('receiptName','comprovante'))
                if not receipt_name.lower().endswith(('.png','.jpg','.jpeg','.pdf')):return self.fail(400,'Comprovante deve ser PDF, JPG ou PNG.')
                raw=base64.b64decode(d['receiptData'],validate=True)
                if len(raw)>10*1024*1024:return self.fail(400,'Comprovante individual excede 10 MB.')
                key=secrets.token_hex(16); target=UPLOAD_DIR/(key+'_'+receipt_name); target.write_bytes(raw);receipt_path=str(target)
            except Exception:return self.fail(400,'Não foi possível processar o comprovante.')
        with db() as c:
            cur=c.execute('INSERT INTO reimbursements(owner,description,category,cost_center,amount_cents,status,date,receipt_name,receipt_path,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(u['username'],desc,cat,cc,cents,'PENDENTE',day,receipt_name,receipt_path,now(),now())); log(c,u['username'],f'CRIOU REEMBOLSO {cur.lastrowid}')
        return self.send_json(201,{'ok':True,'id':cur.lastrowid})
    def change_status(self,u,p,d):
        if u['role']!='admin':return self.fail(403,'Ação exclusiva do administrador.')
        try:rid=int(p.split('/')[-2])
        except:return self.fail(404,'Solicitação não encontrada.')
        status=str(d.get('status','')).upper();reason=str(d.get('reason','')).strip()[:500]
        if status not in STATUSES:return self.fail(400,'Status inválido.')
        with db() as c:
            r=c.execute('SELECT * FROM reimbursements WHERE id=?',(rid,)).fetchone()
            if not r:return self.fail(404,'Solicitação não encontrada.')
            allowed={'PENDENTE':{'APROVADO','NEGADO'},'APROVADO':{'PAGO','NEGADO'},'NEGADO':set(),'PAGO':set()}
            if status not in allowed.get(r['status'],set()):return self.fail(409,'Esta transição de status não é permitida.')
            if status=='NEGADO' and not reason:return self.fail(400,'Informe o motivo da recusa.')
            c.execute('UPDATE reimbursements SET status=?,denial_reason=?,updated_at=? WHERE id=?',(status,reason if status=='NEGADO' else '',now(),rid))
            c.execute('INSERT INTO notifications(username,message,created_at) VALUES(?,?,?)',(r['owner'],f'Sua solicitação #{rid} ({r["description"]}) foi alterada para {status}.'+(f' Motivo: {reason}' if status=='NEGADO' else ''),now()));log(c,u['username'],f'ALTEROU STATUS {rid} PARA {status}')
        return self.send_json(200,{'ok':True})
    def edit_reimbursement(self,u,p,d):
        try:rid=int(p.split('/')[-2])
        except:return self.fail(404,'Solicitação não encontrada.')
        desc=str(d.get('description','')).strip()[:500];cat=str(d.get('category','')).strip()[:120];cc=str(d.get('costCenter','')).strip()[:120]
        try:cents=int(round(float(d.get('amount',0))*100))
        except:cents=0
        if not desc or not cat or not cc or cents<=0:return self.fail(400,'Revise os campos informados.')
        with db() as c:
            r=c.execute('SELECT * FROM reimbursements WHERE id=?',(rid,)).fetchone()
            if not r:return self.fail(404,'Solicitação não encontrada.')
            if u['role']!='admin' and r['owner']!=u['username']:return self.fail(403,'Acesso negado.')
            if r['status'] not in ('PENDENTE','NEGADO'):return self.fail(409,'Somente solicitações pendentes ou negadas podem ser corrigidas.')
            c.execute('UPDATE reimbursements SET description=?,category=?,cost_center=?,amount_cents=?,status="PENDENTE",denial_reason="",updated_at=? WHERE id=?',(desc,cat,cc,cents,now(),rid));log(c,u['username'],f'CORRIGIU REEMBOLSO {rid}')
        return self.send_json(200,{'ok':True})
    def delete_reimbursement(self,u,p,d):
        if u['role']!='admin':return self.fail(403,'Ação exclusiva do administrador.')
        try:rid=int(p.split('/')[-2])
        except:return self.fail(404,'Solicitação não encontrada.')
        if d.get('confirm') is not True:return self.fail(400,'Confirme a exclusão.')
        with db() as c:
            r=c.execute('SELECT * FROM reimbursements WHERE id=?',(rid,)).fetchone()
            if not r:return self.fail(404,'Solicitação não encontrada.')
            c.execute('DELETE FROM reimbursements WHERE id=?',(rid,));log(c,u['username'],f'EXCLUIU REEMBOLSO {rid}')
        f=Path(r['receipt_path']) if r['receipt_path'] else None
        if f and f.resolve().is_relative_to(UPLOAD_DIR) and f.exists():f.unlink(missing_ok=True)
        return self.send_json(200,{'ok':True})
    def multipart(self):
        ctype=self.headers.get('Content-Type','')
        if 'multipart/form-data' not in ctype:raise ValueError('Envie um arquivo CSV ou ZIP.')
        body=self.read_body(); boundary=re.search(r'boundary=(?:"([^"]+)"|([^;]+))',ctype)
        if not boundary:raise ValueError('Formulário inválido.')
        bd=(boundary.group(1) or boundary.group(2)).encode(); parts=body.split(b'--'+bd)
        for part in parts:
            if b'\r\n\r\n' not in part:continue
            head,payload=part.split(b'\r\n\r\n',1);payload=payload.rsplit(b'\r\n',1)[0]
            m=re.search(rb'name="file"; filename="([^"]*)"',head)
            if m:return safe_name(m.group(1).decode('utf-8','replace')),payload
        raise ValueError('Selecione o backup CSV ou ZIP.')
    def read_backup(self,filename,blob):
        attachments={}; csv_bytes=None
        if filename.lower().endswith('.zip'):
            try:z=zipfile.ZipFile(io.BytesIO(blob))
            except:raise ValueError('Arquivo ZIP inválido.')
            files=[n for n in z.namelist() if not n.endswith('/') and not n.startswith('__MACOSX/')]
            csvs=[n for n in files if n.lower().endswith('.csv')]
            if len(csvs)!=1:raise ValueError('O ZIP deve conter exatamente um CSV do backup.')
            csv_bytes=z.read(csvs[0])
            if sum(info.file_size for info in z.infolist())>150*1024*1024:raise ValueError('Conteúdo descompactado excede 150 MB.')
            seen_names=set()
            for n in files:
                if n.lower().endswith(('.jpg','.jpeg','.png','.pdf')) and z.getinfo(n).file_size<=12*1024*1024:
                    key=safe_name(n)
                    # Não sobrescrever anexos distintos com o mesmo nome-base em diretórios diferentes.
                    if key in seen_names:raise ValueError('O ZIP contém comprovantes com nomes duplicados; renomeie-os para evitar anexos trocados.')
                    seen_names.add(key)
                    raw=z.read(n)
                    attachments[key]={'content':raw,'name':key,'amountCents':None,'readStatus':'pending'}
            if len(attachments)>250:raise ValueError('Limite de 250 comprovantes por ZIP excedido.')
            # OCR limitado a quatro processos paralelos para manter a análise responsiva.
            def extract(item):
                key,receipt=item
                amount_cents,read_status=read_receipt_amount(key,receipt['content'])
                return key,amount_cents,read_status
            with ThreadPoolExecutor(max_workers=4) as pool:
                for key,amount_cents,read_status in pool.map(extract,attachments.items()):
                    attachments[key]['amountCents']=amount_cents
                    attachments[key]['readStatus']=read_status
        elif filename.lower().endswith('.csv'):csv_bytes=blob
        else:raise ValueError('Formato aceito: CSV ou ZIP com um CSV e comprovantes opcionais.')
        try:text=csv_bytes.decode('utf-8-sig')
        except: text=csv_bytes.decode('cp1252')
        reader=csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:raise ValueError('CSV sem cabeçalho.')
        needed={'usuario','despesa','categoria','c_custo','valor','status','data'}
        fields={str(x).strip().lower() for x in reader.fieldnames}
        if not needed.issubset(fields):raise ValueError('Cabeçalhos incompatíveis. Esperados usuario, despesa, categoria, c_custo, valor, status e data.')
        rows=[]
        for i,r in enumerate(reader,2):
            row={str(k).strip().lower():str(v or '').strip() for k,v in r.items() if k is not None}
            if not any(row.values()):continue
            try: cents=int(round(float(row.get('valor','').replace(',','.'))*100))
            except:raise ValueError(f'Valor inválido na linha {i}.')
            status=row.get('status','').upper()
            if status not in STATUSES:raise ValueError(f'Status inválido na linha {i}: {status}.')
            day=row.get('data','')[:10]
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):raise ValueError(f'Data inválida na linha {i}.')
            rows.append({'sourceId':row.get('id',''),'cpf':clean_cpf(row.get('usuario')),'description':row.get('despesa','')[:500],'category':row.get('categoria','')[:120],'costCenter':row.get('c_custo','')[:120],'cents':cents,'status':status,'date':day,'receiptOriginal':row.get('caminho_arquivo',''),'receiptName':safe_name(row.get('caminho_arquivo','')),'line':i})
        if not rows:raise ValueError('O CSV não contém lançamentos.')
        if len(rows)>10000:raise ValueError('Limite de 10.000 lançamentos excedido.')
        return rows,attachments
    def match_receipts_by_amount(self,rows,files):
        """Vincula apenas quando há um comprovante e um registro únicos para o valor exato."""
        receipt_counts={}
        for receipt in files.values():
            value=receipt.get('amountCents')
            if value is not None:receipt_counts[value]=receipt_counts.get(value,0)+1
        row_counts={}
        for row in rows:row_counts[row['cents']]=row_counts.get(row['cents'],0)+1
        matches=[]; used=set(); name_matches=[]; named_mismatches=[]
        for row in rows:
            named=row.get('receiptName')
            if named and named in files:
                receipt=files[named]
                # Nome só é aceito quando o conteúdo também confirma exatamente o valor do registro.
                if receipt.get('amountCents')==row['cents'] and row_counts.get(row['cents'])==1 and receipt_counts.get(row['cents'])==1:
                    name_matches.append({'line':row['line'],'receipt':named,'matchType':'nome_e_valor_exato','confidence':'exact_amount'})
                    used.add(row['line'])
                elif receipt.get('amountCents') is not None and receipt.get('amountCents')!=row['cents']:
                    named_mismatches.append({'line':row['line'],'receipt':named,'rowCents':row['cents'],'receiptCents':receipt['amountCents']})
        matches.extend(name_matches)
        for row in rows:
            if row['line'] in used:continue
            candidates=[name for name,receipt in files.items()
                        if receipt.get('amountCents')==row['cents'] and name not in {m['receipt'] for m in matches}]
            if len(candidates)==1 and receipt_counts.get(row['cents'])==1 and row_counts.get(row['cents'])==1:
                matches.append({'line':row['line'],'receipt':candidates[0],'matchType':'valor_unico','confidence':'exact_amount'})
                used.add(row['line'])
        used_names={m['receipt'] for m in matches}
        review=[]
        for row in rows:
            if row['line'] in used:continue
            same=[name for name,receipt in files.items() if receipt.get('amountCents')==row['cents'] and name not in used_names]
            if same:
                reason='valor_repetido' if row_counts.get(row['cents'],0)>1 or receipt_counts.get(row['cents'],0)>1 or len(same)>1 else 'nao_unico'
                review.append({'line':row['line'],'cents':row['cents'],'candidates':same,'reason':reason})
        unmatched_files=[]
        for name,receipt in files.items():
            if name not in used_names:
                unmatched_files.append({'name':name,'amountCents':receipt.get('amountCents'),'readStatus':receipt.get('readStatus')})
        return matches,review,unmatched_files,named_mismatches
    def import_preview(self,u):
        if u['role']!='admin':return self.fail(403,'Apenas administrador pode importar backup.')
        try:filename,blob=self.multipart(); rows,files=self.read_backup(filename,blob)
        except ValueError as e:return self.fail(400,str(e))
        fp=hashlib.sha256(blob).hexdigest()
        with db() as c:
            prev=c.execute('SELECT id FROM import_batches WHERE fingerprint=?',(fp,)).fetchone()
            users={r['cpf']:r for r in c.execute('SELECT username,cpf,full_name FROM users').fetchall()}
        matched=sum(1 for r in rows if r['cpf'] in users)
        missing=sorted({r['cpf'] for r in rows if r['cpf'] not in users})
        # A prévia não grava solicitações nem comprovantes no banco ou na pasta permanente.
        receipt_matches,receipt_review,unmatched_files,named_mismatches=self.match_receipts_by_amount(rows,files)
        summary={'filename':filename,'fingerprint':fp,'count':len(rows),'matchedUsers':matched,'unmatchedUsers':missing,'attachmentsFound':len(receipt_matches),'attachmentsReferenced':len(files),'receiptMatches':receipt_matches,'receiptReview':receipt_review,'unmatchedReceipts':unmatched_files,'namedValueMismatches':named_mismatches,'duplicateBatch':bool(prev),'totalCents':sum(r['cents'] for r in rows),'statuses':{s:sum(1 for r in rows if r['status']==s) for s in STATUSES}}
        if not prev:
            token=secrets.token_urlsafe(24); (DATA_DIR/(token+'.json')).write_text(json.dumps({'user':u['username'],'fp':fp,'filename':filename,'rows':rows,'receiptMatches':receipt_matches,'files':{k:{'content':base64.b64encode(v['content']).decode(),'amountCents':v.get('amountCents'),'readStatus':v.get('readStatus')} for k,v in files.items()}},ensure_ascii=False),encoding='utf-8');summary['previewToken']=token
        return self.send_json(200,{'preview':summary})
    def import_confirm(self,u,d):
        if u['role']!='admin':return self.fail(403,'Apenas administrador pode importar backup.')
        token=str(d.get('previewToken','')); confirm=d.get('confirm') is True
        if not confirm or not re.fullmatch(r'[A-Za-z0-9_-]{20,80}',token):return self.fail(400,'Confirmação ou prévia inválida.')
        path=DATA_DIR/(token+'.json')
        if not path.is_file():return self.fail(410,'Prévia expirou; envie o backup novamente.')
        try:payload=json.loads(path.read_text(encoding='utf-8'))
        except:return self.fail(400,'Prévia inválida.')
        if payload.get('user')!=u['username']:return self.fail(403,'Prévia pertence a outra sessão administrativa.')
        with db() as c:
            if c.execute('SELECT 1 FROM import_batches WHERE fingerprint=?',(payload['fp'],)).fetchone():return self.fail(409,'Este backup já foi importado anteriormente.')
            users={r['cpf']:r['username'] for r in c.execute('SELECT cpf,username FROM users').fetchall()}
            unmatched=sorted({r['cpf'] for r in payload['rows'] if r['cpf'] not in users})
            if unmatched:return self.fail(409,'Importação bloqueada: cadastre/regularize os CPFs antes. CPFs sem usuário: '+', '.join(unmatched))
            existing_count=c.execute('SELECT COUNT(*) FROM reimbursements').fetchone()[0]
            if existing_count:
                return self.fail(409,'Importação bloqueada: o banco já contém solicitações. Faça a migração em uma base nova e vazia ou revise os registros antes de prosseguir.')
            c.execute('INSERT INTO import_batches(fingerprint,filename,imported_by,imported_at,row_count) VALUES(?,?,?,?,?)',(payload['fp'],payload['filename'],u['username'],now(),len(payload['rows'])))
            count=0
            matches_by_line={m['line']:m['receipt'] for m in payload.get('receiptMatches',[])}
            staged_files=[]
            try:
                for r in payload['rows']:
                    source=f"{payload['fp']}:{r['sourceId'] or r['line']}"
                    matched_name=matches_by_line.get(r['line'],''); stored=''; name=''
                    receipt=payload.get('files',{}).get(matched_name) if matched_name else None
                    if receipt:
                        name=matched_name
                        raw=base64.b64decode(receipt['content'],validate=True)
                        suffix=Path(name).suffix.lower(); dest=UPLOAD_DIR/(secrets.token_hex(16)+suffix)
                        dest.write_bytes(raw); staged_files.append(dest); stored=str(dest)
                    c.execute('INSERT INTO reimbursements(owner,description,category,cost_center,amount_cents,status,date,receipt_name,receipt_path,created_at,updated_at,source_key) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(users[r['cpf']],r['description'] or 'Reembolso importado',r['category'] or 'OUTROS',r['costCenter'] or 'OUTROS',r['cents'],r['status'],r['date'],name,stored,now(),now(),source)); count+=1
                log(c,u['username'],f'IMPORTOU BACKUP {payload["filename"]}: {count} LANÇAMENTOS')
            except Exception:
                for staged in staged_files:staged.unlink(missing_ok=True)
                raise
        path.unlink(missing_ok=True)
        return self.send_json(200,{'ok':True,'imported':count})

if __name__=='__main__':
    init_db()
    print(f'Duarte Repay listening on 0.0.0.0:{PORT}; database={DB_PATH}; uploads={UPLOAD_DIR}')
    ThreadingHTTPServer(('0.0.0.0',PORT),App).serve_forever()
