# playwright_recorder.py
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, urljoin
import json, time

def record_session(base_url, output="session.json", max_pages=20):
    requests_log = []
    seen_requests = set()
    visited_pages = set()
    to_visit      = [base_url]
    base_domain   = urlparse(base_url).netloc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page    = context.new_page()

        def on_request(req):
            url = req.url
            if urlparse(url).netloc != base_domain:
                return
            key = f"{req.method}:{url}"
            if key in seen_requests:
                return
            seen_requests.add(key)
            requests_log.append({
                "method":   req.method,
                "url":      url,
                "path":     urlparse(url).path or "/",
                "resource": req.resource_type,
            })

        page.on("request", on_request)

        while to_visit and len(visited_pages) < max_pages:
            url = to_visit.pop(0)
            if url in visited_pages:
                continue

            try:
                print(f"[{len(visited_pages)+1}/{max_pages}] Načítavam: {url}")
                page.goto(url, timeout=15000)
                page.wait_for_load_state("networkidle", timeout=10000)
                visited_pages.add(url)

                # Automaticky zozbiera všetky linky na stránke
                links = page.eval_on_selector_all(
                    "a[href]",
                    "els => els.map(e => e.href)"
                )

                for link in links:
                    # len rovnaká doména, bez kotiev (#) a query params
                    parsed = urlparse(link)
                    if parsed.netloc != base_domain:
                        continue
                    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if clean not in visited_pages and clean not in to_visit:
                        to_visit.append(clean)

                time.sleep(0.3)

            except Exception as e:
                print(f"  [WARN] {url}: {e}")
                visited_pages.add(url)  # preskočí problematickú stránku

        browser.close()

    with open(output, "w") as f:
        json.dump(requests_log, f, indent=2, ensure_ascii=False)

    # Štatistiky
    by_type = {}
    for r in requests_log:
        t = r["resource"]
        by_type[t] = by_type.get(t, 0) + 1

    print(f"\nNavštívené stránky ({len(visited_pages)}):")
    for p in sorted(visited_pages):
        print(f"  {p}")

    print(f"\nZaznamenané requesty ({len(requests_log)} total):")
    for rtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {rtype:<20} {count}x")
    print(f"\nUložené → {output}")


if __name__ == "__main__":
    import sys
    url       = sys.argv[1] if len(sys.argv) > 1 else "https://www.vut.cz"
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    record_session(url, max_pages=max_pages)
