import httpx
from pathlib import Path

SCHEMA_URL = "https://app.playerdata.co.uk/api/schema.graphql"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "schema.graphql"


def main():
    response = httpx.get(SCHEMA_URL)
    response.raise_for_status()
    OUTPUT_PATH.write_text(response.text)
    print(f"Schema written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
