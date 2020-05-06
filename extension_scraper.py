import json
import os
import sys
import requests
from lxml import html
import pickle
from collections import Counter
EXTENSION_ROOT_PATH = "/Users/yaatehr/Library/Application Support/Google/Chrome/Default/Extensions"


def try_json_attribute(json_input, lookup_key):
    """
    helper method. json object access in try catch
    """
    if not isinstance(lookup_key, str):
        raise RuntimeError("lookup_key must be a string")
    value = list(item_generator(json_input, lookup_key))
    try:
        value = str(value[0])
    except:
        value = None
    return value


def item_generator(json_input, lookup_key):
    """
    recursively index into dictionaries and lists for the target key
    """
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
    """
        class that represents the metadata from each manifest.json
    """
    def __init__(self, json_root, id):
        self.id = id 
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
        r = requests.get(f"https://chrome.google.com/webstore/detail/{self.id}" , allow_redirects=True) #query google api to reverse lookup name from id
        tree = html.fromstring(r.content)
        title = tree.xpath('//title/text()') # get title
        try:
            title = title[0] #unpack list
        except:
            title = f"Error FAILED_TO_PARSE_{self.id}" #error if the list is empty (no title div on the page)

        return title


    def analyze_csp(self): #TODO doesn't do anything yet
        pass
        # if not self.content_security_policy:
        #     print("CSP is secure")
        # if "unsafe-eval" in self.content_security_policy.lower():
        #     pass
        # if "unsafe" in self.content_security_policy:
        #     pass




if __name__ == "__main__":
    root_path = EXTENSION_ROOT_PATH # you can replace this with the path to your extensions
    id_to_path = {}
    for root, dirs, files in os.walk(root_path): #build id to path dict
        for file in files:
            if file == ("manifest.json"):
                full_path = os.path.join(root, file)
                id_to_path[os.path.basename(os.path.dirname(os.path.dirname(full_path)))] = full_path

    extension_list = []
    for k,v in id_to_path.items(): # build metadata class for each manifest
        with open(v) as fid:
            data = json.load(fid)
            extension = Extension(data, k)
            # print(extension.__dict__.items())
            if extension.is_valid:
                extension_list.append(extension)

    analytics = {"csp": Counter(), "permissions": Counter() } #TODO add optional permissions

    for extension in extension_list:
        if extension.content_security_policy:
            policy_types = extension.content_security_policy.split(";")
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
        if extension.permissions:
            perms = extension.permissions.strip('][').split(', ')
            for p in perms:
                analytics["permissions"][p] += 1
            
    print(analytics)



    with open("yaateh_extensions.pkl", 'wb') as f:
        pickle.dump((extension_list, analytics), f)