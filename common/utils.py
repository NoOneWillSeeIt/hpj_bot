import httpx


def concat_url(url1: httpx.URL | str, url2: httpx.URL | str) -> str:
    return str(httpx.URL(url1).join(url2))
