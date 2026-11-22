"""Render the last 26 weeks of the public GitHub profile calendar."""

import argparse
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


COLORS = ("#16181A", "#244248", "#386973", "#539DA8", "#A9EAF1")
ROOT = Path(__file__).resolve().parents[2]


class ContributionCalendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.levels = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag != "td" or "ContributionCalendar-day" not in classes:
            return
        day = date.fromisoformat(attributes["data-date"])
        level = int(attributes["data-level"])
        if not 0 <= level < len(COLORS) or day in self.levels:
            raise ValueError(f"Unexpected contribution cell for {day}")
        self.levels[day] = level


def render(levels):
    last_day = max(levels)
    last_sunday = last_day - timedelta(days=(last_day.weekday() + 1) % 7)
    first_sunday = last_sunday - timedelta(weeks=25)
    day_count = (last_day - first_sunday).days + 1
    days = [first_sunday + timedelta(days=offset) for offset in range(day_count)]
    if any(day not in levels for day in days):
        raise ValueError("GitHub returned an incomplete contribution calendar")

    cells = []
    for offset, day in enumerate(days):
        week, weekday = divmod(offset, 7)
        level = levels[day]
        style = f' class="active" style="animation-delay:{week * 0.055:.3f}s"' if level else ""
        cells.append(
            f'  <rect x="{52 + week * 29}" y="{54 + weekday * 23}" width="27" '
            f'height="21" rx="3" fill="{COLORS[level]}"{style}/>'
        )

    range_label = f"{first_sunday:%b %d, %Y} – {last_day:%b %d, %Y}"
    legend = [
        f'  <rect x="{656 + index * 17}" y="230" width="13" height="13" rx="2" fill="{color}"/>'
        for index, color in enumerate(COLORS)
    ]
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 856 264" width="856" height="264">',
        '  <title>GitHub contribution calendar</title>',
        f'  <desc>Activity from {range_label}. Brighter squares indicate higher activity.</desc>',
        '  <style>',
        '    @media (prefers-reduced-motion: no-preference) {',
        '      .active { animation: sweep 1.35s ease-out 1; }',
        '    }',
        '    @keyframes sweep { 0% { opacity: 1; } 38% { opacity: .55; } 100% { opacity: 1; } }',
        '  </style>',
        '  <rect width="856" height="264" rx="12" fill="#000"/>',
        '  <rect x=".5" y=".5" width="855" height="263" rx="11.5" fill="none" stroke="#27272A"/>',
        '  <g font-family="system-ui, Segoe UI, Arial, sans-serif" font-size="23" fill="#A1A1AA">',
        f'    <text x="52" y="36">{range_label}</text>',
        '    <text x="642" y="242" text-anchor="end">Less</text>',
        '    <text x="804" y="242" text-anchor="end">More</text>',
        '  </g>',
        *cells,
        *legend,
        '</svg>',
        '',
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username", nargs="?", default="samhoon000")
    args = parser.parse_args()

    request = Request(
        f"https://github.com/users/{args.username}/contributions",
        headers={"User-Agent": "GitHub-Profile-Calendar"},
    )
    calendar = ContributionCalendar()
    with urlopen(request, timeout=30) as response:
        calendar.feed(response.read().decode("utf-8"))
    if not calendar.levels:
        raise ValueError("GitHub returned no contribution cells")

    svg = render(calendar.levels)
    target = ROOT / ".github/assets/profile/contributions.svg"
    target.write_text(svg, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
