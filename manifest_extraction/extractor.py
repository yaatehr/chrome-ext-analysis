import json
import os
import subprocess
import sys


IDS_FNAME = "inputs.txt"
TEMP_NAME = "extension"
OUT_DIR = "manifests"


def extract(app_id):
    # return the manifest given the app_id
    out = subprocess.run(
        ["./crx.py", app_id, TEMP_NAME, "--delete"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    manifest = out.stdout.decode()
    if len(manifest) == 0:
        return None
    try:
        t = json.loads(manifest.replace("\n", ""))
        manifest = json.dumps(manifest, indent=2)
    except:
        pass
    return manifest


def load_ids():
    with open(IDS_FNAME) as f:
        return set(f.read().splitlines())


def run_extractor():
    for app_id in load_ids():
        out_fname = f"{OUT_DIR}/{app_id}.json"
        if os.path.exists(out_fname):
            print(f"skipping {app_id}: already found manifest")
            continue
        manifest = extract(app_id)
        if manifest is None:
            print(f"failed {app_id}: couldn't extract json")
            continue
        with open(out_fname, "w") as f:
            f.write(manifest)
            print(f"completed {app_id}")


if __name__ == "__main__":
    run_extractor()
    sys.exit(0)
