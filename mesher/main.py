import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Union

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse

from mesher.app import create_mesh
from mesher.job import Job, State

app = FastAPI()
jobs: "dict[str, Job]" = {}


def job_success(uid: str):
    if not uid in jobs:
        return False
    if jobs[uid].status == State.success:
        return True
    return False


def job_finished(uid: str):
    if not uid in jobs or jobs[uid].status == State.running:
        return False
    return True


@app.get("/")
async def main():
    return {"msg": "hello world!"}


async def perform_conversion(infile: Path, uid: str):
    work = Path(tempfile.mkdtemp(".mesher-work"))
    try:
        await create_mesh(
            infile, jobs[uid].outfile, fs_license=Path(".license"), workdir=work
        )
    except Exception as err:
        jobs[uid] = jobs[uid].set_errored()
        raise err
    else:
        jobs[uid] = jobs[uid].set_finished()
    finally:
        os.remove(infile)
        shutil.rmtree(work)


@app.post("/jobs")
async def convert(infile: UploadFile, background_tasks: BackgroundTasks):
    with tempfile.NamedTemporaryFile(
        "w+b", suffix="".join(Path(infile.filename).suffixes), delete=False
    ) as f:
        f.write(await infile.read())
        tmpfile = Path(f.name)

    with tempfile.NamedTemporaryFile(
        "r", suffix=".obj", prefix="mesher_out.", delete=False
    ) as f:
        out = Path(f.name)

    uid = uuid.uuid4().hex
    jobs[uid] = Job.new_running(out)

    background_tasks.add_task(perform_conversion, tmpfile, uid)
    return {"jobid": uid}


@app.get("/jobs/{uid}")
async def status(uid: str):
    if not uid in jobs:
        raise HTTPException(404)
    if jobs[uid].status == State.success:
        status = "done"
    elif jobs[uid].status == State.error:
        status = "error"
    else:
        status = "running"

    return {"status": status}


@app.get("/jobs/{uid}/data")
async def get(uid: str):
    if not job_success(uid):
        raise HTTPException(404)

    return FileResponse(jobs[uid].outfile)


@app.delete("/jobs/{uid}")
async def delete(uid: str):
    if not job_finished(uid):
        raise HTTPException(404)
    os.remove(jobs[uid].outfile)
    del jobs[uid]
    return {"status": "success"}
