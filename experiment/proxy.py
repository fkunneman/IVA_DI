"""Redirect HTTP requests to another server."""

from typing import Dict, List, Tuple
import os
import re
from glob import glob
from mitmproxy import http
from mitmproxy.addonmanager import Loader

PORT = 8000

PROXY_STORE_PATH = "proxy-store"
PROXY_OVERRIDE_PATH = "proxy-override"
REDIRECT_CHECKS = ("", "leefomgeving/een-melding-doen")

lookup: Dict[str, Dict[str, str]] = {}

# overrides per domain name, match pattern, mime type, override target filename
overrides: Dict[str, List[Tuple[str, str, str]]] = {}


def load(loader: Loader) -> None:
    try:
        with open(os.path.join(PROXY_OVERRIDE_PATH, "override.tsv"), "rt") as f:
            for line in f.readlines():
                host, pattern, mime_type, target = line.strip().split("\t")

                if host not in overrides:
                    overrides[host] = []

                overrides[host].append((pattern, mime_type, target))

    except FileNotFoundError:
        print("No override file")

    for filepath in glob(PROXY_STORE_PATH + "/*.tsv"):
        hostname = os.path.split(filepath)[-1][:-4]
        host_lookup = {}
        with open(filepath, "rt") as f:
            for line in f.readlines():
                path, mime_type = line.split("\t")
                host_lookup[path] = mime_type.strip()

        lookup[hostname] = host_lookup


def done() -> None:
    for host, host_lookup in lookup.items():
        with open(os.path.join(PROXY_STORE_PATH, host + ".tsv"), mode="w+") as f:
            f.writelines(
                f"{path}\t{mime_type}\n" for path, mime_type in host_lookup.items()
            )


def request(flow: http.HTTPFlow) -> None:
    if flow.request.method == "GET":
        # pretty_host takes the "Host" header of the request into account,
        # which is useful in transparent mode where we usually only have the IP
        # otherwise.
        host = flow.request.pretty_host
        path_hash = request_path_hash(flow.request)
        try:
            host_override = overrides[host]
            for pattern, mime_type, target in host_override:
                if re.match(pattern, path_hash):
                    override_request(flow, host, target, mime_type)
                    return
        except KeyError:
            pass


def restore_request(
    flow: http.HTTPFlow, host: str, path_hash: str, mime_type: str
) -> None:
    with open(path_hash_physical_path(host, path_hash), mode="rb") as f:
        flow.response = http.Response.make(200, f.read(), {"Content-Type": mime_type})


def override_request(
    flow: http.HTTPFlow, host: str, target: str, mime_type: str
) -> None:
    print(f"Override {host} {target}")
    with open(os.path.join(PROXY_OVERRIDE_PATH, host, target), mode="rb") as f:
        flow.response = http.Response.make(200, f.read(), {"Content-Type": mime_type})


def response(flow: http.HTTPFlow):
    if flow.request.method == "GET":
        # store a copy
        host = flow.request.pretty_host
        try:
            host_lookup = lookup[host]
        except KeyError:
            lookup[host] = host_lookup = {}

        path_hash = request_path_hash(flow.request)
        try:
            mime_type = flow.response.headers["Content-Type"]
        except KeyError:
            mime_type = ""

        host_lookup[path_hash] = mime_type

        content = flow.response.content

        store_request(content, host, path_hash)


def store_request(content: bytes | None, host: str, path_hash: str) -> None:
    physical_path = path_hash_physical_path(host, path_hash)
    os.makedirs(os.path.dirname(physical_path), exist_ok=True)
    with open(physical_path, mode="wb+") as f:
        f.write(content)


def request_path_hash(request: http.Request) -> str:
    # make sure we always start with a slash
    path = "/".join(("", *request.path_components))
    query_items = [f"{key}={value}" for key, value in request.query.items(True)]
    if len(query_items):
        path += f"{hash(';'.join(query_items))}"

    return "/" if not path else path


def path_hash_physical_path(host: str, path_hash: str) -> str:
    return os.path.join(
        PROXY_STORE_PATH, host, path_hash.replace("_", "__").replace("/", "_")
    )
