FROM deepmi/fastsurfer:gpu-v1.1.1
COPY ./app /app
RUN python -m venv /venv \
    /venv/bin/python -m pip install -r /app/requirments.txt

WORKDIR "/app"
ENTRYPOINT ["/venv/bin/python", "./run.py"]
