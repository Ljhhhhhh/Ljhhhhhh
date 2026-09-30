"""Render the public GitHub contribution calendar using only the Python standard library."""

from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
import urllib.request


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.counts = {}
        self.tooltip = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs:
            self.days[attrs["id"]] = (date.fromisoformat(attrs["data-date"]), int(attrs["data-level"]))
        if tag == "tool-tip":
            self.tooltip = attrs.get("for")
            self.text = []

    def handle_data(self, data):
        if self.tooltip:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tooltip:
            label = "".join(self.text)
            match = re.match(r"\s*([\d,]+|No) contributions? on ", label)
            if not match:
                raise ValueError(f"Unexpected contribution label: {label}")
            self.counts[self.tooltip] = 0 if match[1] == "No" else int(match[1].replace(",", ""))
            self.tooltip = None


request = urllib.request.Request("https://github.com/users/Ljhhhhhh/contributions", headers={"User-Agent": "Ljhhhhhh-profile-calendar"})
with urllib.request.urlopen(request, timeout=30) as response:
    parser = CalendarParser()
    parser.feed(response.read().decode("utf-8"))

today = datetime.now(timezone(timedelta(hours=8))).date()
days = sorted((day, level, parser.counts[key]) for key, (day, level) in parser.days.items() if day <= today)
if len(days) < 350:
    raise ValueError("Incomplete contribution calendar; keeping the existing image")

start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
colors = ["#172742", "#16546a", "#168b9a", "#36c8c8", "#94f5dc"]
svg = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 290" role="img" aria-labelledby="title desc">',
    '<title id="title">开发足迹 · GitHub 公开可见贡献</title>',
    f'<desc id="desc">{days[0][0]} 至 {days[-1][0]}，共 {sum(count for _, _, count in days)} 次公开可见贡献。数据来自 GitHub 公开贡献页面。</desc>',
    '<rect width="1000" height="290" rx="12" fill="#0d1930"/>',
    '<path d="M28 29h8v8h-8z M42 29h8v8h-8z M56 29h8v8h-8z" fill="#36c8c8"/>',
    '<text x="28" y="76" fill="#fff2d4" font-family="monospace" font-size="27" font-weight="bold">BUILD LOG</text>',
    '<text x="971" y="72" text-anchor="end" fill="#94f5dc" font-family="monospace" font-size="18">WEB / DESKTOP / AI</text>',
]
months = set()
for day, level, count in days:
    week, weekday = divmod((day - start).days, 7)
    x, y = 29 + week * 17.5, 115 + weekday * 16
    month = day.strftime("%Y-%m")
    if month not in months:
        months.add(month)
        svg.append(f'<text x="{x}" y="101" fill="#8da7c6" font-family="monospace" font-size="10">{day:%b}</text>')
    height = 2 + level
    label = escape(f"{day}: {count} contributions")
    svg.append(f'<g><title>{label}</title><path d="M{x} {y+12}h12v{height}h-12z" fill="#0a1225"/><path d="M{x+12} {y}l3 3v{12+height}l-3 -3z" fill="#11203a"/><rect x="{x}" y="{y}" width="12" height="12" fill="{colors[level]}"/></g>')

svg.append(f'<text x="29" y="263" fill="#a4bad4" font-family="monospace" font-size="13">{sum(count for _, _, count in days)} PUBLICLY VISIBLE CONTRIBUTIONS / {days[0][0]} — {days[-1][0]}</text>')
for level, color in enumerate(colors):
    svg.append(f'<rect x="{863 + level * 20}" y="251" width="12" height="12" fill="{color}"/>')
svg.append('</svg>')
destination = Path(__file__).resolve().parents[1] / "assets" / "contributions.svg"
destination.write_text("\n".join(svg), encoding="utf-8")
print(f"Updated {destination.name}: {len(days)} days, {sum(count for _, _, count in days)} contributions")
