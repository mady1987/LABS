FROM python:3.11-bookworm

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
      bzip2 \
      g++ \
      git \
      graphviz \
      libgl1-mesa-glx \
      libhdf5-dev \
      openmpi-bin \
      wget \
      python3-tk && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m -u 1000 myuser

USER myuser

COPY --chown=myuser app app

EXPOSE 8001

CMD ["python", "app/main.py"]