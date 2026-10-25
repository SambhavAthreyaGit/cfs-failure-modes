"""Deterministic lookups: do cited papers and named compounds actually exist?"""

import os
import re
import time
from difflib import SequenceMatcher
from urllib.parse import quote

import requests

EMAIL = os.getenv("CONTACT_EMAIL", "")
HEADERS = {"User-Agent": f"cfs-failure-modes/0.1 (mailto:{EMAIL})" if EMAIL else "cfs-failure-modes/0.1"}
TIMEOUT = 20


def _get(url: str, **params):
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            return r
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return None


def similar(a: str, b: str) -> float:
    norm = lambda s: re.sub(r"[^a-z0-9 ]", "", (s or "").lower())
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def check_doi(doi: str) -> dict:
    r = _get(f"https://api.crossref.org/works/{quote(doi.strip())}")
    if r is None:
        return {"status": "lookup_error"}
    if r.status_code != 200:
        return {"status": "not_found"}
    titles = r.json()["message"].get("title") or [""]
    return {"status": "found", "real_title": titles[0]}


def check_pmid(pmid: str) -> dict:
    r = _get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
             db="pubmed", id=pmid.strip(), retmode="json", email=EMAIL)
    if r is None or r.status_code != 200:
        return {"status": "lookup_error"}
    doc = r.json().get("result", {}).get(pmid.strip())
    if not doc or "error" in doc:
        return {"status": "not_found"}
    return {"status": "found", "real_title": doc.get("title", "")}


def search_title(title: str) -> dict:
    r = _get("https://api.crossref.org/works", **{"query.bibliographic": title, "rows": 3})
    if r is None or r.status_code != 200:
        return {"status": "lookup_error"}
    items = r.json()["message"].get("items", [])
    best = max(items, key=lambda it: similar(title, (it.get("title") or [""])[0]), default=None)
    if best and similar(title, (best.get("title") or [""])[0]) >= 0.85:
        return {"status": "found", "real_title": best["title"][0], "doi": best.get("DOI")}
    return {"status": "not_found"}


def verify_citation(cit: dict) -> dict:
    """Return the citation with a verdict:
    verified       - the identifier resolves and the title matches the claim (or no title was claimed)
    mismatch       - the identifier resolves, but to a different paper (misattribution)
    not_found      - no such DOI/PMID, or no paper with that title
    unverifiable   - nothing specific enough to check
    lookup_error   - network/API problem; rerun later
    """
    claimed = cit.get("title") or ""
    if cit.get("doi"):
        res = check_doi(cit["doi"])
    elif cit.get("pmid"):
        res = check_pmid(cit["pmid"])
    elif len(claimed) > 20:
        res = search_title(claimed)
    else:
        return {**cit, "verdict": "unverifiable"}

    if res["status"] != "found":
        return {**cit, "verdict": res["status"]}
    if claimed and (cit.get("doi") or cit.get("pmid")) and similar(claimed, res["real_title"]) < 0.6:
        return {**cit, "verdict": "mismatch", "real_title": res["real_title"]}
    return {**cit, "verdict": "verified", "real_title": res["real_title"]}


def verify_compound(name: str) -> dict:
    r = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(name.strip())}/cids/JSON")
    if r is None:
        return {"name": name, "verdict": "lookup_error"}
    if r.status_code == 200 and r.json().get("IdentifierList", {}).get("CID"):
        return {"name": name, "verdict": "found", "cid": r.json()["IdentifierList"]["CID"][0]}
    return {"name": name, "verdict": "not_found"}
