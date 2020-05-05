import json
import os
import sys
import requests
from lxml import html
import pickle
from collections import Counter
EXTENSION_ROOT_PATH = "/Users/yaatehr/Library/Application Support/Google/Chrome/Default/Extensions"




def try_json_attribute(json_input, lookup_key):
    if not isinstance(lookup_key, str):
        raise RuntimeError("lookup_key must be a string")
    value = list(item_generator(json_input, lookup_key))
    try:
        value = str(value[0])
    except:
        value = None
    return value


def item_generator(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield v
            else:
                yield from item_generator(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key)

class Extension():
    def __init__(self, json_root, id):
        self.id = id
        self.query_url = "https://chrome.google.com/webstore/detail/"
        self.content_security_policy = try_json_attribute(json_root, "content_security_policy")
        self.permissions = try_json_attribute(json_root, "permissions")
        self.optional_permissions = try_json_attribute(json_root, "optional_permissions")
        self.app = try_json_attribute(json_root, "app")

        self.title = self.get_plaintext_name()
        if "Error".lower() in self.title.lower():
            self.is_valid = False
        else:
            self.is_valid = True

    def get_plaintext_name(self):
        r = requests.get(self.query_url + self.id, allow_redirects=True)
        tree = html.fromstring(r.content)
        title = tree.xpath('//title/text()')
        try:
            title = title[0]
        except:
            title = f"Error FAILED_TO_PARSE_{self.id}"

        return title


    def analyze_csp(self):
        if not self.content_security_policy:
            print("CSP is secure")
        if "unsafe-eval" in self.content_security_policy.lower():
            pass
        if "unsafe" in self.content_security_policy:
            pass




if __name__ == "__main__":
    # root_path = os.path.abspath(os.path.dirname(__file__))
    root_path = EXTENSION_ROOT_PATH
    id_to_path = {}
    with open("temp_output.csv", 'w+') as f:
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file == ("manifest.json"):
                    full_path = os.path.join(root, file)
                    id_to_path[os.path.basename(os.path.dirname(os.path.dirname(full_path)))] = full_path

    extension_list = []
    for k,v in id_to_path.items():
        with open(v) as fid:
            data = json.load(fid)
            e = Extension(data, k)
            # print(e.__dict__.items())
            if e.is_valid:
                extension_list.append(e)
    print(len(extension_list))

    analytics = {"csp": Counter(), "permissions": Counter() }


    for e in extension_list:
        if e.content_security_policy:
            policy_types = e.content_security_policy.split(";")
            t = ""
            for p_type in policy_types:
                for i, p in enumerate(p_type.split()):
                    if i == 0:
                        t = p
                        continue
                    if p == 'self':
                        print(p)
                        continue

                    analytics["csp"][t] += 1
        if e.permissions:
            perms = e.permissions.strip('][').split(', ')
            for p in perms:
                analytics["permissions"][p] += 1
            

        print(analytics)



    with open("yaateh_extensions.pkl", 'wb') as f:
        pickle.dump((extension_list, analytics), f)