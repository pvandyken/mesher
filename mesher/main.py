import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
import aiohttp

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, validator

from mesher.app import create_mesh
from mesher.job import Job, State
from mesher import fs_license

app = FastAPI()
jobs: "dict[str, Job]" = {}
LICENSE = fs_license.get_license_file()


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

class InputURL(BaseModel):
    url: str
    ext: str

    @validator('ext')
    def ext_must_begin_with_period(cls, v):
        if not re.match(r'^\.', v):
            raise ValueError('ext must begin with a period')
        return v


@app.get("/")
async def main():
    return {"msg": "hello world!"}


async def perform_conversion(infile: Path, uid: str):
    work = Path(tempfile.mkdtemp(".mesher-work"))
    try:
        await create_mesh(
            infile, jobs[uid].outfile, fs_license=LICENSE, workdir=work
        )
    except Exception as err:
        jobs[uid] = jobs[uid].set_errored()
        raise err
    else:
        jobs[uid] = jobs[uid].set_finished()
    finally:
        os.remove(infile)
        shutil.rmtree(work)

async def download_infile(infile_url: InputURL, path: Path, uid: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(infile_url.url) as response:
            if response.status >= 400:
                jobs[uid].set_errored()
                return
            with path.open('w+b') as f:
                f.write(await response.read())
    await perform_conversion(path, uid)


def get_uid():
    with tempfile.NamedTemporaryFile(
        "r", suffix=".obj", prefix="mesher_out.", delete=False
    ) as f:
        outfile = Path(f.name)
    uid = uuid.uuid4().hex
    jobs[uid] = Job.new_job(outfile)
    return uid


@app.post("/jobs")
async def convert_url(background_tasks: BackgroundTasks, infile: InputURL):
    with tempfile.NamedTemporaryFile(
        "w+b", suffix=infile.ext, delete=False
    ) as f:
        tmpfile = Path(f.name)
    uid = get_uid()
    background_tasks.add_task(download_infile, infile, tmpfile, uid)
    return {"jobid": uid}
            
        

@app.post("/jobs/data")
async def convert_data(background_tasks: BackgroundTasks, infile: UploadFile):
    with tempfile.NamedTemporaryFile(
        "w+b", suffix="".join(Path(infile.filename).suffixes), delete=False
    ) as f:
        f.write(await infile.read())
        tmpfile = Path(f.name)

    uid = get_uid()
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
