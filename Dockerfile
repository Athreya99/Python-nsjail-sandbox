FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y autoconf bison flex gcc g++ git libprotobuf-dev libnl-route-3-dev libtool make pkg-config protobuf-compiler && rm -rf /var/lib/apt/lists/* && git clone --depth 1 https://github.com/google/nsjail.git /tmp/nsjail && cd /tmp/nsjail && make && mv /tmp/nsjail/nsjail /usr/local/bin/ && rm -rf /tmp/nsjail

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/nsjail /app/sandbox

ENV PORT=8080

EXPOSE 8080

CMD ["python", "app.py"]