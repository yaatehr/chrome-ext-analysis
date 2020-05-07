import json
import requests
from typing import Any, Dict, Generator

from lxml import html

# basic json type. typing doesn't allow recursive types so
# this is a hack work-around
JsonType = Dict[str, Any]


def try_json_attribute(json_input: JsonType, lookup_key: str) -> Any:
    """
    helper method. json object access in try catch
    """
    if not isinstance(lookup_key, str):
        raise TypeError("lookup_key must be a string")
    value = list(item_generator(json_input, lookup_key))
    try:
        value = str(value[0])
    except:
        value = None
    return value


def item_generator(json_input: JsonType, lookup_key: str) -> Generator[Any, None, None]:
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
    else:
        # it's a value type, and in this case it would have been
        # yielded already
        pass


class Extension:
    """
    Represents the metadata in an extensions' manifest.json
    """
    def __init__(self, json_root: JsonType, app_id: str) -> None:
        self.id = app_id

        self.app = try_json_attribute(json_root, "app")
        self.content_scripts = try_json_attribute(json_root, "content_scripts")
        self.content_security_policy = try_json_attribute(
            json_root, "content_security_policy"
        )
        self.export = try_json_attribute(json_root, "export")
        self.manifest_version = try_json_attribute(json_root, "manifest_version")
        self.optional_permissions = try_json_attribute(
            json_root, "optional_permissions"
        )
        self.permissions = try_json_attribute(json_root, "permissions")

        self.manifest_json = json_root
        self.title = self._get_plaintext_name()
        self.is_valid = "error" not in self.title.lower()

    def _get_plaintext_name(self) -> str:
        #query google api to reverse lookup name from id
        r = requests.get(
            f"https://chrome.google.com/webstore/detail/{self.id}" ,
            allow_redirects=True
        )
        tree = html.fromstring(r.content)
        # this returns a list, so we get the first one. If it's
        # empty, that means there are no title on the page
        title = tree.xpath('//title/text()')
        try:
            return title[0]
        except IndexError:
            return f"Error FAILED_TO_PARSE_{self.id}"

    def csp(self):
        if self.content_security_policy is None:
            return None
        csps = self.content_security_policy.split(";")
        csp_map = {}
        for csp in csps:
            key, *values = csp.strip().split(" ")
            csp_map[key] = values
        return csp_map

    def analyze_csp(self):
        # TODO: note that the csp is on `self.csp` which is shorter
        # if not self.content_security_policy:
        #     print("CSP is secure")
        # if "unsafe-eval" in self.content_security_policy.lower():
        #     pass
        # if "unsafe" in self.content_security_policy:
        #     pass
        raise NotImplementedError


    def __str__(self):
        """
        Turn metadata from each extension into a string.
        To be used for line by line CSV extraction
        """
        pass

