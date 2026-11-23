import json
import urllib.request
from typing import Any, List

TIMEOUT_SECONDS = 10


def fetch_json(url: str) -> List[Any]:
    with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read())


def post_json(url: str, payload: List[Any]) -> None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS):
        pass
