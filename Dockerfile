FROM deepmi/fastsurfer:gpu-v1.1.1 AS fastsurfer

FROM python:3.10.7-slim as mesher

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1-mesa-glx \
    libxrender-dev && \
    apt clean && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    export PATH="/root/.local/bin:$PATH" && \
    poetry config virtualenvs.options.no-pip true && \
    poetry config virtualenvs.options.no-setuptools true && \
    poetry config virtualenvs.in-project true 

COPY poetry.lock /mesher/poetry.lock
COPY pyproject.toml /mesher/pyproject.toml
COPY README.md /mesher/README.MD
WORKDIR /mesher
RUN /root/.local/bin/poetry install -n --only main
COPY . /mesher
ENTRYPOINT ["/bin/bash"]


FROM python:3.10.7-slim AS runtime

# Repeat installation from fastsurfer
# Install required packages for freesurfer to run
RUN apt-get update && apt-get install -y --no-install-recommends \
      tcsh \
      time \
      bc \
      gawk \
      libgomp1 \
      # Plus some extensions we need for pyvista
      libgl1-mesa-glx \
      libxrender-dev && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

# Add FreeSurfer Environment variables
ENV OS=Linux \
    FS_OVERRIDE=0 \
    FIX_VERTEX_AREA= \
    SUBJECTS_DIR=/opt/freesurfer/subjects \
    FSF_OUTPUT_FORMAT=nii.gz \
    FREESURFER_HOME=/opt/freesurfer \
    PYTHONUNBUFFERED=0 \
    PATH=/venv/bin:/opt/freesurfer/bin:$PATH

COPY --from=fastsurfer /venv /venv
COPY --from=fastsurfer /opt/freesurfer /opt/freesurfer
COPY --from=fastsurfer /fastsurfer /fastsurfer
COPY --from=mesher /mesher /mesher


EXPOSE 8080
ARG fs_license=''
ENV FS_LICENSE ${fs_license}
WORKDIR "/mesher"
ENTRYPOINT ["./.venv/bin/uvicorn", "mesher.main:app", "--host", "0.0.0.0", "--port", "8080"]
# COPY ./app /app

# RUN python -m venv /venv \
#     /venv/bin/python -m pip install -r /app/requirments.txt

# WORKDIR "/app"
# ENTRYPOINT ["/venv/bin/python", "./run.py"]

# FROM deepmi/fastsurfer:gpu-v1.1.1
# COPY ./app /app
# RUN python -m venv /venv \
#     /venv/bin/python -m pip install -r /app/requirments.txt

# WORKDIR "/app"
# ENTRYPOINT ["/venv/bin/python", "./run.py"]