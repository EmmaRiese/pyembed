"""
The widget loads Skulpt and CodeMirror from vendor/ next to embed.js, not
from a CDN (esm.sh was down on 2026-10-30 and every snippet hung). Running a
snippet must not request anything from another host.
"""

from urllib.parse import urlparse

from harness import run_snippet


def test(page, base_url):
    host = urlparse(base_url).netloc
    external = []

    def note(request):
        if urlparse(request.url).netloc not in (host, ""):
            external.append(request.url)

    page.on("request", note)
    out = run_snippet(page, base_url, "../tests/fixtures/unicode_latin1_ident.json")
    assert out.strip() == "True", out
    assert not external, external
