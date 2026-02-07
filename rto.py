import requests
from bs4 import BeautifulSoup
import re

HOME_URL = "https://parivahan.gov.in/rcdlstatus/?pur_cd=102"
POST_URL = "https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml"

def scrape_out(html, find):
    lines = html.split("\n")
    for i, line in enumerate(lines):
        if find in line and i + 1 < len(lines):
            return re.sub("<.*?>", "", lines[i + 1]).strip()
    return ""

def fetch_rto_details(reg1, reg2):
    session = requests.Session()

    r = session.get(HOME_URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    viewstate = soup.find("input", {"name": "javax.faces.ViewState"})
    if not viewstate:
        return None
    viewstate = viewstate["value"]

    buttons = soup.find_all("button")
    if len(buttons) < 2:
        return None
    button_id = buttons[1]["id"]

    headers = {
        "Faces-Request": "partial/ajax",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://parivahan.gov.in",
        "Referer": HOME_URL,
        "User-Agent": "Mozilla/5.0",
    }

    payload = {
        "javax.faces.partial.ajax": "true",
        "javax.faces.source": button_id,
        "javax.faces.partial.execute": "@all",
        "javax.faces.partial.render": "form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl",
        button_id: button_id,
        "form_rcdl": "form_rcdl",
        "form_rcdl:tf_reg_no1": reg1,
        "form_rcdl:tf_reg_no2": reg2,
        "javax.faces.ViewState": viewstate,
    }

    r2 = session.post(POST_URL, headers=headers, data=payload)
    html = r2.text

    return {
        "vehicle_registration_info": {
            "regno": scrape_out(html, "Registration No:"),
            "reg_date": scrape_out(html, "Registration Date:"),
            "chassis": scrape_out(html, "Chassis No:"),
            "engineno": scrape_out(html, "Engine No:"),
            "ownername": scrape_out(html, "Owner Name:"),
            "vehicleclass": scrape_out(html, "Vehicle Class:"),
            "fueltype": scrape_out(html, "Fuel Type:"),
            "fitnessupto": scrape_out(html, "Fitness Upto:"),
            "insuranceupto": scrape_out(html, "Insurance Upto:"),
            "fuelnorms": scrape_out(html, "Fuel Norms:"),
            "roadtaxpaidupto": scrape_out(html, "Road Tax Paid Upto:"),
        }
    }