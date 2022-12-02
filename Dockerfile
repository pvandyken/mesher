FROM deepmi/fastsurfer:gpu-v1.1.1 AS fastsurfer

FROM ubuntu:20.04 as mesher

COPY ./mesher /mesher
# Repeat installation from fastsurfer
# Install required packages for freesurfer to run
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1-mes-glx \
    libxrender-dev && \
    apt clean && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    export PATH="/root/.local/bin:$PATH" && \
    poetry config virtualenvs.options.no-pip true && \
    poetry config virtualenvs.options.no-setuptools true && \
    poetry config virtualenvs.in-project true && \
    cd /mesher && \
    poetry install -n --only main

FROM ubuntu:20.04 AS runtime


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