import json
import pickle
import re
import sys
from collections import Counter
from typing import Callable, Dict, Set

from extension import Extension


DATA_FNAME = "extension_class_dict.pkl"
# this is the shortest permission length found on the website
MIN_PERMISSION_LENGTH = 3
OFFICIAL_PERMISSIONS = None
OUT_FNAME = "extension_data.csv"
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


def run() -> None:
    id_to_extension_map = load_data()
    set_chrome_permissions(id_to_extension_map)
    print(VALID_PERMISSIONS)
    # TODO: add csp stuffs
    headers = ["title", "app_id", *VALID_PERMISSIONS]
    permission_resolvers = [
        EResolver.permission_resolver(p) for p in VALID_PERMISSIONS
    ]
    resolvers = [EResolver.title, EResolver.app_id, *permission_resolvers]

    data = [headers] + [
        [r(ext) for r in resolvers]
        for ext in id_to_extension_map.values()
        if ext.is_valid
    ]

    with open(OUT_FNAME, "w") as f:
        for line in data:
            f.write(",".join(line) + "\n")


if __name__ == "__main__":
    run()
    sys.exit(0)
