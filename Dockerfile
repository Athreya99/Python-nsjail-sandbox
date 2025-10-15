FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    autoconf bison flex gcc g++ git \
    libprotobuf-dev libnl-route-3-dev \
    libtool make pkg-config protobuf-compiler \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/google/nsjail.git /nsjail \
    && cd /nsjail && make \
    && mv /nsjail/nsjail /usr/local/bin/ \
    && rm -rf /nsjail

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY app.py /app/app.py
COPY nsjail.cfg /app/nsjail.cfg

WORKDIR /app

RUN mkdir -p /tmp/sandbox

EXPOSE 8080

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]