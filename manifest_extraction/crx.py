#!/usr/bin/env python3.8
import glob
import json
import os
import sys


BASE_URL = "https://clients2.google.com/service/update2/crx?response=redirect&os=mac&arch=x86-64&os_arch=x86-64&nacl_arch=x86-64&prod=chromecrx&prodchannel=unknown&prodversion=81.0.4044.129&acceptformat=crx2,crx3&x=id%3D__APP_ID__%26uc&zipname=__APP_ID__.zip"
APP_ID_PLACEHOLDER = "__APP_ID__"
# FROM: https://www.w3schools.com/tags/ref_urlencode.ASP
USAGE = """Usage 1: PROG app_id app_name

  This will output the the json for the given app_id and download a file
  named {app_name}.crx into the directory in which this is ran. For
  instance, if you run:

    ./crx.py gighmmpiobklfepjocnamgkkbiglidom hello

  then it will output the corresponding json and download a file named
  hello.crx into this directory.

------------------------------------------------------------------------

Usage 2: PROG app_name.crx
  This is basically the save as Usage 1 except the .crx file is provided
  on input.
"""


def url_for_app_id(app_id):
    return BASE_URL.replace(APP_ID_PLACEHOLDER, app_id)


def read_and_output_json(fname):
    with open(fname) as f:
        data = json.load(f)
        print(json.dumps(data))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(0)
    name = sys.argv[1]
    if not name.endswith(".crx"):
        # download the extension first
        try:
            app_name = sys.argv[2]
        except:
            app_name ="extension"
        url = url_for_app_id(name)
        os.system(f"curl -L -o \"{app_name}.crx\" \"{url}\" &> /dev/null")
        # reset the name to be that of the downloaded extension
        name = f"{app_name}.crx"

    # using the .crx file, extract it and output the manifest.json
    os.system("mkdir temp")
    os.system(f"mv {name} temp")
    os.system(f"cd temp && unzip {name} &> /dev/null")
    read_and_output_json("temp/manifest.json")
    os.system(f"mv temp/{name} .")
    os.system("rm -rf temp")
    sys.exit(0)
