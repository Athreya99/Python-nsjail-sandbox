from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import json
import sys

app = Flask(__name__)

def run_script(script):
    #execution directory
    with tempfile.TemporaryDirectory(dir='/app/sandbox') as tmpdir:
        script_path = os.path.join(tmpdir,'script.py')
        
        # user script
        with open(script_path,  'w') as f:
            wrapped_script = f"""
{script}
import json
try:
    result = main()
    if isinstance(result, (dict, list, str, int, float, bool, type(None))):
        print(json.dumps(result))
    else:
        raise ValueError("main() must return a JSON-serializable object")
except Exception as e:
    import sys, traceback
    traceback.print_exc(file=sys.stderr)
    raise
"""
            f.write(wrapped_script)
        
        try:
            # Run the script in nsjail
            cmd = [
                '/usr/local/bin/nsjail',
                '--config', '/app/nsjail.cfg',
                '--',
                sys.executable,
                script_path
            ]
            
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=tmpdir)
            

            if process.returncode == 0 and process.stdout.strip():
                try:
                    result = json.loads(process.stdout.strip())
                    return {'result': result}
                except:
                    return {'error': 'result fetch failed', 'output': process.stdout, 'errors': process.stderr}
            else:
                return {'error': 'script run failed', 'output': process.stdout, 'errors': process.stderr}
                
        except subprocess.TimeoutExpired:
            return {'error': 'Timeout expired'}
        except Exception as e:
            return {'error': str(e)}


@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    
    if not data or 'script' not in data:
        return jsonify({'error':'No script provided'}), 400
    
    script = data['script']
    
    if not script.strip():
        return jsonify({'error':'Script is empty'}), 400
    
    if 'def main()' not in script:
        return jsonify({'error':'Script needs a main() function'}), 400
    
    result = run_script(script)
    return jsonify(result)


@app.route('/healthz')
def health():
    return jsonify({'status': 'ok | healthy'})


@app.route('/')
def home():
    return jsonify({'message': 'Python sandbox - POST your script to /execute'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)