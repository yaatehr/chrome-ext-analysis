import json
import requests
import pickle
import pprint
import os
import sys
from collections import Counter

from lxml import html

from extension import try_json_attribute, item_generator, Extension
EXTENSION_ROOT_PATH = "/Users/yaatehr/Library/Application Support/Google/Chrome/Default/Extensions"


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=2, compact=True)

    # root_path = EXTENSION_ROOT_PATH # you can replace this with the path to your extensions
    root_path = os.path.abspath(os.path.dirname(__file__))
    manifest_path = os.path.join(root_path, "manifest_extraction/manifests/")

    id_to_path = {}

    #NOTE Uncomment and comment out the other sectino if you want to evaluate your own extensions

    # for root, dirs, files in os.walk(root_path): #build id to path dict
    #     for file in files:
    #         if file == ("manifest.json"):
    #             full_path = os.path.join(root, file)
    #             id_to_path[os.path.basename(os.path.dirname(os.path.dirname(full_path)))] = full_path

    #NOTE Uncomment and comment out the other section if you want to evaluate scraped extensions

    checkpoint_path = os.path.join(root_path, "extension_class_dict.pkl")
    if not os.path.exists(checkpoint_path):

        for root, dirs, files in os.walk(manifest_path): #build id to path dict
            for file in files:
                if file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    id = file[:-5]
                    id_to_path[id] = full_path


        extension_class_dict = {}
        num_invalid_extensions = 0
        total_num_extensions = len(id_to_path.items())
        counter = 0

        for k,v in id_to_path.items(): # build metadata class for each manifest
            if counter % (total_num_extensions//10) == 0 :
                print(f"completed {counter}/{total_num_extensions} extensions")

            with open(v) as fid:
                data = json.load(fid)
                extension = Extension(data, k)
                # print(extension.__dict__.items())
                if extension.is_valid:
                    extension_class_dict[k] = extension
                else:
                    num_invalid_extensions +=1
            counter += 1

        print(f"finished with  {num_invalid_extensions} failures out of {total_num_extensions} total extensions")

        #Note checkpoint the extensions after their names have been queried
        with open(checkpoint_path, "wb") as checkpoint_file:
            pickle.dump(extension_class_dict, checkpoint_file)
    else:
        extension_class_dict = pickle.load(open(checkpoint_path, "rb"))

    extension_list = list(extension_class_dict.values())



    analytics = {"content_security_policy": Counter(), "permissions": Counter(), "unsafe": Counter(), "misc": Counter(), "num_content_scripts": Counter(), "num_apps_evaluated": len(extension_list)} #TODO add optional permissions:

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

                    analytics["content_security_policy"][t] += 1
                    if "unsafe" in p:
                        analytics["unsafe"][p] += 1
        if extension.permissions:
            perms = extension.permissions.strip('][').split(', ')
            for p in perms:
                p = p.strip("\'")
                analytics["permissions"][p] += 1

        if extension.export:
            analytics["misc"]["export"] += 1
        if extension.manifest_version:
            if "1" in extension.manifest_version or extension.manifest_version == 1:
                analytics["misc"]["manifest_version"] += 1
        if extension.content_scripts:
            js = list(item_generator(extension.manifest_json, "js"))
            if len(js):
                analytics["num_content_scripts"][len(js)] += 1

    pruned_analytics = {}
    num_most_common = 50
    for k,v in analytics.items():
        if isinstance(v, Counter):
            pruned_analytics[k] = v.most_common(num_most_common)
        else:
            pruned_analytics[k] = v

    pp.pprint(pruned_analytics)

    # with open("yaateh_extensions.pkl", 'wb') as f:
    #     pickle.dump((extension_list, analytics), f)

