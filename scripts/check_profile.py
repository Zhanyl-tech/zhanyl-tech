#!/usr/bin/env python3
"""Check README.md's links, anchors and claims against their sources.

    python scripts/check_profile.py links
    python scripts/check_profile.py claims
    python scripts/check_profile.py reproduce --schedlab /path/to/schedlab
    python scripts/check_profile.py all --local ~/work   # sibling checkouts, no GitHub fetches

Why each check exists:
  links      GitHub answers HTTP 200 for any #anchor on a repo page, so a
             renamed heading breaks a deep link silently. Anchors are checked
             against the headings of the README they point into, on that
             repo's default branch, because that is the page a reader lands on.
  claims     the profile's numbers and statuses are copied from other repos.
             For each claim listed in claims.toml this fails when the README's
             quoted text, or the source it is quoted from, changes without the
             other. Sources are read on the default branch, for the same
             reason. README text with no entry in claims.toml is not checked.
  reproduce  some numbers exist only as the output of a seed loop; this re-runs
             it (scripts/reproduce_scheduler_claims.py) and compares. The
             claims step checks that every number a reproduce claim shows in
             the README is also in the output it expects, so the two cannot
             be edited apart.

Standard library only (tomllib needs Python 3.11+). Exit status 1 on any
failure. Hosts that block automated requests (LinkedIn, X) produce a warning,
not a pass, when they answer with their blocking status: the link is reported
as unverified. Any other status from them, a 404 say, still fails.
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urldefrag, urlparse

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CLAIMS = ROOT / "claims.toml"
USER_AGENT = "Mozilla/5.0 (compatible; zhanyl-tech-profile-check)"
# Hosts known to refuse automated clients whatever the page state, with the
# status codes they refuse them with. Only those codes are reported as
# unverified; anything else there (a 404, a timeout) fails like any other link.
# A host covers its subdomains, so www.linkedin.com is linkedin.com.
BOT_BLOCKING_HOSTS: dict[str, frozenset[int]] = {
    "linkedin.com": frozenset({999, 405}),
    # X answers 403 to GitHub's hosted runners (datacenter addresses) for a
    # profile that answers 200 from a home connection. twitter.com redirects
    # to x.com, so it gets the same answer.
    "x.com": frozenset({403}),
    "twitter.com": frozenset({403}),
}
# The ref links and claims are read at. raw.githubusercontent.com resolves HEAD
# to the repo's default branch, the one github.com/<owner>/<repo> shows. A
# pinned SHA from claims.toml [refs] is deliberately not used here: a frozen
# README would keep passing after the live one renamed a heading or changed a
# number, which is exactly the drift these checks exist to catch.
DEFAULT_BRANCH = "HEAD"
NUMBER = re.compile(r"\d+(?:\.\d+)?")

failures: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"WARN  {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def normalise(text: str) -> str:
    """Collapse whitespace and blockquote markers so line wrapping never matters."""
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return re.sub(r"\s+", " ", text).strip()


_cache: dict[str, str] = {}


def fetch(url: str) -> tuple[int, str]:
    if url in _cache:
        return 200, _cache[url]
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            _cache[url] = body
            return resp.status, body
    except urllib.error.HTTPError as err:
        return err.code, ""
    except (urllib.error.URLError, TimeoutError) as err:
        return 0, str(err)


def repo_file(owner: str, repo: str, ref: str, path: str, local: Path | None) -> str | None:
    if local is not None:
        p = local / repo / path
        return p.read_text() if p.is_file() else None
    status, body = fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}")
    return body if status == 200 else None


def github_slugs(markdown: str) -> set[str]:
    """Anchors GitHub generates for a README's headings (with -1, -2 for repeats)."""
    slugs: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in markdown.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        m = None if in_fence else re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if not m:
            continue
        text = re.sub(r"<[^>]+>", "", m.group(1))
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = text.lower()
        # GitHub keeps letters, digits, spaces, hyphens and underscores, then
        # turns each space into a hyphen: "Baselines — the number" becomes
        # "baselines--the-number".
        slug = "".join(c for c in text if c.isalnum() or c in " -_").replace(" ", "-")
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        slugs.add(slug if n == 0 else f"{slug}-{n}")
    return slugs


def bot_blocked(hostname: str | None, status: int) -> bool:
    """Whether `status` is the answer `hostname` gives every automated client,
    so it says nothing about the page."""
    host = (hostname or "").lower()
    return any(
        status in codes and (host == domain or host.endswith(f".{domain}"))
        for domain, codes in BOT_BLOCKING_HOSTS.items()
    )


def readme_links(text: str) -> list[str]:
    links = re.findall(r"\]\(([^)\s]+)\)", text)
    links += re.findall(r'(?:src|href)="([^"]+)"', text)
    return list(dict.fromkeys(links))


def check_links(cfg: dict, local: Path | None) -> None:
    owner = cfg["owner"]
    text = README.read_text()
    for link in readme_links(text):
        url, anchor = urldefrag(link)
        parsed = urlparse(url)
        if not parsed.scheme:
            (ok if (ROOT / url).exists() else fail)(f"relative link {link}")
            continue
        m = re.fullmatch(rf"https://github\.com/{owner}/([^/]+)/?", url)
        if m and local is not None:
            repo = m.group(1)
            (ok if (local / repo).is_dir() else fail)(f"{link} (local checkout)")
        else:
            status, body = fetch(url)
            if bot_blocked(parsed.hostname, status):
                warn(f"{link}: HTTP {status} (host blocks automated clients; unverified)")
                continue
            if not 200 <= status < 400:
                fail(f"{link}: HTTP {status}")
                continue
            ok(f"{link}: HTTP {status}")
        if not anchor:
            continue
        if m:
            repo = m.group(1)
            md = repo_file(owner, repo, DEFAULT_BRANCH, "README.md", local)
            where = "local checkout" if local else "default branch"
            if md is None:
                fail(f"{link}: could not read {repo}/README.md ({where})")
            elif anchor in github_slugs(md):
                ok(f"  anchor #{anchor} exists in {repo}/README.md ({where})")
            else:
                fail(f"{link}: no heading produces #{anchor} in {repo}/README.md ({where})")
        else:
            # An external page: the anchor must be an id or name in its HTML.
            if re.search(rf'(?:id|name)="{re.escape(anchor)}"', body):
                ok(f"  anchor #{anchor} exists")
            else:
                fail(f"{link}: no id or name {anchor!r} in the page")


def unmatched_numbers(profile: str, expect: list[str]) -> list[str]:
    """Numbers in `profile` that `expect` does not also contain, counted with
    multiplicity ("9/10 ... 9/10" needs two 9s and two 10s).

    Both sides of a reproduce claim are typed by hand. Without this, the README
    and `profile` could say 72.4% while `expect`, and so the reproduce step,
    still checked 72.3%. Numbers are compared as written, so 1.2 and 1.20 differ.
    """
    have = Counter(NUMBER.findall(" ".join(expect)))
    need = Counter(NUMBER.findall(profile))
    return sorted((need - have).elements())


def check_claims(cfg: dict, local: Path | None) -> None:
    owner = cfg["owner"]
    readme = normalise(README.read_text())
    ids: set[str] = set()
    for claim in cfg["claim"]:
        cid = claim["id"]
        if cid in ids:
            fail(f"claim {cid}: duplicate id")
        ids.add(cid)
        if normalise(claim["profile"]) not in readme:
            fail(f"claim {cid}: profile text not found in README.md: {claim['profile']!r}")
            continue
        kind = claim["kind"]
        if kind == "reproduce":
            stray = unmatched_numbers(claim["profile"], claim["expect"])
            if stray:
                fail(f"claim {cid}: README shows {', '.join(stray)} but `expect` does not; the reproduce step would not check them")
            else:
                ok(f"claim {cid}: in README, and its numbers match `expect` (values checked by the reproduce step)")
            continue
        if kind == "source":
            repo = claim["repo"]
            where = f"{repo}/{claim['path']}@{'local' if local else 'default branch'}"
            body = repo_file(owner, repo, DEFAULT_BRANCH, claim["path"], local)
        elif kind == "url":
            where = claim["url"]
            status, body = fetch(claim["url"])
            body = normalise(html.unescape(re.sub(r"<[^>]+>", " ", body))) if status == 200 else None
        else:
            fail(f"claim {cid}: unknown kind {kind!r}")
            continue
        if body is None:
            fail(f"claim {cid}: could not read {where}")
            continue
        source = normalise(body)
        missing = [e for e in claim["expect"] if normalise(e) not in source]
        if missing:
            for e in missing:
                fail(f"claim {cid}: {where} does not say {e!r}")
        else:
            ok(f"claim {cid}: {where}")


def check_reproduce(cfg: dict, schedlab: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "reproduce_scheduler_claims.py"), "--schedlab", schedlab],
        check=False,
        capture_output=True,
        text=True,
    )
    print(proc.stdout, end="")
    if proc.returncode != 0:
        # The reproduce script reports every failure on stderr: which schedlab
        # command failed and schedlab's own error (an older CLI rejecting a
        # flag, say), or which output it could not parse. check=True would
        # raise with only the exit status and drop all of that from the log.
        for line in proc.stderr.splitlines():
            print(f"  | {line}")
        fail(f"reproduce_scheduler_claims.py exited {proc.returncode} (its stderr is above)")
        return
    got = normalise(proc.stdout)
    for claim in cfg["claim"]:
        if claim["kind"] != "reproduce":
            continue
        for e in claim["expect"]:
            (ok if normalise(e) in got else fail)(f"claim {claim['id']}: reproduced {e!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["links", "claims", "reproduce", "all"])
    parser.add_argument(
        "--local", type=Path, help="directory holding sibling checkouts; read files from them instead of GitHub"
    )
    parser.add_argument("--schedlab", default="schedlab", help="schedlab CLI for the reproduce step")
    args = parser.parse_args()
    cfg = tomllib.loads(CLAIMS.read_text())
    local = args.local.resolve() if args.local else None

    if args.step in ("links", "all"):
        check_links(cfg, local)
    if args.step in ("claims", "all"):
        check_claims(cfg, local)
    if args.step in ("reproduce", "all"):
        check_reproduce(cfg, args.schedlab)

    print(f"\n{len(failures)} failure(s), {len(warnings)} warning(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
