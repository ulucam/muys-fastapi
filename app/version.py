import json
from functools import lru_cache
from urllib.request import Request, urlopen


YEREL_SURUM = "v0.3"
GITHUB_RELEASE_API = "https://api.github.com/repos/ulucam/muys-fastapi/releases/latest"


@lru_cache(maxsize=1)
def guncel_surumu_al() -> str:
    """Uygulama açılışında GitHub release sürümünü dene; erişim yoksa yerel etiketi kullan."""
    try:
        istek = Request(
            GITHUB_RELEASE_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "MUYS-FastAPI",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urlopen(istek, timeout=2) as yanit:
            return json.load(yanit).get("tag_name") or YEREL_SURUM
    except Exception:
        return YEREL_SURUM
