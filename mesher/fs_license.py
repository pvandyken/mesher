from pathlib import Path
import os
import google_secrets as secrets

LICENSE =  Path("/fs_license")

def get_license_file():
    if LICENSE.exists():
        return LICENSE
    if lic := os.environ.get("FS_LICENSE"):
        data = lic.encode()
    else:
        data = secrets.access_secret_version('mesher', 'fs_license', 'latest')
    LICENSE.write_bytes(data)
    return LICENSE
