# Python Script Execution API

A Flask API service that executes arbitrary Python scripts in a sandboxed environment using nsjail.

## Features

- Execute Python scripts via REST API
- Sandboxed execution with nsjail
- Resource limits (CPU, memory, time)
- Support for numpy and pandas
- Returns both function result and stdout

## Requirements

- Docker
- Google Cloud SDK (for deployment)


### Build and Run

```bash
docker build -t python-sandbox .
docker run -p 8080:8080 python-sandbox
```

### Test Locally

```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"message\": \"hello world\"}"
  }'
```

## Deploy to Google Cloud Run

```bash
gcloud run deploy python-sandbox --source . --region us-central1 --allow-unauthenticated
```

## API Usage

### Endpoint: POST /execute

Send a Python script that defines a `main()` function. The function's return value will be captured and returned as JSON.

**Request:**
```json
{
  "script": "def main():\n    return {'result': 42}"
}
```

**Response:**
```json
{
  "result": {"result": 42},
  "stdout": ""
}
```

### Example with stdout

```bash
curl -X POST https://your-service-url.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    print(\"calculating...\")\n    return sum([1,2,3,4,5])"
  }'
```

Response:
```json
{
  "result": 15,
  "stdout": "calculating...\n"
}
```

### Example with numpy

```bash
curl -X POST https://your-service-url.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import numpy as np\ndef main():\n    arr = np.array([1,2,3])\n    return arr.sum().item()"
  }'
```

### Example with pandas

```bash
curl -X POST https://your-service-url.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import pandas as pd\ndef main():\n    df = pd.DataFrame({\"a\": [1,2,3]})\n    return df.sum().to_dict()"
  }'
```

## Limitations

- Scripts must define a `main()` function
- Maximum execution time: 10 seconds
- Memory limit: 256MB
- CPU limit: 3 seconds
- main() must return JSON-serializable objects

## Security

The service uses nsjail to sandbox script execution with:
- Resource limits (memory, CPU, file size)
- Time limits
- Isolated execution environment

## Health Check

```bash
curl http://localhost:8080/healthz
```

Response:
```json
{"status": "ok"}
```

## Project Structure

```
.
├── app.py              # Flask application
├── nsjail.cfg          # nsjail configuration
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition
└── README.md          # This file
```

## Troubleshooting

**Import errors:**
- Only numpy and pandas are installed
- Standard library modules are available

**nsjail errors on Cloud Run:**
- This is expected - Cloud Run has security restrictions
