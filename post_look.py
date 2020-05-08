import json
import pickle
import re
import sys
from collections import Counter
from typing import Callable, Dict, List, Set

from extension import Extension


DATA_FNAME = "extension_class_dict.pkl"
# this is the shortest permission length found on the website
MIN_PERMISSION_LENGTH = 3
OFFICIAL_PERMISSIONS = None
OUT_FNAME = "extension_data_csp.csv"
VALID_PERMISSIONS = None

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
VALID_CHARACTERS = ALPHABET + ALPHABET.upper() + " ()-0123456789&|_"


def load_official_permissions() -> Set[str]:
    with open("chrome_permissions.txt") as f:
        return set(f.read().splitlines())


def load_data() -> Dict[str, Extension]:
    with open(DATA_FNAME, "rb") as f:
        return pickle.load(f)


def is_chrome_permission(permission: str) -> bool:
    return re.fullmatch("[a-zA-Z]+", permission) is not None and len(permission) >= MIN_PERMISSION_LENGTH


def set_chrome_permissions(id_to_extension_map: Dict[str, Extension]) -> None:
    global OFFICIAL_PERMISSIONS, VALID_PERMISSIONS
    OFFICIAL_PERMISSIONS = load_official_permissions()
    VALID_PERMISSIONS = OFFICIAL_PERMISSIONS.copy()
    for ext in id_to_extension_map.values():
        if ext.permissions is None:
            continue
        for p in ext.permissions:
            if p in OFFICIAL_PERMISSIONS:
                continue
            # using this to check if we missed anything, but it should
            # not print.
            if is_chrome_permission(p):
                VALID_PERMISSIONS.add(p)
                print(f"|{p}| found somehow!")
    VALID_PERMISSIONS = sorted(list(VALID_PERMISSIONS))


def remove_weird(s: str) -> str:
    return "".join(c for c in s if c in VALID_CHARACTERS)


def has_base64_hash(items: List[str]) -> bool:
    return any(is_base64_hash(el) for el in items)


# According to:
#   https://www.w3.org/TR/2015/CR-CSP2-20150721/#source-list-syntax
# there are only 3 valid hash functions (and this is also vaguely confirmed
# by the Chrome website on:
#   https://developer.chrome.com/extensions/contentSecurityPolicy#relaxing
def is_base64_hash(s: str) -> bool:
    hash_starts = ["sha256-", "sha384-", "sha512-"]
    return any(s.startswith(f"'{hs}") for hs in hash_starts)


def has_non_localhost_http_url(items: List[str]) -> bool:
    return any(
        (s.startswith("http:") and ("localhost" not in s)) for s in items
    )


class EResolver:
    @staticmethod
    def title(ext: Extension) -> str:
        title = ext.title.replace(" - Chrome Web Store", "").strip()
        return remove_weird(title)

    @staticmethod
    def app_id(ext: Extension) -> str:
        return ext.id

    @staticmethod
    def permission_resolver(permission) -> Callable[[Extension], str]:
        return lambda ext: str(int(ext.has_permission(permission)))

    @staticmethod
    def manifest_version(ext: Extension) -> str:
        return str(int(str(ext.manifest_version) == "2")).lower()

    CSP_HEADERS = [
        # script-src
        "script-scr:unsafe-eval",
        "script-scr:unsafe-eval-base64-hash",
        "script-scr:unsafe-inline",
        "script-scr:unsafe-inline-base64-hash",
        "script-src:non-localhost-http-url",
        # style-src
        "style-scr:unsafe-eval",
        "style-scr:unsafe-eval-base64-hash",
        "style-scr:unsafe-inline",
        "style-scr:unsafe-inline-base64-hash",
        "style-src:non-localhost-http-url",
        # default src, setting this is good so that everything
        # else that is src doesn't fallback to *
        "good#default-src",
        # other csps that should be set to something because
        # the default-src doesn't affect them
        "good#base-uri",
        "good#form-action",
        "good#frame-ancestors",
        "good#plugin-types",
        "good#report-uri",
        "good#sandbox",
    ]

    @staticmethod
    def csp(extension: Extension) -> List[str]:
        csp = extension.csp()
        # script-src
        script_src_u_eval = [0, 0]
        script_src_u_inline = [0, 0]
        script_src_non_localhost = 0
        if csp is not None:
            script_src = csp.get("script-src", [])
            has_hash = has_base64_hash(script_src)
            u_eval = "'unsafe-eval'" in script_src
            u_inline = "'unsafe-inline'" in script_src
            if u_eval:
                script_src_u_eval[int(has_hash)] = 1
            if u_inline:
                script_src_u_inline[int(has_hash)] = 1
            script_src_non_localhost = int(has_non_localhost_http_url(script_src))

        # style-src
        style_src_u_eval = [0, 0]
        style_src_u_inline = [0, 0]
        style_src_non_localhost = 0
        if csp is not None:
            style_src = csp.get("style-src", [])
            has_hash = has_base64_hash(style_src)
            u_eval = "'unsafe-eval'" in style_src
            u_inline = "'unsafe-inline'" in style_src
            if u_eval:
                style_src_u_eval[int(has_hash)] = 1
            if u_inline:
                style_src_u_inline[int(has_hash)] = 1
            style_src_non_localhost = int(has_non_localhost_http_url(style_src))

        default_src = 0
        if csp is not None:
            default_section = csp.get("default-src", [])
            default_src = int(len(default_section) > 0)

        good_csps_keys = [
            "base-uri",
            "form-action",
            "frame-ancestors",
            "plugin-types",
            "report-uri",
            "sandbox",
        ]
        good_csps_values = [0 for _ in good_csps_keys]
        if csp is not None:
            good_csps_values = [
                int(len(csp.get(k, [])) > 0) for k in good_csps_keys
            ]

        return list(map(str, [
            *script_src_u_eval,
            *script_src_u_inline,
            script_src_non_localhost,
            *style_src_u_eval,
            *style_src_u_inline,
            style_src_non_localhost,
            default_src,
            *good_csps_values,
        ]))

    URL_HEADERS = []

    @staticmethod
    def url_permissions(extension: Extension) -> List[str]:
        return []


def run() -> None:
    id_to_extension_map = load_data()
    set_chrome_permissions(id_to_extension_map)
    # COMMENT: I commented out the permissions stuffs since we don't
    #          really need them rn (they're already extracted in a sheet)
    # permission_headers = VALID_PERMISSIONS
    # permission_resolvers = [
    #     EResolver.permission_resolver(p) for p in VALID_PERMISSIONS
    # ]
    headers = [
        "title",
        "app_id",
        "manifest_version",
        *EResolver.URL_HEADERS,
        *EResolver.CSP_HEADERS,
    ]
    resolvers = [
        EResolver.title, EResolver.app_id, EResolver.manifest_version
    ]
    extend_resolvers = [EResolver.url_permissions, EResolver.csp]

    data = [headers]
    for app_id in sorted(id_to_extension_map.keys()):
        ext = id_to_extension_map[app_id]
        if not ext.is_valid:
            continue
        row = [r(ext) for r in resolvers]
        for er in extend_resolvers:
            row.extend(er(ext))
        data.append(row)

    with open(OUT_FNAME, "w") as f:
        for line in data:
            f.write(",".join(line) + "\n")


if __name__ == "__main__":
    run()
    sys.exit(0)
