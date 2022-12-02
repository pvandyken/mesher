import asyncio
import logging
import os
from pathlib import Path

import nibabel as nib
import numpy as np
import pyvista as pv
from skimage import measure

logger = logging.getLogger(__name__)


async def create_mesh(
    in_path: Path,
    out_path: Path,
    workdir: Path,
    fs_license: Path = Path(".license"),
):

    tmp = workdir / "mesher"
    tmp.mkdir(exist_ok=True, parents=True)
    if in_path.suffix != ".mgz":
        nib.save(nib.load(in_path), tmp / "t1.mgz")
        in_path = tmp / "t1.mgz"
    os.environ["FASTSURFER_HOME"] = "/fastsurfer"
    proc = await asyncio.create_subprocess_exec(
        "/fastsurfer/run_fastsurfer.sh",
        "--fs_license",
        fs_license.resolve(),
        "--t1",
        in_path,
        "--sid",
        "sub",
        "--sd",
        tmp / "fastsurfer",
        "--seg_only",
        # stdout=asyncio.subprocess.PIPE,
        # stderr=asyncio.subprocess.PIPE,
    )
    # while proc.returncode is None:

    ret = await proc.wait()
    if ret:
        if proc.stderr:
            err = (await proc.stderr.read()).decode()
        else:
            err = ""
        raise Exception(err)
    dparc = tmp / "fastsurfer/sub/mri/aparc.DKTatlas+aseg.deep.mgz"

    img = nib.load(dparc)
    data = img.get_fdata()
    verts, faces, *_ = measure.marching_cubes(data, 0)

    pv_faces = np.hstack([[len(face), *face] for face in faces])

    surf = pv.PolyData(verts, pv_faces)
    centered = surf.translate(np.array(surf.center) * -1, inplace=False)
    pv.save_meshio(out_path, centered)


# def cli(
#     in_path: Path,
#     out_path: Path,
#     fs_license: Path = typer.Option(Path(".license")),
#     workdir: Path = typer.Option(...),
# ):
#     asyncio.run(create_mesh(in_path, out_path, workdir, fs_license))


# if __name__ == "__main__":
#     typer.run(create_mesh)
