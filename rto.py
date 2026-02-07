import requests
from bs4 import BeautifulSoup, SoupStrainer

HOME_URL = "https://parivahan.gov.in/rcdlstatus/"
POST_URL = "https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml"

def fetch_rto_details(first, second):
    try:
        # Step 1: Get home page (cookies + viewstate)
        r = requests.get(
            HOME_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )
        cookies = r.cookies

        soup = BeautifulSoup(r.text, "html.parser")
        viewstate_tag = soup.select_one('input[name="javax.faces.ViewState"]')
        if not viewstate_tag:
            return None

        viewstate = viewstate_tag["value"]

        # Step 2: POST request (JSF AJAX)
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

        r = requests.post(
            POST_URL,
            data=data,
            cookies=cookies,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Faces-Request": "partial/ajax",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=20
        )

        # Step 3: Extract table rows text
        soup = BeautifulSoup(r.text, "html.parser")
        table_only = SoupStrainer("tr")
        soup = BeautifulSoup(soup.get_text(), "html.parser", parse_only=table_only)

        text = soup.get_text(separator="\n").strip()

        if not text:
            return None

        # Return RAW text (same style as your PHP / CLI)
        return text

    except Exception as e:
        return None
