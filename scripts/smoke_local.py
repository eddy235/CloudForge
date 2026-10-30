"""Use only against CloudForge's loopback Docker Compose demo.

Run after `docker compose up --build -d`.
"""
import json
import urllib.error
import urllib.request

BASE='http://127.0.0.1:8000'

def call(path,method='GET'):
    req=urllib.request.Request(BASE+path,method=method)
    try:
        with urllib.request.urlopen(req,timeout=8) as res:
            return res.status,res.headers, res.read()
    except urllib.error.HTTPError as e:
        return e.code,e.headers,e.read()


def main():
    status,headers,body=call('/health/')
    assert status==200,(status,body)
    health=json.loads(body)
    assert health.get('demo_mode') is True,health
    status,headers,body=call('/demo/')
    assert status==200 and b'SYNTHETIC DATA ONLY' in body
    assert "script-src 'none'" in headers.get('Content-Security-Policy','')
    for path in ['/admin/','/login/','/tickets/','/assets/','/reports/']:
        status,_,_=call(path)
        assert status==404,(path,status)
    for path in ['/tickets/new/','/demo/']:
        status,_,_=call(path,method='POST')
        assert status==404,(path,status)
    print('PASS: Local Docker demo is synthetic, read-only and access-isolated.')

if __name__=='__main__':main()
