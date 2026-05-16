#!/usr/bin/env python3
"""
download_mplus_examples_v2.py
==============================

Download Mplus example library from statmodel.com:
  - Stage A: User's Guide Chapter 3-13 examples (structured)
  - Stage B: Web Notes archive (1 zip per note)
  - Stage C: Mplus Examples index + subpages
  - Stage D: Special Mplus Topics pages (15 pages, mostly zip resources)

Output structure:
  mplus_library/
    01_users_guide/
      chap3_regression_path/
        ex3.1/
          ex3.1.inp / .dat / .html / mcex3.1.inp
      chap5_cfa_sem/  ...
      ...
    02_web_notes/
      webnote_01/    (auto-extracted zip)
      webnote_15/
      ...
    03_examples_index/
      penn/
      baysem/
      ...
    04_special_topics/
      BSEM/
        bsem_2012/   (auto-extracted zip)
      Mediation/
      ...
    _manifest.json      (full inventory of what was downloaded)

Usage:
    # all stages (default)
    python download_mplus_examples_v2.py

    # only User's Guide (= behavior of v1)
    python download_mplus_examples_v2.py --stages users_guide

    # specific stages
    python download_mplus_examples_v2.py --stages users_guide web_notes special_topics

    # adjust politeness / workers
    python download_mplus_examples_v2.py --delay 0.8 --workers 4

Dependencies: requests, beautifulsoup4
Install:  pip install requests beautifulsoup4

Tested with Python 3.9+.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import logging
import os
import re
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, unquote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write(
        "\nMissing dependencies. Install them first:\n"
        "    pip install requests beautifulsoup4\n\n"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE = "https://www.statmodel.com"
TIMEOUT = 30
RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds (exponential)
DEFAULT_DELAY = 0.5  # politeness delay between requests on the same worker

# ---------- Stage A: User's Guide ----------
UG_CHAPTERS: dict[int, str] = {
    3: "regression_path",
    4: "efa",
    5: "cfa_sem",
    6: "growth_survival",
    7: "mixture_crosssectional",
    8: "mixture_longitudinal",
    9: "multilevel",
    10: "multilevel_mixture",
    11: "missing_bayesian",
    12: "montecarlo",
    13: "special_features",
}

# ---------- Stage B: Web Notes index ----------
WEB_NOTES_INDEX = f"{BASE}/examples/webnote.shtml"

# ---------- Stage C: Examples index ----------
EXAMPLES_INDEX = f"{BASE}/examples/index.shtml"

# ---------- Stage D: Special Mplus Topics ----------
SPECIAL_TOPICS: dict[str, str] = {
    "BSEM": f"{BASE}/BSEM.shtml",
    "ComplexSurveyData": f"{BASE}/resrchpap.shtml",
    "DSEM_TimeSeries": f"{BASE}/TimeSeries.shtml",
    "ESEM": f"{BASE}/ESEM.shtml",
    "Genetics": f"{BASE}/geneticstopic.shtml",
    "IRT": f"{BASE}/irtanalysis.shtml",
    "MeasurementInvariance": f"{BASE}/MeasurementInvariance.shtml",
    "Mediation": f"{BASE}/Mediation.shtml",
    "MissingData": f"{BASE}/missingdata.shtml",
    "MixtureModeling": f"{BASE}/MixtureModeling.shtml",
    "MultilevelModeling": f"{BASE}/MultilevelModeling.shtml",
    "PSEM": f"{BASE}/psem.shtml",
    "RandomizedTrials": f"{BASE}/randtrials.shtml",
    "RI-CLPM": f"{BASE}/RI-CLPM.shtml",
    "RI-LTA": f"{BASE}/RI-LTA.shtml",
    "SEM": f"{BASE}/SEM.shtml",
    "SurvivalAnalysis": f"{BASE}/SurvivalAnalysis.shtml",
}

# What we consider an Mplus / data asset worth fetching as-is.
ASSET_EXTS = {".inp", ".dat", ".out", ".html", ".htm"}

# What we treat as a "bundle" to download AND auto-extract.
ARCHIVE_EXTS = {".zip"}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Asset:
    url: str
    local_path: Path
    required: bool = False


@dataclass
class StageStats:
    ok: int = 0
    cached: int = 0
    missing: int = 0
    failed: int = 0
    zips_extracted: int = 0
    notes: list[str] = field(default_factory=list)

    def merge(self, other: "StageStats") -> None:
        self.ok += other.ok
        self.cached += other.cached
        self.missing += other.missing
        self.failed += other.failed
        self.zips_extracted += other.zips_extracted
        self.notes.extend(other.notes)


# ---------------------------------------------------------------------------
# Logging + HTTP helpers
# ---------------------------------------------------------------------------

def setup_logger(verbose: bool) -> logging.Logger:
    logger = logging.getLogger("mplus_dl_v2")
    logger.handlers.clear()
    h = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    h.setFormatter(logging.Formatter(fmt, datefmt="%H:%M:%S"))
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (compatible; MplusExampleDownloader/2.0; "
                "research/skill-development)"
            )
        }
    )
    return s


def http_get(
    session: requests.Session,
    url: str,
    logger: logging.Logger,
    delay: float,
    retries: int = RETRIES,
) -> requests.Response | None:
    """GET with retries, exponential backoff, and 429-aware politeness."""
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            time.sleep(delay)
            r = session.get(url, timeout=TIMEOUT)
            if r.status_code == 429:
                # Slow down hard.
                wait = 30 * attempt
                logger.warning(f"429 rate-limited on {url}; sleeping {wait}s")
                time.sleep(wait)
                continue
            return r
        except requests.RequestException as e:
            last_err = e
            sleep_s = RETRY_BACKOFF ** attempt
            logger.debug(
                f"Attempt {attempt}/{retries} failed for {url}: {e}; retry in {sleep_s:.1f}s"
            )
            time.sleep(sleep_s)
    logger.error(f"Giving up on GET {url}: {last_err}")
    return None


def fetch_asset(
    session: requests.Session,
    asset: Asset,
    logger: logging.Logger,
    delay: float,
) -> str:
    """Fetch one file. Returns 'ok' | 'cached' | 'missing' | 'failed'."""
    if asset.local_path.exists() and asset.local_path.stat().st_size > 0:
        return "cached"

    asset.local_path.parent.mkdir(parents=True, exist_ok=True)
    r = http_get(session, asset.url, logger, delay)
    if r is None:
        return "failed"
    if r.status_code == 404:
        if asset.required:
            logger.warning(f"404 (required): {asset.url}")
            return "failed"
        logger.debug(f"404 (optional): {asset.url}")
        return "missing"
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        logger.warning(f"HTTP error on {asset.url}: {e}")
        return "failed"
    asset.local_path.write_bytes(r.content)
    return "ok"


def safe_filename_from_url(url: str) -> str:
    name = unquote(os.path.basename(urlparse(url).path))
    # spaces in URL like "Loop plot 3.18.pdf" come through here
    return name or "index.html"


def safe_subdir_name(s: str) -> str:
    """Make a filesystem-friendly directory name."""
    s = re.sub(r"\s+", "_", s.strip())
    s = re.sub(r"[^\w\-.]", "_", s)
    return s[:80] or "untitled"


def extract_zip(
    zip_path: Path, dest_root: Path, logger: logging.Logger
) -> bool:
    """
    Safely extract a zip alongside itself into a sibling dir named after the zip.
    Skips members that try to escape the dest dir (Zip Slip defence).
    """
    if not zip_path.exists():
        return False
    extract_dir = dest_root / zip_path.stem
    if extract_dir.exists() and any(extract_dir.iterdir()):
        return False  # already extracted
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                # Prevent Zip Slip
                member_path = (extract_dir / member.filename).resolve()
                if not str(member_path).startswith(str(extract_dir.resolve())):
                    logger.warning(f"Skipping unsafe member: {member.filename}")
                    continue
                zf.extract(member, extract_dir)
        logger.info(f"Extracted: {zip_path.name} -> {extract_dir.relative_to(dest_root.parent)}")
        return True
    except zipfile.BadZipFile:
        logger.warning(f"Not a valid zip (will keep as-is): {zip_path}")
        return False


# ---------------------------------------------------------------------------
# Stage A: User's Guide Chapter 3-13
# ---------------------------------------------------------------------------

def parse_ug_example_ids(chapter_html: str, chap_num: int) -> list[str]:
    soup = BeautifulSoup(chapter_html, "html.parser")
    pat = re.compile(rf"chap{chap_num}/ex({chap_num}\.[\w\.]+?)\.inp$")
    seen: list[str] = []
    seen_set: set[str] = set()
    for a in soup.find_all("a", href=True):
        m = pat.search(a["href"])
        if m:
            ex_id = m.group(1)
            if ex_id not in seen_set:
                seen_set.add(ex_id)
                seen.append(ex_id)
    return seen


def build_ug_assets(chap_num: int, ex_id: str, out_dir: Path) -> list[Asset]:
    base = f"{BASE}/usersguide/chap{chap_num}"
    folder = out_dir / f"ex{ex_id}"
    return [
        Asset(f"{base}/ex{ex_id}.inp", folder / f"ex{ex_id}.inp", required=True),
        Asset(f"{base}/ex{ex_id}.html", folder / f"ex{ex_id}.html", required=True),
        Asset(f"{base}/ex{ex_id}.dat", folder / f"ex{ex_id}.dat", required=False),
        Asset(f"{base}/mcex{ex_id}.inp", folder / f"mcex{ex_id}.inp", required=False),
    ]


def run_stage_users_guide(
    session: requests.Session,
    out_root: Path,
    chapters: list[int],
    workers: int,
    delay: float,
    logger: logging.Logger,
) -> StageStats:
    stats = StageStats()
    stage_dir = out_root / "01_users_guide"
    stage_dir.mkdir(parents=True, exist_ok=True)

    for chap_num in chapters:
        slug = UG_CHAPTERS.get(chap_num, f"chap{chap_num}")
        chap_dir = stage_dir / f"chap{chap_num}_{slug}"
        chap_dir.mkdir(parents=True, exist_ok=True)

        url = f"{BASE}/usersguide/chapter{chap_num}.shtml"
        r = http_get(session, url, logger, delay)
        if r is None or r.status_code != 200:
            logger.error(f"Could not fetch chapter {chap_num} index ({url})")
            stats.failed += 1
            continue
        chap_html = r.text
        (chap_dir / f"_chapter{chap_num}_index.html").write_text(
            chap_html, encoding="utf-8"
        )

        ex_ids = parse_ug_example_ids(chap_html, chap_num)
        logger.info(f"[A] Chapter {chap_num} ({slug}): {len(ex_ids)} examples")
        assets: list[Asset] = []
        for ex_id in ex_ids:
            assets.extend(build_ug_assets(chap_num, ex_id, chap_dir))

        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(fetch_asset, session, a, logger, delay) for a in assets]
            for fut in cf.as_completed(futures):
                result = fut.result()
                setattr(stats, result, getattr(stats, result) + 1)

    return stats


# ---------------------------------------------------------------------------
# Generic page harvester (used by stages B, C, D)
# ---------------------------------------------------------------------------

def collect_links(page_html: str, page_url: str) -> dict[str, list[str]]:
    """
    From a page, gather useful links by category.
    Returns dict with keys: 'assets' (.inp/.dat/.out/.html/.htm),
    'archives' (.zip), and 'subpages' (more shtml/html links on same host).
    """
    soup = BeautifulSoup(page_html, "html.parser")
    out = {"assets": [], "archives": [], "subpages": []}
    host = urlparse(page_url).netloc
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue
        full = urljoin(page_url, href)
        if urlparse(full).netloc != host:
            continue  # off-site (papers, github, etc.) — skip
        path = urlparse(full).path.lower()
        ext = os.path.splitext(path)[1]
        if ext in ASSET_EXTS:
            out["assets"].append(full)
        elif ext in ARCHIVE_EXTS:
            out["archives"].append(full)
        elif ext in {".shtml", ".html", ".htm"} and (
            "/examples/" in full or "/usersguide/" in full
        ):
            # Only follow subpages under /examples/ (Stage C recursion)
            out["subpages"].append(full)
    return out


def fetch_page_text(
    session: requests.Session, url: str, logger: logging.Logger, delay: float
) -> str | None:
    r = http_get(session, url, logger, delay)
    if r is None or r.status_code != 200:
        return None
    return r.text


def download_and_maybe_extract(
    session: requests.Session,
    url: str,
    dest_dir: Path,
    logger: logging.Logger,
    delay: float,
    stats: StageStats,
) -> None:
    """Download a single URL into dest_dir. If it's a zip, extract it too."""
    fname = safe_filename_from_url(url)
    local = dest_dir / fname
    asset = Asset(url=url, local_path=local, required=False)
    result = fetch_asset(session, asset, logger, delay)
    setattr(stats, result, getattr(stats, result) + 1)
    if result in {"ok", "cached"} and local.suffix.lower() == ".zip":
        if extract_zip(local, dest_dir, logger):
            stats.zips_extracted += 1


# ---------------------------------------------------------------------------
# Stage B: Web Notes
# ---------------------------------------------------------------------------

def run_stage_web_notes(
    session: requests.Session,
    out_root: Path,
    delay: float,
    logger: logging.Logger,
) -> StageStats:
    stats = StageStats()
    stage_dir = out_root / "02_web_notes"
    stage_dir.mkdir(parents=True, exist_ok=True)

    index_html = fetch_page_text(session, WEB_NOTES_INDEX, logger, delay)
    if index_html is None:
        stats.notes.append(f"Could not load index {WEB_NOTES_INDEX}")
        return stats
    (stage_dir / "_index.html").write_text(index_html, encoding="utf-8")
    links = collect_links(index_html, WEB_NOTES_INDEX)

    logger.info(
        f"[B] Web Notes index: {len(links['assets'])} asset links, "
        f"{len(links['archives'])} zip archives"
    )

    # Grab all .zip archives (each typically contains a complete web-note example set).
    for zip_url in links["archives"]:
        # Group zips so we don't dump everything in one folder.
        fname = safe_filename_from_url(zip_url)
        slot = stage_dir / safe_subdir_name(Path(fname).stem)
        slot.mkdir(parents=True, exist_ok=True)
        download_and_maybe_extract(session, zip_url, slot, logger, delay, stats)

    # Also grab any direct .inp/.dat/.out files listed on the index.
    for url in links["assets"]:
        fname = safe_filename_from_url(url)
        if Path(fname).suffix.lower() not in ASSET_EXTS:
            continue
        slot = stage_dir / "_direct_files"
        slot.mkdir(parents=True, exist_ok=True)
        download_and_maybe_extract(session, url, slot, logger, delay, stats)

    return stats


# ---------------------------------------------------------------------------
# Stage C: Examples index (recurse one level)
# ---------------------------------------------------------------------------

def run_stage_examples_index(
    session: requests.Session,
    out_root: Path,
    delay: float,
    logger: logging.Logger,
) -> StageStats:
    stats = StageStats()
    stage_dir = out_root / "03_examples_index"
    stage_dir.mkdir(parents=True, exist_ok=True)

    index_html = fetch_page_text(session, EXAMPLES_INDEX, logger, delay)
    if index_html is None:
        stats.notes.append(f"Could not load index {EXAMPLES_INDEX}")
        return stats
    (stage_dir / "_index.html").write_text(index_html, encoding="utf-8")

    links = collect_links(index_html, EXAMPLES_INDEX)
    logger.info(
        f"[C] Examples index: {len(links['subpages'])} subpages, "
        f"{len(links['archives'])} zips, {len(links['assets'])} direct assets"
    )

    # Direct items on the index page
    for url in links["archives"] + links["assets"]:
        slot = stage_dir / "_index_files"
        slot.mkdir(parents=True, exist_ok=True)
        download_and_maybe_extract(session, url, slot, logger, delay, stats)

    # Recurse into each /examples/ subpage one level
    visited: set[str] = {EXAMPLES_INDEX}
    for sub_url in links["subpages"]:
        if sub_url in visited:
            continue
        visited.add(sub_url)
        sub_name = Path(urlparse(sub_url).path).stem
        sub_dir = stage_dir / safe_subdir_name(sub_name)
        sub_dir.mkdir(parents=True, exist_ok=True)

        sub_html = fetch_page_text(session, sub_url, logger, delay)
        if sub_html is None:
            stats.failed += 1
            continue
        (sub_dir / "_page.html").write_text(sub_html, encoding="utf-8")

        sub_links = collect_links(sub_html, sub_url)
        for url in sub_links["archives"] + sub_links["assets"]:
            download_and_maybe_extract(session, url, sub_dir, logger, delay, stats)

    return stats


# ---------------------------------------------------------------------------
# Stage D: Special Mplus Topics
# ---------------------------------------------------------------------------

def run_stage_special_topics(
    session: requests.Session,
    out_root: Path,
    delay: float,
    logger: logging.Logger,
) -> StageStats:
    stats = StageStats()
    stage_dir = out_root / "04_special_topics"
    stage_dir.mkdir(parents=True, exist_ok=True)

    for topic, url in SPECIAL_TOPICS.items():
        topic_dir = stage_dir / safe_subdir_name(topic)
        topic_dir.mkdir(parents=True, exist_ok=True)
        page_html = fetch_page_text(session, url, logger, delay)
        if page_html is None:
            stats.failed += 1
            stats.notes.append(f"[D] Skipped {topic}: page fetch failed")
            continue
        (topic_dir / "_page.html").write_text(page_html, encoding="utf-8")

        links = collect_links(page_html, url)
        logger.info(
            f"[D] {topic}: {len(links['archives'])} zips, "
            f"{len(links['assets'])} direct assets"
        )

        for u in links["archives"] + links["assets"]:
            download_and_maybe_extract(session, u, topic_dir, logger, delay, stats)

    return stats


# ---------------------------------------------------------------------------
# Manifest + CLI
# ---------------------------------------------------------------------------

def write_manifest(out_root: Path, all_stats: dict[str, StageStats]) -> None:
    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stages": {
            name: {
                "ok": s.ok,
                "cached": s.cached,
                "missing_optional": s.missing,
                "failed": s.failed,
                "zips_extracted": s.zips_extracted,
                "notes": s.notes,
            }
            for name, s in all_stats.items()
        },
    }
    # Count all .inp files actually on disk (most useful end-state metric).
    inp_count = sum(1 for _ in out_root.rglob("*.inp"))
    manifest["total_inp_files_on_disk"] = inp_count
    (out_root / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--output", "-o", type=Path, default=Path("./mplus_library"),
        help="Output directory (default: ./mplus_library)",
    )
    p.add_argument(
        "--stages", nargs="+",
        choices=["users_guide", "web_notes", "examples_index", "special_topics", "all"],
        default=["all"],
        help="Which stages to run (default: all)",
    )
    p.add_argument(
        "--chapters", type=int, nargs="+", default=sorted(UG_CHAPTERS),
        help=f"User's Guide chapters (default: all of {sorted(UG_CHAPTERS)})",
    )
    p.add_argument("--workers", "-w", type=int, default=4, help="Parallel workers (default: 4)")
    p.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                   help=f"Politeness delay between requests on each worker, in seconds "
                        f"(default: {DEFAULT_DELAY}). Increase if you hit 429.")
    p.add_argument("--verbose", "-v", action="store_true")
    return p.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    logger = setup_logger(args.verbose)

    stages = args.stages
    if "all" in stages:
        stages = ["users_guide", "web_notes", "examples_index", "special_topics"]

    bad_chaps = [c for c in args.chapters if c not in UG_CHAPTERS]
    if bad_chaps:
        logger.error(f"Unknown chapters: {bad_chaps}. Valid: {sorted(UG_CHAPTERS)}")
        return 2

    args.output.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output root: {args.output.resolve()}")
    logger.info(f"Stages: {stages}")
    logger.info(f"Politeness delay: {args.delay}s | Workers: {args.workers}")

    session = make_session()
    all_stats: dict[str, StageStats] = {}

    if "users_guide" in stages:
        logger.info("=" * 60)
        logger.info("STAGE A: User's Guide Chapter 3-13")
        all_stats["users_guide"] = run_stage_users_guide(
            session, args.output, args.chapters, args.workers, args.delay, logger
        )

    if "web_notes" in stages:
        logger.info("=" * 60)
        logger.info("STAGE B: Web Notes")
        all_stats["web_notes"] = run_stage_web_notes(
            session, args.output, args.delay, logger
        )

    if "examples_index" in stages:
        logger.info("=" * 60)
        logger.info("STAGE C: Examples index (with one level recursion)")
        all_stats["examples_index"] = run_stage_examples_index(
            session, args.output, args.delay, logger
        )

    if "special_topics" in stages:
        logger.info("=" * 60)
        logger.info("STAGE D: Special Mplus Topics")
        all_stats["special_topics"] = run_stage_special_topics(
            session, args.output, args.delay, logger
        )

    write_manifest(args.output, all_stats)

    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    for name, s in all_stats.items():
        logger.info(
            f"  {name:20s} ok={s.ok:4d} cached={s.cached:4d} "
            f"missing={s.missing:4d} failed={s.failed:4d} "
            f"zips_extracted={s.zips_extracted:3d}"
        )
    total_inp = sum(1 for _ in args.output.rglob("*.inp"))
    logger.info(f"Total .inp files on disk: {total_inp}")
    logger.info(f"Library saved to: {args.output.resolve()}")
    logger.info(f"Manifest: {(args.output / '_manifest.json').resolve()}")

    any_fail = any(s.failed > 0 for s in all_stats.values())
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
