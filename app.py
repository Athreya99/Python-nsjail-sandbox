import os
import json
import subprocess
import tempfile
from flask import Flask, request, jsonify
import os, tempfile, subprocess, shutil
app = Flask(__name__)

MAX_SCRIPT_SIZE = 100000
NSJAIL_BIN = shutil.which("nsjail") or "/usr/bin/nsjail"
NSJAIL_CFG = os.getenv("NSJAIL_CFG", "/app/nsjail.cfg")
PYTHON_BIN = "/usr/local/bin/python3"  

NSJAIL_BIN = shutil.which("nsjail") or "/usr/local/bin/nsjail"
PYTHON_BIN = "/usr/local/bin/python3"

def run_script_in_nsjail(script: str, timeout_sec: int = 10):
    tmpdir = tempfile.mkdtemp(prefix="exec_", dir="/tmp")  
    script_path = os.path.join(tmpdir, "script.py")
    with open(script_path, "w") as f:
        f.write(script)
    # no mounts
    cmd = [
        NSJAIL_BIN,
        "--disable_clone_newuser",
        "--disable_clone_newpid",
        "--disable_clone_newuts",
        "--disable_clone_newipc",
        "--disable_clone_newnet",
        "--disable_clone_newcgroup",
        "--disable_clone_newns",
        "--time_limit", "10",
        "--rlimit_as", "268435456",  
        "--rlimit_cpu", "5",
        "--rlimit_fsize", "10485760", 
        "--", PYTHON_BIN, script_path,
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return stdout, stderr, code


@app.route('/execute', methods=['POST'])
def execute():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    try:
        data = request.get_json()
    except:
        return jsonify({"error": "Invalid JSON"}), 400
    
    if not data or 'script' not in data:
        return jsonify({"error": "No script provided"}), 400
    
    script = data['script']
    
    if not isinstance(script, str):
        return jsonify({"error": "Script must be a string"}), 400
    
    if len(script) == 0:
        return jsonify({"error": "Script cannot be empty"}), 400
    
    if len(script) > MAX_SCRIPT_SIZE:
        return jsonify({"error": "Script too large"}), 400
    
    if 'def main' not in script:
        return jsonify({"error": "Script must define main()"}), 400
    
    #  capture output
    wrapped_script = f"""
{script}

import json, sys
from io import StringIO

capture = StringIO()
old_stdout = sys.stdout
sys.stdout = capture

try:
    ret = main()
    sys.stdout = old_stdout
    print(json.dumps({{"result": ret, "stdout": capture.getvalue()}}))
except Exception as err:
    sys.stdout = old_stdout
    print(json.dumps({{"error": str(err)}}))
"""
    
    out, err, status = run_script_in_nsjail(wrapped_script)
    
    if status != 0:
        return jsonify({"error": "Script failed", "stderr": err}), 400
    
    try:
        result = json.loads(out)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except:
        return jsonify({"error": "Bad output"}), 400


@app.route('/healthz')
def healthz():
    return {"status": "ok | healthy"}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
