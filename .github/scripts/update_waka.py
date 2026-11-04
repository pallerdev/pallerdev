"""Reescribe la sección waka del README con los JSON públicos de WakaTime.

Las API keys de WakaTime ya no sirven para /stats, pero las URLs de
"share" son públicas y no necesitan credenciales.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

BAR_WIDTH = 25
NAME_WIDTH = 14
TOP_LANGUAGES = 6

START = "<!--START_SECTION:waka-->"
END = "<!--END_SECTION:waka-->"


def fetch(url):
    # Sin User-Agent propio, Cloudflare puede rechazar el de urllib.
    request = urllib.request.Request(url, headers={"User-Agent": "waka-readme-updater"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)["data"]


def bar(percent):
    filled = round(percent / 100 * BAR_WIDTH)
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def rows(items):
    return "\n".join(
        f"{item['name']:<{NAME_WIDTH}}{bar(item['percent'])}  {item['percent']:5.2f} %"
        for item in items
    )


def render(languages, categories):
    # "Other" agrupa lenguajes sueltos y no aporta nada en un perfil.
    top_languages = [l for l in languages if l["name"] != "Other"][:TOP_LANGUAGES]
    # Por debajo de 1 % la barra sale vacía y solo añade ruido.
    used_categories = [c for c in categories if c["percent"] >= 1]
    updated = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    return (
        "```text\n"
        "💬 Languages\n"
        f"{rows(top_languages)}\n"
        "\n"
        "🤖 How I code\n"
        f"{rows(used_categories)}\n"
        "```\n"
        "\n"
        f"<sub>Updated daily from WakaTime · last run {updated}</sub>"
    )


def main():
    readme_path = sys.argv[1] if len(sys.argv) > 1 else "README.md"

    languages = fetch(os.environ["WAKA_LANGUAGES_URL"])
    categories = fetch(os.environ["WAKA_CATEGORIES_URL"])

    with open(readme_path, encoding="utf-8") as file:
        readme = file.read()

    pattern = re.compile(f"{re.escape(START)}.*?{re.escape(END)}", re.DOTALL)
    if not pattern.search(readme):
        sys.exit(f"Markers {START} / {END} not found in {readme_path}")

    section = f"{START}\n{render(languages, categories)}\n{END}"
    readme = pattern.sub(lambda _: section, readme)

    with open(readme_path, "w", encoding="utf-8") as file:
        file.write(readme)


if __name__ == "__main__":
    main()
