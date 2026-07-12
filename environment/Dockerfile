# Dockerfile — JupyterLab image for simdes courseware
# Build:  docker build -t simdes-jupyter -f environment/Dockerfile .
# Run:    docker compose up jupyter   (preferred; see docker-compose.yml)

FROM python:3.11-slim

LABEL maintainer="course-author"
LABEL description="JupyterLab environment for Simulation Without a Black Box"

# System dependencies for matplotlib PDF backend and LaTeX rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy dependency specification first (layer cache)
COPY environment/requirements.txt /workspace/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Install the simdes package in editable mode
COPY simdes/ /workspace/simdes/
RUN pip install --no-cache-dir -e /workspace/simdes/

# Copy the rest of the repo (mounted as volume in docker-compose, so this
# is used only for standalone docker build; changes on disk are visible in
# compose mode)
COPY . /workspace/

# JupyterLab configuration: no browser, listen on all interfaces
ENV JUPYTER_ENABLE_LAB=yes
EXPOSE 8888

CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--NotebookApp.token=''", \
     "--NotebookApp.password=''"]
