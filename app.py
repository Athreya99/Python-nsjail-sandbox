import os
import json
import subprocess
import tempfile
from flask import Flask, request, jsonify

app = Flask(__name__)

NSJAIL_CFG = '/app/nsjail.cfg'
MAX_SCRIPT_SIZE = 100000


def run_script(script):
        tmpdir = tempfile.mkdtemp()
        script_path = os.path.join(tmpdir, "script.py")
        with open(script_path, "w") as f:
            f.write(script)
        
        cmd = ["nsjail","--config",NSJAIL_CFG, 
               "--bindmount_ro",tmpdir,"--", 
               "/usr/local/bin/python3",script_path]
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired:
            return "", "Execution timeout", -1
        except Exception as e:
            return "", str(e), -1


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
    
    out, err, status = run_script(wrapped_script)
    
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
