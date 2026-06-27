#Scraping the hormuz strait live tracker 



#!/usr/bin/env python3
"""
Website crawler + scraper in one file.

What it does:
- Crawls internal pages from a start URL.
- Extracts common page values (text, headings, links, images, tables, metadata).
- Saves all collected data into a single JSON output file.

Usage:
    python website_scraper.py --url https://hormuzstraitmonitor.com/ --output website_data.json --max-pages 100
"""


#Importing packages 
#Importing for webscraping 
from __future__ import annotations 
import argparse 
import json
import re 
import time 
from collections import deque 
from datetime import datetime, timezone 
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse 
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import SSLError
from urllib3.util.retry import Retry


KPI_KEYWORDS = {
    "kpi",
    "metric",
    "metrics",
    "count",
    "counts",
    "price",
    "premium",
    "throughput",
    "transit",
    "vessel",
    "ships",
    "oil",
    "lng",
    "rate",
    "impact",
    "cost",
    "total",
    "daily",
}

STATUS_KEYWORDS = {
    "status",
    "state",
    "condition",
    "restricted",
    "open",
    "closed",
    "suspended",
    "active",
    "inactive",
    "normal",
    "critical",
}

GRAPH_KEYWORDS = {
    "chart",
    "graph",
    "plot",
    "series",
    "dataset",
    "datasets",
    "labels",
    "xaxis",
    "yaxis",
    "traces",
    "timeline",
}

NUMBER_PATTERN = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
STATUS_VALUE_PATTERN = re.compile(
    r"\b(restricted|open|closed|suspended|active|inactive|normal|critical|extreme|in progress|contested)\b",
    re.IGNORECASE,
)


def build_session() -> requests.Session:
    """Create a requests session with retries and browser-like headers."""
    session = requests.Session()

    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
    )
    return session


def normalize_text(text: str) -> str:
    """Collapse extra whitespace and trim text."""
    return re.sub(r"\s+", " ", text or "").strip()


def clean_url(url: str) -> str:
    """Remove fragments and normalize trailing slash behavior."""
    url_no_fragment, _ = urldefrag(url)
    return url_no_fragment.strip()


def is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"}


def is_same_domain(url: str, base_domain: str) -> bool:
    return urlparse(url).netloc == base_domain


def fetch_rendered_html(url: str, timeout_seconds: int) -> str | None:
    """Render a page in a real browser and return hydrated HTML after JS execution."""
    try:
        from selenium import webdriver
        from selenium.common.exceptions import TimeoutException, WebDriverException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except Exception:
        return None

    driver = None
    last_error: Exception | None = None

    def _build_drivers() -> list[Any]:
        drivers: list[Any] = []
        try:
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument("--headless=new")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1366,2000")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--no-sandbox")
            drivers.append(("edge", edge_options))
        except Exception:
            pass

        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1366,2000")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            drivers.append(("chrome", chrome_options))
        except Exception:
            pass

        return drivers

    for driver_name, options in _build_drivers():
        try:
            if driver_name == "edge":
                driver = webdriver.Edge(options=options)
            else:
                driver = webdriver.Chrome(options=options)

            driver.set_page_load_timeout(timeout_seconds)
            driver.get(url)

            wait = WebDriverWait(driver, timeout_seconds)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

            # Dismiss ad close overlays when present.
            for frame in driver.find_elements(By.TAG_NAME, "iframe"):
                try:
                    driver.switch_to.frame(frame)
                    close_buttons = driver.find_elements(
                        By.XPATH,
                        "//*[self::button or self::div or self::span][contains(translate(normalize-space(.), 'CLOSE', 'close'), 'close')]",
                    )
                    for button in close_buttons[:2]:
                        try:
                            button.click()
                        except Exception:
                            continue
                except Exception:
                    pass
                finally:
                    driver.switch_to.default_content()

            # Wait for key status widget text to appear in hydrated DOM.
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//*[contains(translate(normalize-space(.), 'RESTRICTEDCLOSEDOPEN', 'restrictedclosedopen'), 'restricted') or "
                            "contains(translate(normalize-space(.), 'RESTRICTEDCLOSEDOPEN', 'restrictedclosedopen'), 'closed') or "
                            "contains(translate(normalize-space(.), 'STRAIT STATUS', 'strait status'), 'strait status')]",
                        )
                    )
                )
            except TimeoutException:
                pass

            return driver.page_source
        except Exception as exc:
            last_error = exc
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass
            driver = None
            continue
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = None

    if last_error is not None:
        return None
    return None


def fetch_dashboard_api_data(
    start_url: str,
    session: requests.Session,
    timeout_seconds: int,
    insecure_fallback_used: bool,
) -> tuple[dict[str, Any] | None, bool]:
    """Fetch live dashboard data that the frontend uses to render status/KPIs/graphs."""
    dashboard_url = urljoin(start_url, "/api/dashboard")

    try:
        response = session.get(dashboard_url, timeout=timeout_seconds)
    except SSLError:
        if not insecure_fallback_used:
            requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
            insecure_fallback_used = True
        try:
            response = session.get(dashboard_url, timeout=timeout_seconds, verify=False)
        except requests.RequestException:
            return None, insecure_fallback_used
    except requests.RequestException:
        return None, insecure_fallback_used

    if response.status_code >= 400:
        return None, insecure_fallback_used

    try:
        payload = response.json()
        if isinstance(payload, dict):
            return payload, insecure_fallback_used
    except ValueError:
        return None, insecure_fallback_used

    return None, insecure_fallback_used


def merge_dashboard_api_into_page(page_data: dict[str, Any], dashboard_payload: dict[str, Any]) -> None:
    """Merge dashboard API fields into extracted page JSON for exact rendered values."""
    dashboard_data = dashboard_payload.get("data", dashboard_payload)
    if not isinstance(dashboard_data, dict):
        return

    page_data["dashboard_api"] = dashboard_data

    kpis: list[dict[str, Any]] = list(page_data.get("kpis", []))
    statuses: list[dict[str, Any]] = list(page_data.get("statuses", []))
    graphs = page_data.get("graphs", {})

    # Status from API reflects the rendered status badge (e.g., RESTRICTED).
    strait_status = dashboard_data.get("straitStatus")
    if isinstance(strait_status, dict):
        status_value = normalize_text(str(strait_status.get("status", "")))
        if status_value:
            statuses.append({
                "key": "straitStatus.status",
                "value": status_value,
                "source": "dashboard_api",
            })

        since_value = normalize_text(str(strait_status.get("since", "")))
        if since_value:
            statuses.append({
                "key": "straitStatus.since",
                "value": since_value,
                "source": "dashboard_api",
            })

    # Capture numeric KPI-style values from known dashboard sections.
    for section_name in [
        "shipCount",
        "oilPrice",
        "strandedVessels",
        "insurance",
        "throughput",
        "globalTradeImpact",
        "tankerRates",
    ]:
        section = dashboard_data.get(section_name)
        if not isinstance(section, dict):
            continue

        for key, value in section.items():
            if isinstance(value, (int, float)):
                kpis.append(
                    {
                        "name": f"{section_name}.{key}",
                        "value": str(value),
                        "unit": "",
                        "raw": str(value),
                        "source": "dashboard_api",
                    }
                )
            elif isinstance(value, str) and NUMBER_PATTERN.search(value):
                number, unit = parse_number_and_unit(value)
                kpis.append(
                    {
                        "name": f"{section_name}.{key}",
                        "value": number,
                        "unit": unit,
                        "raw": value,
                        "source": "dashboard_api",
                    }
                )

    embedded_objects: list[dict[str, Any]] = list(graphs.get("embedded_chart_objects", []))
    table_series: list[dict[str, Any]] = list(graphs.get("table_timeseries", []))

    # Graph series exposed by API.
    oil_price = dashboard_data.get("oilPrice", {})
    if isinstance(oil_price, dict) and isinstance(oil_price.get("sparkline"), list):
        embedded_objects.append(
            {
                "source": "dashboard_api",
                "chart": {
                    "name": "oilPrice.sparkline",
                    "labels": list(range(len(oil_price.get("sparkline", [])))),
                    "series": [oil_price.get("sparkline", [])],
                },
            }
        )

    throughput = dashboard_data.get("throughput", {})
    if isinstance(throughput, dict) and isinstance(throughput.get("last7Days"), list):
        embedded_objects.append(
            {
                "source": "dashboard_api",
                "chart": {
                    "name": "throughput.last7Days",
                    "labels": list(range(len(throughput.get("last7Days", [])))),
                    "series": [throughput.get("last7Days", [])],
                },
            }
        )

    timeline = dashboard_data.get("crisisTimeline", {})
    if isinstance(timeline, dict) and isinstance(timeline.get("events"), list):
        table_series.append(
            {
                "source": "dashboard_api",
                "x": "event_index",
                "series": ["events"],
                "rows": [[str(i), normalize_text(str(event.get("title", "")))] for i, event in enumerate(timeline.get("events", []), start=1)],
            }
        )

    # De-duplicate merged statuses and kpis.
    dedup_statuses: list[dict[str, Any]] = []
    seen_statuses: set[tuple[str, str]] = set()
    for item in statuses:
        sig = (normalize_text(str(item.get("key", ""))).lower(), normalize_text(str(item.get("value", ""))).lower())
        if sig not in seen_statuses:
            seen_statuses.add(sig)
            dedup_statuses.append(item)

    dedup_kpis: list[dict[str, Any]] = []
    seen_kpis: set[tuple[str, str]] = set()
    for item in kpis:
        sig = (normalize_text(str(item.get("name", ""))).lower(), normalize_text(str(item.get("raw", item.get("value", "")))).lower())
        if sig not in seen_kpis:
            seen_kpis.add(sig)
            dedup_kpis.append(item)

    page_data["statuses"] = dedup_statuses
    page_data["kpis"] = dedup_kpis
    page_data["graphs"] = {
        "dom_containers": graphs.get("dom_containers", []),
        "embedded_chart_objects": embedded_objects,
        "table_timeseries": table_series,
    }


def extract_tables(soup: BeautifulSoup) -> list[dict[str, Any]]:
    tables_data: list[dict[str, Any]] = []

    for table in soup.find_all("table"):
        headers = [normalize_text(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr"):
            cells = [normalize_text(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]
            if any(cells):
                rows.append(cells)
        if headers or rows:
            tables_data.append({"headers": headers, "rows": rows})

    return tables_data


def has_any_keyword(text: str, keywords: set[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def normalize_key_name(key: str) -> str:
    return normalize_text(key).strip(":").lower().replace(" ", "_")


def parse_number_and_unit(value: str) -> tuple[str, str]:
    """Extract numeric token and unit/currency/percent from a string value."""
    value = normalize_text(value)
    number_match = NUMBER_PATTERN.search(value)
    if not number_match:
        return value, ""

    number = number_match.group(0)
    unit_part = normalize_text(value.replace(number, "", 1))
    return number, unit_part


def split_label_value(text: str) -> tuple[str, str] | None:
    text = normalize_text(text)
    if not text:
        return None

    if ":" in text:
        left, right = text.split(":", 1)
        left = normalize_text(left)
        right = normalize_text(right)
        if left and right:
            return left, right

    # Generic fallback for lines like "War Risk Premium 1.2%"
    if NUMBER_PATTERN.search(text):
        parts = text.rsplit(" ", 1)
        if len(parts) == 2 and parts[0] and parts[1]:
            return normalize_text(parts[0]), normalize_text(parts[1])

    return None


def extract_balanced_json_candidates(text: str, max_candidates: int = 40) -> list[str]:
    """Find balanced JSON-like objects/arrays in script text without fixed layout assumptions."""
    candidates: list[str] = []
    in_string = False
    escape = False
    quote_char = ""
    stack: list[str] = []
    start_idx = -1

    for idx, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote_char:
                in_string = False
            continue

        if ch in {"\"", "'"}:
            in_string = True
            quote_char = ch
            continue

        if ch in "[{":
            if not stack:
                start_idx = idx
            stack.append(ch)
            continue

        if ch in "]}":
            if not stack:
                continue

            opener = stack[-1]
            if (opener == "[" and ch == "]") or (opener == "{" and ch == "}"):
                stack.pop()
                if not stack and start_idx >= 0:
                    candidate = text[start_idx : idx + 1].strip()
                    if 2 <= len(candidate) <= 250000:
                        candidates.append(candidate)
                        if len(candidates) >= max_candidates:
                            break
            else:
                stack.clear()
                start_idx = -1

    return candidates


def extract_embedded_json(soup: BeautifulSoup) -> list[dict[str, Any]]:
    extracted: list[dict[str, Any]] = []

    for script in soup.find_all("script"):
        script_type = (script.get("type") or "").strip().lower()
        script_text = (script.string or script.get_text() or "").strip()
        if not script_text:
            continue

        if script_type in {"application/ld+json", "application/json"}:
            try:
                extracted.append({"source": script_type, "data": json.loads(script_text)})
            except json.JSONDecodeError:
                extracted.append({"source": script_type, "data": script_text[:2000]})
            continue

        candidates = extract_balanced_json_candidates(script_text)
        parsed_count = 0
        for candidate in candidates:
            try:
                data = json.loads(candidate)
                extracted.append({"source": "script-json-candidate", "data": data})
                parsed_count += 1
            except json.JSONDecodeError:
                continue

            if parsed_count >= 10:
                break

    return extracted


def extract_status_from_dom(soup: BeautifulSoup) -> list[dict[str, str]]:
    statuses: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for el in soup.find_all(True):
        attrs_text = " ".join(
            [
                str(el.get("id", "")),
                " ".join(el.get("class", [])) if isinstance(el.get("class", []), list) else str(el.get("class", "")),
            ]
        )
        text = normalize_text(el.get_text(" ", strip=True))
        if not text or len(text) > 160:
            continue

        pair = split_label_value(text)
        if pair and (has_any_keyword(pair[0], STATUS_KEYWORDS) or has_any_keyword(attrs_text, STATUS_KEYWORDS)):
            item = {"key": pair[0], "value": pair[1], "source": "dom"}
            signature = (item["key"].lower(), item["value"].lower())
            if signature not in seen:
                seen.add(signature)
                statuses.append(item)

        if has_any_keyword(text, {"currently", "restricted", "open", "closed", "suspended", "active", "inactive"}) and has_any_keyword(
            attrs_text + " " + text, STATUS_KEYWORDS
        ):
            item = {"key": "status", "value": text, "source": "dom"}
            signature = (item["key"].lower(), item["value"].lower())
            if signature not in seen:
                seen.add(signature)
                statuses.append(item)

        # Layout-agnostic status block detection: label and value often appear as separate sibling text nodes.
        if len(text) <= 140:
            short_texts = [normalize_text(s) for s in el.stripped_strings if normalize_text(s)]
            short_texts = [s for s in short_texts if len(s) <= 80][:6]
            if len(short_texts) >= 2:
                label = ""
                value = ""
                for s in short_texts:
                    if not label and has_any_keyword(s, STATUS_KEYWORDS):
                        label = s
                    if not value and STATUS_VALUE_PATTERN.search(s):
                        value = s

                if label and value:
                    item = {"key": label, "value": value, "source": "dom_group"}
                    signature = (item["key"].lower(), item["value"].lower())
                    if signature not in seen:
                        seen.add(signature)
                        statuses.append(item)

        for attr_name in ["data-status", "aria-label", "title"]:
            attr_val = normalize_text(str(el.get(attr_name, "")))
            if attr_val and has_any_keyword(attr_val, STATUS_KEYWORDS):
                item = {"key": attr_name, "value": attr_val, "source": "attribute"}
                signature = (item["key"].lower(), item["value"].lower())
                if signature not in seen:
                    seen.add(signature)
                    statuses.append(item)

    return statuses


def extract_kpis_from_dom(soup: BeautifulSoup) -> list[dict[str, str]]:
    kpis: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for el in soup.find_all(True):
        attrs_text = " ".join(
            [
                str(el.get("id", "")),
                " ".join(el.get("class", [])) if isinstance(el.get("class", []), list) else str(el.get("class", "")),
                str(el.get("data-testid", "")),
            ]
        )
        text = normalize_text(el.get_text(" ", strip=True))
        if not text or len(text) > 180:
            continue

        if not NUMBER_PATTERN.search(text):
            continue

        pair = split_label_value(text)
        if pair and (has_any_keyword(pair[0], KPI_KEYWORDS) or has_any_keyword(attrs_text, KPI_KEYWORDS) or has_any_keyword(text, KPI_KEYWORDS)):
            number, unit = parse_number_and_unit(pair[1])
            item = {
                "name": pair[0],
                "value": number,
                "unit": unit,
                "raw": pair[1],
                "source": "dom",
            }
            signature = (item["name"].lower(), item["raw"].lower())
            if signature not in seen:
                seen.add(signature)
                kpis.append(item)

    return kpis


def walk_json_values(node: Any, path: str = "") -> list[tuple[str, Any]]:
    pairs: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            next_path = f"{path}.{key}" if path else str(key)
            pairs.extend(walk_json_values(value, next_path))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            next_path = f"{path}[{idx}]"
            pairs.extend(walk_json_values(value, next_path))
    else:
        pairs.append((path, node))
    return pairs


def is_chart_like_json(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    keys = {str(k).lower() for k in node.keys()}
    return bool(keys.intersection(GRAPH_KEYWORDS)) or (
        ("data" in keys or "series" in keys) and ("labels" in keys or "xaxis" in keys or "yaxis" in keys)
    )


def find_chart_objects(node: Any, max_items: int = 30) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def _walk(obj: Any) -> None:
        if len(found) >= max_items:
            return
        if isinstance(obj, dict):
            if is_chart_like_json(obj):
                found.append(obj)
            for value in obj.values():
                _walk(value)
        elif isinstance(obj, list):
            for value in obj:
                _walk(value)

    _walk(node)
    return found


def extract_structured_from_embedded_json(embedded_json: list[dict[str, Any]]) -> dict[str, Any]:
    kpis: list[dict[str, str]] = []
    statuses: list[dict[str, str]] = []
    graph_data: list[dict[str, Any]] = []
    seen_kpi: set[tuple[str, str]] = set()
    seen_status: set[tuple[str, str]] = set()

    for block in embedded_json:
        data = block.get("data")
        source = str(block.get("source", "embedded-json"))

        for chart_obj in find_chart_objects(data):
            graph_data.append({"source": source, "chart": chart_obj})

        for key_path, value in walk_json_values(data):
            key_lower = key_path.lower()
            if value is None:
                continue

            value_str = normalize_text(str(value))
            if not value_str:
                continue

            if has_any_keyword(key_lower, STATUS_KEYWORDS):
                status_item = {"key": key_path, "value": value_str, "source": source}
                signature = (status_item["key"].lower(), status_item["value"].lower())
                if signature not in seen_status:
                    seen_status.add(signature)
                    statuses.append(status_item)

            if has_any_keyword(key_lower, KPI_KEYWORDS) and (NUMBER_PATTERN.search(value_str) or isinstance(value, (int, float))):
                number, unit = parse_number_and_unit(value_str)
                kpi_item = {
                    "name": key_path,
                    "value": number,
                    "unit": unit,
                    "raw": value_str,
                    "source": source,
                }
                signature = (kpi_item["name"].lower(), kpi_item["raw"].lower())
                if signature not in seen_kpi:
                    seen_kpi.add(signature)
                    kpis.append(kpi_item)

    return {
        "kpis": kpis,
        "statuses": statuses,
        "graph_data": graph_data,
    }


def extract_graph_containers(soup: BeautifulSoup) -> list[dict[str, Any]]:
    containers: list[dict[str, Any]] = []
    for el in soup.find_all(["canvas", "svg", "figure", "section", "div"]):
        attrs_text = " ".join(
            [
                str(el.get("id", "")),
                " ".join(el.get("class", [])) if isinstance(el.get("class", []), list) else str(el.get("class", "")),
                str(el.get("role", "")),
            ]
        )
        if not has_any_keyword(attrs_text, GRAPH_KEYWORDS):
            continue

        data_attributes = {
            key: normalize_text(str(value))
            for key, value in el.attrs.items()
            if str(key).startswith("data-") and normalize_text(str(value))
        }
        containers.append(
            {
                "tag": el.name,
                "id": normalize_text(str(el.get("id", ""))),
                "class": " ".join(el.get("class", [])) if isinstance(el.get("class", []), list) else normalize_text(str(el.get("class", ""))),
                "text": normalize_text(el.get_text(" ", strip=True))[:300],
                "data_attributes": data_attributes,
            }
        )
    return containers


def extract_timeseries_from_tables(tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    series_list: list[dict[str, Any]] = []

    for table in tables:
        rows = table.get("rows", [])
        headers = table.get("headers", [])
        if not rows:
            continue

        if headers and len(headers) >= 2:
            first_header = headers[0].lower()
            if any(token in first_header for token in ["date", "time", "day", "month", "year"]):
                series_list.append(
                    {
                        "source": "table",
                        "x": headers[0],
                        "series": headers[1:],
                        "rows": rows,
                    }
                )

    return series_list


def extract_page_data(url: str, html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else ""

    meta = []
    for tag in soup.find_all("meta"):
        item = {
            "name": tag.get("name") or tag.get("property") or "",
            "content": tag.get("content") or "",
        }
        if item["name"] or item["content"]:
            meta.append(item)

    headings = {
        f"h{i}": [normalize_text(h.get_text(" ", strip=True)) for h in soup.find_all(f"h{i}") if normalize_text(h.get_text(" ", strip=True))]
        for i in range(1, 7)
    }

    paragraphs = [
        normalize_text(p.get_text(" ", strip=True))
        for p in soup.find_all("p")
        if normalize_text(p.get_text(" ", strip=True))
    ]

    list_items = [
        normalize_text(li.get_text(" ", strip=True))
        for li in soup.find_all("li")
        if normalize_text(li.get_text(" ", strip=True))
    ]

    links = []
    for a in soup.find_all("a", href=True):
        href = clean_url(urljoin(url, a["href"]))
        links.append(
            {
                "text": normalize_text(a.get_text(" ", strip=True)),
                "href": href,
            }
        )

    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            images.append(
                {
                    "src": clean_url(urljoin(url, src)),
                    "alt": normalize_text(img.get("alt", "")),
                }
            )

    json_ld = []
    for script in soup.find_all("script", type="application/ld+json"):
        content = script.string or script.get_text()
        content = (content or "").strip()
        if content:
            try:
                json_ld.append(json.loads(content))
            except json.JSONDecodeError:
                json_ld.append(content)

    tables = extract_tables(soup)
    embedded_json = extract_embedded_json(soup)
    embedded_structured = extract_structured_from_embedded_json(embedded_json)
    dom_statuses = extract_status_from_dom(soup)
    dom_kpis = extract_kpis_from_dom(soup)
    graph_containers = extract_graph_containers(soup)
    table_series = extract_timeseries_from_tables(tables)

    # Merge and de-duplicate KPI/status entries from DOM + embedded JSON.
    merged_kpis: list[dict[str, str]] = []
    seen_kpis: set[tuple[str, str]] = set()
    for item in dom_kpis + embedded_structured["kpis"]:
        sig = (normalize_text(item.get("name", "")).lower(), normalize_text(item.get("raw", item.get("value", ""))).lower())
        if sig not in seen_kpis:
            seen_kpis.add(sig)
            merged_kpis.append(item)

    merged_statuses: list[dict[str, str]] = []
    seen_statuses: set[tuple[str, str]] = set()
    for item in dom_statuses + embedded_structured["statuses"]:
        sig = (normalize_text(item.get("key", "")).lower(), normalize_text(item.get("value", "")).lower())
        if sig not in seen_statuses:
            seen_statuses.add(sig)
            merged_statuses.append(item)

    page_text = normalize_text(soup.get_text(" ", strip=True))

    return {
        "url": url,
        "title": title,
        "meta": meta,
        "headings": headings,
        "paragraphs": paragraphs,
        "list_items": list_items,
        "tables": tables,
        "links": links,
        "images": images,
        "json_ld": json_ld,
        "kpis": merged_kpis,
        "statuses": merged_statuses,
        "graphs": {
            "dom_containers": graph_containers,
            "embedded_chart_objects": embedded_structured["graph_data"],
            "table_timeseries": table_series,
        },
        "embedded_json": embedded_json,
        "full_text": page_text,
    }


def crawl_website(
    start_url: str,
    max_pages: int,
    delay_seconds: float,
    timeout_seconds: int,
    render_js: bool,
) -> dict[str, Any]:
    start_url = clean_url(start_url)
    if not is_http_url(start_url):
        raise ValueError("Start URL must begin with http:// or https://")

    base_domain = urlparse(start_url).netloc
    session = build_session()
    insecure_fallback_used = False

    visited: set[str] = set()
    queue: deque[str] = deque([start_url])
    pages: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    all_kpis: list[dict[str, Any]] = []
    all_statuses: list[dict[str, Any]] = []
    all_graphs: list[dict[str, Any]] = []
    rendered_pages_count = 0
    dashboard_api_payload, insecure_fallback_used = fetch_dashboard_api_data(
        start_url=start_url,
        session=session,
        timeout_seconds=timeout_seconds,
        insecure_fallback_used=insecure_fallback_used,
    )

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()

        if current_url in visited:
            continue
        if not is_http_url(current_url):
            continue
        if not is_same_domain(current_url, base_domain):
            continue

        try:
            try:
                response = session.get(current_url, timeout=timeout_seconds)
            except SSLError:
                # Some sites use cert chains that fail verification on local machines.
                if not insecure_fallback_used:
                    requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
                    insecure_fallback_used = True
                response = session.get(current_url, timeout=timeout_seconds, verify=False)
            status_code = response.status_code
            content_type = response.headers.get("Content-Type", "")

            if status_code >= 400:
                errors.append({"url": current_url, "error": f"HTTP {status_code}"})
                visited.add(current_url)
                continue

            if "text/html" not in content_type.lower():
                visited.add(current_url)
                continue

            html = response.text
            rendered_html = None
            if render_js:
                rendered_html = fetch_rendered_html(current_url, timeout_seconds)

            if rendered_html:
                html = rendered_html
                rendered_pages_count += 1

            page_data = extract_page_data(current_url, html)
            if current_url == start_url and dashboard_api_payload:
                merge_dashboard_api_into_page(page_data, dashboard_api_payload)
            page_data["rendered_html_used"] = bool(rendered_html)
            pages.append(page_data)
            for item in page_data.get("kpis", []):
                all_kpis.append({"url": current_url, **item})
            for item in page_data.get("statuses", []):
                all_statuses.append({"url": current_url, **item})
            graphs = page_data.get("graphs", {})
            all_graphs.append(
                {
                    "url": current_url,
                    "dom_containers": graphs.get("dom_containers", []),
                    "embedded_chart_objects": graphs.get("embedded_chart_objects", []),
                    "table_timeseries": graphs.get("table_timeseries", []),
                }
            )
            visited.add(current_url)

            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                next_url = clean_url(urljoin(current_url, a["href"]))
                if (
                    next_url
                    and next_url not in visited
                    and is_http_url(next_url)
                    and is_same_domain(next_url, base_domain)
                ):
                    queue.append(next_url)

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        except requests.RequestException as exc:
            errors.append({"url": current_url, "error": str(exc)})
            visited.add(current_url)

    return {
        "start_url": start_url,
        "domain": base_domain,
        "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
        "ssl_insecure_fallback_used": insecure_fallback_used,
        "render_js": render_js,
        "rendered_pages_count": rendered_pages_count,
        "dashboard_api_used": bool(dashboard_api_payload),
        "dashboard_api_timestamp": dashboard_api_payload.get("timestamp") if isinstance(dashboard_api_payload, dict) else None,
        "max_pages": max_pages,
        "visited_count": len(visited),
        "scraped_pages_count": len(pages),
        "errors_count": len(errors),
        "all_kpis": all_kpis,
        "all_statuses": all_statuses,
        "all_graphs": all_graphs,
        "pages": pages,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl a website and save extracted values to JSON.")
    parser.add_argument(
        "--url",
        default="https://hormuzstraitmonitor.com/",
        help="Starting URL, default: https://hormuzstraitmonitor.com/",
    )
    parser.add_argument("--output", default="website_data.json", help="Output JSON file path")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum internal pages to crawl")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay (seconds) between page requests")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout (seconds)")
    parser.add_argument("--render-js", action="store_true", help="Render pages in browser before extraction")
    parser.add_argument("--no-render-js", action="store_true", help="Disable browser rendering and use raw HTML only")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_js = False
    if args.no_render_js:
        render_js = False
    elif args.render_js:
        render_js = True

    result = crawl_website(
        start_url=args.url,
        max_pages=args.max_pages,
        delay_seconds=args.delay,
        timeout_seconds=args.timeout,
        render_js=render_js,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Saved {result['scraped_pages_count']} pages to {args.output}")
    if result["errors_count"]:
        print(f"Encountered {result['errors_count']} errors (see output file).")


if __name__ == "__main__":
    main()