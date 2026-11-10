import os, json, subprocess, tempfile, threading, time, shutil
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=80*1024*1024
slot=threading.BoundedSemaphore(1)
@app.get('/')
def home(): return render_template('index.html')
@app.get('/samples/<name>')
def samples(name):
    if name not in ('log4j-before-2.14.1.tar','log4j-compare-2.24.3.tar'): return jsonify(error='파일이 없습니다.'),404
    return send_from_directory('samples',name,as_attachment=True)
@app.errorhandler(RequestEntityTooLarge)
def too_large(e): return jsonify(error='파일은 최대 80MB까지 업로드할 수 있습니다.'),413
@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'sha256-MVDkWJPSRmvPDaA93bAlo8RSRbieHJbxSBO83RKkDFk='; style-src 'self' 'sha256-QI7soWC/em7Ck/9wEyBUB7PnP+ZC3okPp62Fa0xTqwI='; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    return response
@app.post('/api/scan')
def scan():
    # Cross-site browser requests are rejected; no session or API secret is used.
    origin=request.headers.get('Origin')
    if origin and origin.rstrip('/') != request.host_url.rstrip('/'): return jsonify(error='동일한 사이트에서 업로드해주세요.'),403
    f=request.files.get('image')
    if not f or not f.filename or not f.filename.lower().endswith('.tar'):
        return jsonify(error='docker save로 저장한 컨테이너 이미지 .tar 파일을 선택하세요. JPG/PNG와 소스 압축 파일은 검사할 수 없습니다.'),400
    if not slot.acquire(blocking=False): return jsonify(error='다른 검사가 진행 중입니다. 잠시 후 다시 시도해주세요.'),429
    started=time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix='image-scan-') as d:
            archive=Path(d)/'image.tar'; output=Path(d)/'result.json'; f.save(archive)
            # Never extract an uploaded archive in the web application.
            command=['trivy','image','--input',str(archive),'--skip-db-update','--skip-java-db-update','--scanners','vuln','--format','json','--output',str(output),'--timeout','3m','--quiet','--exit-code','0']
            try: result=subprocess.run(command,capture_output=True,text=True,timeout=195,check=False)
            except subprocess.TimeoutExpired: return jsonify(error='검사 시간이 초과되었습니다. 배포 통과로 판단하지 마세요. DB 다운로드 상태를 확인하고 다시 시도하세요.'),504
            except FileNotFoundError: return jsonify(error='서버에 Trivy가 설치되지 않았습니다. 제공된 Docker Compose로 실행하세요.'),503
            if result.returncode != 0 or not output.exists():
                app.logger.warning('Trivy scan failed: %s',result.stderr[-2000:])
                return jsonify(error='검사에 실패했습니다. 올바른 docker save 이미지인지, 서버가 취약점 DB를 다운로드할 수 있는지 확인하세요. 이 상태는 PASS가 아닙니다.'),422
            try: report=json.loads(output.read_text())
            except (ValueError,OSError): return jsonify(error='검사 결과를 읽을 수 없습니다. 통과로 판단하지 마세요.'),502
            rows=[]; packages=0; analyzed=[]
            for target in report.get('Results') or []:
                analyzed.append({'target':target.get('Target',''),'type':target.get('Type','')})
                packages+=len(target.get('Packages') or [])
                for v in target.get('Vulnerabilities') or []:
                    rows.append({k:v.get(k,'') for k in ('VulnerabilityID','PkgName','InstalledVersion','FixedVersion','Severity','Title','PrimaryURL')})
            counts={s:sum(v['Severity']==s for v in rows) for s in ('CRITICAL','HIGH','MEDIUM','LOW','UNKNOWN')}
            blocked=counts['CRITICAL']>0
            # No analyzable targets is inconclusive, not a clean bill of health.
            verdict='FAIL' if blocked else ('PASS' if analyzed else 'INCONCLUSIVE')
            return jsonify(verdict=verdict,counts=counts,vulnerabilities=rows,targets=analyzed,elapsed=round(time.monotonic()-started,1),report=report,policy='CRITICAL이 하나라도 검출되면 배포 불가',scope='이미지 안의 지원되는 패키지에 대한 알려진 취약점 검사. 실행 환경·접근 권한·설정 오류·미공개 취약점은 이 검사 범위가 아닙니다.')
    finally: slot.release()
if __name__=='__main__': app.run(host='127.0.0.1',port=8080,debug=False)
