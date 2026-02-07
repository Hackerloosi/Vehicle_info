import requests
from bs4 import BeautifulSoup, SoupStrainer
import time
import random

HOME_URL = "https://parivahan.gov.in/rcdlstatus/"
POST_URL = "https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

def fetch_rto_details(first, second):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)

        # Step 1: home page
        r = session.get(HOME_URL, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        vs = soup.select_one('input[name="javax.faces.ViewState"]')
        if not vs:
            return None

        viewstate = vs["value"]

        # Small human-like delay
        time.sleep(random.uniform(1.5, 3.0))

        # Step 2: submit form
        data = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "form_rcdl:j_idt32",
            "javax.faces.partial.execute": "@all",
            "javax.faces.partial.render": "form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl",
            "form_rcdl:j_idt32": "form_rcdl:j_idt32",
            "form_rcdl": "form_rcdl",
            "form_rcdl:tf_reg_no1": first,
            "form_rcdl:tf_reg_no2": second,
            "javax.faces.ViewState": viewstate,
        }

        r = session.post(
            POST_URL,
            data=data,
            headers={
                **HEADERS,
                "Faces-Request": "partial/ajax",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": HOME_URL,
            },
            timeout=20,
        )

        # Step 3: extract table rows
        soup = BeautifulSoup(r.text, "html.parser")
        table_only = SoupStrainer("tr")
        soup = BeautifulSoup(
            soup.get_text(),
            "html.parser",
            parse_only=table_only,
        )

        text = soup.get_text(separator="\n").strip()
        if not text or "Registration No" not in text:
            return None

        return text

    except Exception:
        return None
