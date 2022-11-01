import math
import sys

import requests
from bs4 import BeautifulSoup
from pycpf import pycpf
from rich import print
from rich.console import Console
from rich.table import Table


def retrieve_cpf(shot):
    cpf = {}
    for field in pycpf.columns():
        name = field[0]
        entry = pycpf.query(name, f"shot = {shot}")
        if entry:
            cpf[name] = {
                "value": entry[name][0],
                "description": field[1],
            }
        else:
            cpf[name] = {
                "value": None,
                "description": field[1],
            }
    return cpf


def retrieve_website_cpf(shot):
    URL = f"https://users.mastu.ukaea.uk/internal/shot/{shot}"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    cpf_table = soup.tbody
    website_cpf_map = {
        "$P_{ohm}$ max": "pohm_max",
        "$J_{ohm}$ total": "johm_total",
        "$P_{nbi \\: ss}$ max": "pnbi_max_ss",
        "$E_{nbi \\: ss}$ max": "enbi_max_ss",
        "$J_{nbi \\: ss}$ total": "jnbi_total_ss",
        "$P_{nbi \\: sw}$ max": "pnbi_max_sw",
        "$E_{nbi \\: sw}$ max": "enbi_max_sw",
        "$J_{nbi \\: sw}$ total": "jnbi_total_sw",
        "$I_{p}$ max": "ip_max",
        "$I_{p}$ avg": "ip_av",
        "$\\kappa$ max": "kappa_max",
        "$T_e$ max": "te0_max",
        "$n_e$ max": "ne0_max",
        "$B_{\\phi}$ max": "bt_max",
        "$\\beta$ max": "betmhd_max",
        "$\\beta_{\\theta}$ max": "bepmhd_max",
        "$W_{mhd}$ max": "wmhd_max",
        "$\\tau_E$ max": "tautot_max",
    }
    website_cpf = {}

    for row in cpf_table.contents:
        if row.contents[2].string:
            split_text = row.contents[2].string.split()
            if len(split_text) == 2:
                value, units = float(split_text[0]), split_text[1]
            else:
                try:
                    value, units = float(split_text[0]), None
                except ValueError:
                    value, units = None, split_text[0]
        else:
            value, units = None, None
        website_cpf[website_cpf_map[f"{row.contents[0].string}"]] = {
            "value": value,
            "units": units,
        }
    return website_cpf


if __name__ == "__main__":
    if sys.argv[1]:
        shot = sys.argv[1]
    else:
        shot = 30420
    website_cpf = retrieve_website_cpf(shot)
    cpf = retrieve_cpf(shot)
    table = Table(title=f"{shot}")
    table.add_column("Name")
    table.add_column("pycpf")
    table.add_column("website")
    table.add_column("Equal")

    [
        table.add_row(
            key,
            str(website_cpf[key]["value"]),
            str(cpf[key]["value"]),
            str(
                math.isclose(
                    website_cpf[key]["value"], cpf[key]["value"], rel_tol=0.0001
                )
            ),
        )
        for key in website_cpf.keys()
        if website_cpf[key]["value"] and cpf[key]["value"]
    ]

    console = Console()
    console.print(table)
