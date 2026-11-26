"""Render ready-to-use city/network comparisons from the exact bundled snapshot."""
from html import escape
from pathlib import Path
import json
import re

from search_metadata import add_search_metadata

EXAMPLES = (
    ("halifax-eastlink", "NS", "Halifax", "11260", "Eastlink"),
    ("langley-telus", "BC", "Langley", "852", "TELUS"),
    ("vancouver-telus", "BC", "Vancouver", "852", "TELUS"),
    ("vancouver-novus", "BC", "Vancouver", "40029", "Novus"),
)


def build_examples(stage, page, tool):
    status = json.loads((stage / "data/status.json").read_text())
    month = status["end"]
    directions = ("download", "upload")
    months = {m["month"]: m for m in status["months"]}
    rows = {
        direction: {(r[0], r[1], str(r[2])): r for r in json.loads((stage / f"data/{month}-{direction}.json").read_text())}
        for direction in directions
    }
    median = 5 + status["percentiles"].index(50)
    for slug, region, city, asn, provider in EXAMPLES:
        heading = f"{provider} internet speeds in {city}"
        description = f"Compare a download result with published M-Lab tests on {provider} AS{asn} in {city}, {region}."
        summaries = []
        for direction in directions:
            row = rows[direction].get((region, city, asn))
            source = escape(months[month]["sources"][direction]["url"], quote=True)
            value = (f'{row[median]:,.2f} Mbps median across {row[4]:,} {direction} tests.'
                     if row else f'No qualifying {direction} group was published.')
            summaries.append(f'<li><strong>{direction.capitalize()}</strong> · {value} '
                             f'<a href="{source}">M-Lab {direction} data (Parquet)</a></li>')
        snapshot = (f'<p>Published M-Lab tests on {provider} (AS{asn}) in {city}, {region}, '
                    f'<time datetime="{month}">{month}</time>.</p><ul class="cohort-facts">{"".join(summaries)}</ul>')
        guide = {"Halifax":"halifax-home-internet", "Vancouver":"vancouver-home-internet"}.get(city)
        if guide:
            snapshot += f'<p><a href="/field-notes/{guide}/">Compare home internet in {city}</a></p>'
        variant = re.sub(r"<title>.*?</title>", f"<title>{heading} · CoolCode</title>", page)
        variant = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{description}">', variant)
        variant = re.sub(r"<h1>.*?</h1>", f"<h1>{heading}</h1>", variant)
        variant = variant.replace('<p>Where does your speed sit among tests on the same network, in the same city?</p>', snapshot)
        variant = variant.replace('<body ', f'<body data-region="{region}" data-city="{city}" data-asn="{asn}" ')
        variant = variant.replace('href="./', 'href="../').replace('src="./', 'src="../')
        target = stage / slug
        target.mkdir()
        (target/"index.html").write_text(add_search_metadata(variant, {
            **tool, "url":tool["url"]+slug+"/", "description":description, "title":heading}))
