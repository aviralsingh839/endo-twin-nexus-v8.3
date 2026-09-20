#!/usr/bin/env python3
"""Small local-LAN ENDO-TWIN phone/workstation bridge."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import json,secrets,socket,threading,time,uuid
class EndoTwinBridgeServer:
    def __init__(self,project_root:Path,port:int=7777):
        self.project_root=Path(project_root);self.port=int(port);self.inbox=self.project_root/"data"/"bridge"/"inbox";self.inbox.mkdir(parents=True,exist_ok=True)
        self.pair_code=f"{secrets.randbelow(1000000):06d}";self.server=None;self.thread=None;self._tokens={};self._lock=threading.Lock()
    @property
    def local_address(self): return _local_ip()
    @property
    def endpoint(self): return f"http://{self.local_address}:{self.port}"
    @property
    def received_count(self): return sum(1 for _ in self.inbox.glob("*.json"))
    def start(self):
        if self.server is not None:return
        bridge=self
        class Handler(BaseHTTPRequestHandler):
            server_version="ENDO-TWIN-Bridge/1.0"
            def log_message(self,fmt,*args):return
            def _json(self,code,payload):
                raw=json.dumps(payload,ensure_ascii=False).encode();self.send_response(code);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(raw)));self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(raw)
            def _read(self):
                n=int(self.headers.get("Content-Length","0"))
                if n<=0 or n>1000000:raise ValueError("invalid request size")
                return json.loads(self.rfile.read(n).decode())
            def _auth(self):
                token=self.headers.get("X-Endo-Token","")
                with bridge._lock:exp=bridge._tokens.get(token)
                return bool(token) and exp is not None and exp>time.time()
            def do_GET(self):
                if self.path=="/v1/health":
                    self._json(200,{"service":"ENDO-TWIN local bridge","server_name":"ENDO-TWIN Workstation","version":"8.5.0","status":"ready","paired_clients":len(bridge._tokens),"received_packages":bridge.received_count,"port":bridge.port,"local_address":bridge.local_address});return
                if self.path=="/v1/inbox":
                    if not self._auth():self._json(401,{"status":"unauthorized","message":"Pair first."});return
                    self._json(200,{"status":"ready","received_packages":bridge.received_count});return
                self._json(404,{"status":"not_found"})
            def do_POST(self):
                if self.path=="/v1/pair":
                    try:p=self._read()
                    except Exception:self._json(400,{"status":"invalid_request"});return
                    if str(p.get("code",""))!=bridge.pair_code:self._json(403,{"status":"pairing_failed","message":"Incorrect pairing code."});return
                    token=secrets.token_urlsafe(32)
                    with bridge._lock:bridge._tokens[token]=time.time()+86400
                    self._json(200,{"paired":True,"status":"paired","token":token,"server_name":"ENDO-TWIN Workstation","expires_in_seconds":86400});return
                if self.path=="/v1/upload":
                    if not self._auth():self._json(401,{"status":"unauthorized","message":"Pair first."});return
                    try:p=self._read()
                    except Exception:self._json(400,{"status":"invalid_request"});return
                    if not isinstance(p,dict):self._json(400,{"status":"invalid_request"});return
                    p.setdefault("received_at_epoch_ms",int(time.time()*1000));p.setdefault("bridge_label","LOCAL_LAN_TRANSFER")
                    out=self.inbox/f"{int(time.time()*1000)}_{uuid.uuid4().hex}.json";out.write_text(json.dumps(p,indent=2,ensure_ascii=False),encoding="utf-8")
                    self._json(200,{"status":"received","received_packages":bridge.received_count,"filename":out.name});return
                self._json(404,{"status":"not_found"})
        self.server=ThreadingHTTPServer(("0.0.0.0",self.port),Handler);self.thread=threading.Thread(target=self.server.serve_forever,name="endo-twin-bridge",daemon=True);self.thread.daemon=True;self.thread.start()
    def stop(self):
        s=self.server;self.server=None
        if s is not None:s.shutdown();s.server_close()
        self.thread=None
def _local_ip():
    for host in ("8.8.8.8","1.1.1.1"):
        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.settimeout(.25);sock.connect((host,80));ip=sock.getsockname()[0];sock.close();return ip
        except OSError:pass
    try:return socket.gethostbyname(socket.gethostname())
    except OSError:return "127.0.0.1"
