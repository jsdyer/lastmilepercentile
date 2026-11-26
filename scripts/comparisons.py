"""Render ready-to-use city/network comparisons from the exact bundled snapshot."""
from html import escape
from pathlib import Path
import json
import re

from search_metadata import add_search_metadata

EXAMPLES = (
    ("halifax-eastlink", "NS", "Halifax", "11260", "Eastlink"),
    ("langley-telus", "BC", "Langley", "852", "TELUS"),
)


def build_examples(stage, page, tool):
    status = json.loads((stage / "data/status.json").read_text())
    month = status["end"]
    rows = json.loads((stage / f"data/{month}-download.json").read_text())
    median = 5 + status["percentiles"].index(50)
    for slug, region, city, asn, provider in EXAMPLES:
        heading = f"{provider} internet speeds in {city}"
        description = f"Compare a download result with published M-Lab tests on {provider} AS{asn} in {city}, {region}."
        row = next((r for r in rows if r[0] == region and r[1] == city and str(r[2]) == asn), None)
        snapshot = (f"In {month}, the median download result was {row[median]:,.2f} Mbps across {row[4]:,} tests."
                    if row else f"No qualifying download group was published for {month}. Choose an earlier month.")
        variant = re.sub(r"<title>.*?</title>", f"<title>{heading} · CoolCode</title>", page)
        variant = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{description}">', variant)
        variant = re.sub(r"<h1>.*?</h1>", f"<h1>{heading}</h1>", variant)
        variant = variant.replace('Where does your speed sit among tests on the same network, in the same city?', snapshot)
        variant = variant.replace('<body ', f'<body data-region="{region}" data-city="{city}" data-asn="{asn}" ')
        variant = variant.replace('href="./', 'href="../').replace('src="./', 'src="../')
        target = stage / slug
        target.mkdir()
        (target/"index.html").write_text(add_search_metadata(variant, {
            **tool, "url":tool["url"]+slug+"/", "description":description, "title":heading}))
