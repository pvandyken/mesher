import numpy as np
import typer
import pyvista as pv
from skimage import measure
import nibabel as nib
import sys
import subprocess as sp
from pathlib import Path


def main(
    in_path: Path,
    out_path: Path,
    fs_license: Path = typer.Option(...),
    workdir: Path = typer.Option(...)
):
    tmp = workdir/'mesher'
    tmp.mkdir(exist_ok=True, parents=True)
    if in_path.suffix != ".mgz":
        nib.save(nib.load(in_path), tmp/'t1.mgz')
        in_path = tmp/'t1.mgz'
    sp.run([
        "/fastsurfer/run_fastsurfer.sh",
        "--fs_license",
        fs_license,
        "--t1",
        in_path
        '--sid',
        'sub',
        '--sd',
        tmp/'fastsurfer',
    ])
    dparc = tmp/'fastsurfer/sub/mri/aparc.DKTatlas+aseg.deep.mgz'

    img = nib.load(dparc)
    data = img.get_fdata()
    verts, faces, *_ = measure.marching_cubes(data, 0)

    pv_faces = np.hstack([
        [len(face), *face] for face in faces
    ])

    surf = pv.PolyData(verts, pv_faces)
    centered = surf.translate(np.array(surf.center) * -1, inplace=False)
    pv.save_meshio(out_path, centered)

if __name__ == "__main__":
    typer.run(main)
