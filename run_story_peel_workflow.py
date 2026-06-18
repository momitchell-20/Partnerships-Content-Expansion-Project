from __future__ import annotations

import argparse
import csv
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI


ROOT = Path(__file__).resolve().parent
DEFAULT_PROMPT_FILE = ROOT / "msn_story_peel_analysis_workflow.md"
DEFAULT_OUTPUT_DIR = ROOT / "output"
DEFAULT_REPORT_PREFIX = "msn_story_peel_analysis_report"
DEFAULT_SOURCE_SHEET_ID = "1fW9Yod5NcnsXon7QZQ-xRmm7cxRxFfhjHypWRljGLso"
DEFAULT_GOOGLE_SERVICE_ACCOUNT_FILE = "/Users/mmitchell/Downloads/partnerships-peeler-17739c16da8e.json"
DEFAULT_DRIVE_FOLDER_ID = "0AEgLRqknvvgcUk9PVA"
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"
OUTPUT_COLUMN_WIDTHS = [100, 96, 109, 625, 113, 184, 240, 292, 193, 265, 194, 271]
OUTPUT_WRAP_COLUMNS = [3, 5, 6, 7, 8, 9, 10, 11]
OUTPUT_HIGHLIGHT_COLUMNS = [6, 8, 10]
OUTPUT_HIGHLIGHT_COLOR = {"red": 0.91, "green": 0.96, "blue": 1.0}
DEFAULT_OUTPUT_TAB_NAME = datetime.now().strftime("%m-%d-%Y")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

HEADER_ALIASES = {
    "title": ("title", "headline", "hed"),
    "url": ("url", "guid", "link", "story_url", "article_url"),
    "description": ("description", "dek", "summary", "standfirst"),
    "body": ("body", "article_body", "full_text", "text", "content"),
    "article": ("article", "story", "story_text", "full_story", "article_text", "fullarticle", "full body"),
    "categories": ("category", "categories", "section", "sections", "tags"),
    "weekly_pvs": ("weekly pvs", "weekly_pv", "msn weekly pvs", "week pvs", "pageviews", "page views"),
    "authors": ("authors", "author", "byline", "writer"),
    "team": ("lydia team", "lydia team?", "team", "section"),
}

ERROR_TOKENS = {
    "#N/A",
    "#REF!",
    "#VALUE!",
    "#ERROR!",
    "#DIV/0!",
    "#NAME?",
    "#NUM!",
}

ERROR_TOKENS_LOWER = {token.lower() for token in ERROR_TOKENS}


@dataclass
class StoryRow:
    title: str
    url: str
    description: str
    body: str
    categories: str
    weekly_pvs: str = ""
    authors: str = ""
    source_team: str = ""
    team: str = ""


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value in {"replace_me", "replace_with_your_new_zapier_webhook_url"}:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path)


def parse_sheet_id(ref: str) -> str:
    value = ref.strip()
    if "/spreadsheets/d/" in value:
        value = value.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
    return value


def clean_inline(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\r", " ")).strip()


def clean_source_cell(text: str) -> str:
    cleaned = clean_inline(text)
    return "" if cleaned in ERROR_TOKENS else cleaned


def is_error_cell(text: str) -> bool:
    return clean_inline(text).lower() in ERROR_TOKENS_LOWER


def clean_body(text: str) -> str:
    body = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    lines = [line.rstrip() for line in body.split("\n")]
    return "\n".join(lines).strip()


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def choose_column(headers: Sequence[str], aliases: Iterable[str]) -> int | None:
    normalized_headers = [normalize_header(header) for header in headers]
    for alias in aliases:
        target = normalize_header(alias)
        if target in normalized_headers:
            return normalized_headers.index(target)
    return None


def load_service_account_credentials(creds_path: Path):
    if not creds_path.exists():
        raise RuntimeError(f"Google service account file not found: {creds_path}")
    return service_account.Credentials.from_service_account_file(
        str(creds_path),
        scopes=GOOGLE_SCOPES,
    )


def build_google_services(creds_path: Path):
    credentials = load_service_account_credentials(creds_path)
    sheets_service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    drive_service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    docs_service = build("docs", "v1", credentials=credentials, cache_discovery=False)
    return sheets_service, drive_service, docs_service


def build_openai_client() -> OpenAI:
    timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "180"))
    return OpenAI(api_key=require_env("OPENAI_API_KEY"), timeout=timeout_seconds)


def load_prompt_template(prompt_file: Path) -> str:
    if not prompt_file.exists():
        raise RuntimeError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8").strip()


def fetch_sheet_values(sheets_service, sheet_id: str, tab_name: str) -> list[list[str]]:
    range_name = f"'{tab_name}'!A:ZZ"
    response = (
        sheets_service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=range_name, majorDimension="ROWS")
        .execute()
    )
    return response.get("values", [])


def fetch_sheet_values_with_fallback(sheets_service, sheet_id: str, tab_name: str) -> list[list[str]]:
    try:
        return fetch_sheet_values(sheets_service, sheet_id, tab_name)
    except HttpError as exc:
        fallback_name = tab_name.rstrip("?")
        if fallback_name != tab_name:
            try:
                print(f"Tab '{tab_name}' failed, retrying with '{fallback_name}'.")
                return fetch_sheet_values(sheets_service, sheet_id, fallback_name)
            except HttpError:
                pass
        raise exc


def parse_pageviews(value: str) -> float:
    cleaned = clean_inline(value).replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def normalize_team_group(value: str) -> str:
    lowered = clean_inline(value).lower()
    if "partnership" in lowered:
        return "Partnerships Stories"
    if "non-partnership" in lowered or lowered.startswith("non") or lowered == "0":
        return "Non-partnerships Stories"
    return ""


def is_partnership_story(story: StoryRow | dict[str, str]) -> bool:
    team_value = ""
    if isinstance(story, StoryRow):
        team_value = story.team or story.source_team
    else:
        team_value = clean_inline(story.get("team", "")) or clean_inline(story.get("source_team", ""))
    normalized = normalize_team_group(team_value)
    return normalized == "Partnerships Stories"


def normalize_row(row: list[str], headers: Sequence[str]) -> StoryRow | None:
    title_idx = choose_column(headers, HEADER_ALIASES["title"])
    url_idx = choose_column(headers, HEADER_ALIASES["url"])
    description_idx = choose_column(headers, HEADER_ALIASES["description"])
    body_idx = choose_column(headers, HEADER_ALIASES["body"])
    article_idx = choose_column(headers, HEADER_ALIASES["article"])
    categories_idx = choose_column(headers, HEADER_ALIASES["categories"])
    weekly_pvs_idx = choose_column(headers, HEADER_ALIASES["weekly_pvs"])
    authors_idx = choose_column(headers, HEADER_ALIASES["authors"])
    if title_idx is None or url_idx is None:
        return None

    def get(idx: int | None) -> str:
        if idx is None or idx >= len(row):
            return ""
        return clean_source_cell(row[idx])

    title = get(title_idx)
    url = get(url_idx)
    description = get(description_idx)
    categories = get(categories_idx)
    weekly_pvs = get(weekly_pvs_idx) or (clean_source_cell(row[2]) if len(row) > 2 else "")
    authors = get(authors_idx) or (clean_source_cell(row[3]) if len(row) > 3 else "")
    team_raw = clean_source_cell(row[4]) if len(row) > 4 else ""
    team = normalize_team_group(team_raw or get(choose_column(headers, HEADER_ALIASES["team"])))

    body_parts: list[str] = []
    if article_idx is not None and article_idx < len(row):
        article_cell = row[article_idx]
        article_text = "" if is_error_cell(article_cell) else clean_body(article_cell)
        if article_text:
            body_parts.append(article_text)
    if body_idx is not None and body_idx < len(row):
        body_cell = row[body_idx]
        body_text = "" if is_error_cell(body_cell) else clean_body(body_cell)
        if body_text and body_text not in body_parts:
            body_parts.append(body_text)

    body = "\n".join(part for part in body_parts if part).strip()

    if not url or not body:
        return None

    return StoryRow(
        title=title,
        url=url,
        description=description,
        body=body,
        categories=categories,
        weekly_pvs=weekly_pvs,
        authors=authors,
        source_team=team_raw,
        team=team,
    )


def normalize_csv_story(row: dict[str, str]) -> StoryRow | None:
    title = clean_source_cell(row.get("Headline", "") or row.get("Title", ""))
    url = clean_source_cell(row.get("URL", "") or row.get("Url", ""))
    body_cell = row.get("Body", "") or row.get("body", "")
    body = "" if is_error_cell(body_cell) else clean_body(body_cell)
    weekly_pvs = clean_source_cell(row.get("Total Week PVs", "") or row.get("Weekly PVs", "") or row.get("Audience", ""))
    authors = clean_source_cell(row.get("Authors", "") or row.get("Author", "") or row.get("Byline", "") or row.get("Writer", ""))
    team_raw = clean_source_cell(row.get("Lydia Team?", "") or row.get("Team", "") or row.get("Section", ""))
    team = normalize_team_group(team_raw) or "Non-partnerships Stories"

    if not url or not body:
        return None

    return StoryRow(
        title=title,
        url=url,
        description="",
        body=body,
        categories="",
        weekly_pvs=weekly_pvs,
        authors=authors,
        source_team=team_raw,
        team=team,
    )


def load_story_rows(values: list[list[str]]) -> list[StoryRow]:
    if not values:
        return []

    headers = values[0]
    stories: list[StoryRow] = []
    for row in values[1:]:
        story = normalize_row(row, headers)
        if story:
            stories.append(story)
    return stories


def load_csv_story_rows(csv_path: Path, limit: int | None = None) -> list[StoryRow]:
    if not csv_path.exists():
        raise RuntimeError(f"CSV file not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    stories = []
    for row in rows:
        story = normalize_csv_story(row)
        if story:
            stories.append(story)
    stories.sort(key=lambda story: parse_pageviews(story.weekly_pvs), reverse=True)
    if limit is not None:
        return stories[:limit]
    return stories


def log_sheet_preview(values: list[list[str]]) -> None:
    if not values:
        print("Source sheet is empty.")
        return
    headers = values[0]
    print("Source headers:")
    print(", ".join(headers))
    print(f"Total raw rows including header: {len(values)}")


def build_story_prompt(template: str, story: StoryRow) -> str:
    story_lines = [
        f"Title: {story.title}",
        f"URL: {story.url}",
    ]
    if story.weekly_pvs:
        story_lines.append(f"Weekly PVs: {story.weekly_pvs}")
    if story.authors:
        story_lines.append(f"Authors: {story.authors}")
    story_lines.extend(
        [
            f"Description: {story.description or '[none]'}",
            f"Categories: {story.categories or '[none]'}",
            "Full article body:",
            story.body,
        ]
    )
    story_block = "\n".join(story_lines)
    return (
        template
        + "\n\n"
        + "Only analyze the story below.\n"
        + "Return the report in the exact output format in the prompt.\n\n"
        + story_block
    )


def make_hyperlink_formula(url: str, label: str) -> str:
    safe_url = (url or "").replace('"', '""')
    safe_label = (label or "").replace('"', '""')
    return f'=HYPERLINK("{safe_url}","{safe_label}")'


def extract_peel_options(report: str) -> list[dict[str, str]]:
    lines = report.splitlines()
    option_starts: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^\s*Peel Option #([1-3])(?:\s*[—-].*)?\s*$", line)
        if match:
            option_starts.append((match.group(1), index))

    results: list[dict[str, str]] = []
    for position, (number, start_index) in enumerate(option_starts):
        end_index = option_starts[position + 1][1] if position + 1 < len(option_starts) else len(lines)
        section = [line.rstrip() for line in lines[start_index + 1 : end_index]]

        headline = ""
        detail = ""
        section_index = 0
        while section_index < len(section) and not section[section_index].strip():
            section_index += 1
        if section_index < len(section) and section[section_index].strip() == "**Suggested new headline:**":
            section_index += 1
        elif section_index < len(section) and section[section_index].strip() == "Suggested new headline:":
            section_index += 1

        headline_lines: list[str] = []
        while section_index < len(section):
            stripped = section[section_index].strip()
            if stripped == "Spinnable detail:":
                section_index += 1
                break
            if stripped:
                headline_lines.append(section[section_index])
            section_index += 1
        headline = clean_inline(" ".join(headline_lines))

        detail_lines = [line for line in section[section_index:] if line.strip()]
        detail = clean_body("\n".join(detail_lines))

        results.append({"number": number, "headline": headline, "detail": detail})

    return results


def build_output_sheet_values(stories: Sequence[StoryRow], reports: Sequence[str]) -> list[list[str]]:
    header = [
        "Assigned",
        "Published",
        "Team",
        "Original Story",
        "MSN Weekly PVs",
        "Author(s)",
        "Peel #1 Hed",
        "Spinnable Detail",
        "Peel #2 Hed",
        "Spinnable Detail",
        "Peel #3 Hed",
        "Spinnable Detail",
    ]
    rows: list[list[str]] = [header]
    ordered_pairs = order_story_reports(stories, reports)
    for story, report in ordered_pairs:
        options = {option["number"]: option for option in extract_peel_options(report)}
        if not options:
            continue
        rows.append(
            [
                "",
                "",
                story.source_team or story.team,
                make_hyperlink_formula(story.url, story.title),
                story.weekly_pvs,
                story.authors,
                options.get("1", {}).get("headline", ""),
                options.get("1", {}).get("detail", ""),
                options.get("2", {}).get("headline", ""),
                options.get("2", {}).get("detail", ""),
                options.get("3", {}).get("headline", ""),
                options.get("3", {}).get("detail", ""),
            ]
        )
    if len(rows) <= 2:
        return rows

    def visible_sort_key(row: list[str]) -> tuple[int, float, str]:
        team_value = clean_inline(row[2]).lower()
        partnership_rank = 0 if team_value.startswith("partnership") and not team_value.startswith("non-partnership") else 1
        return (partnership_rank, -parse_pageviews(row[4]), clean_inline(row[3]).lower())

    data_rows = rows[1:]
    data_rows.sort(key=visible_sort_key)
    return [header, *data_rows]


def order_story_reports(stories: Sequence[StoryRow], reports: Sequence[str]) -> list[tuple[StoryRow, str]]:
    pairs = list(zip(stories, reports))
    partnerships = [item for item in pairs if is_partnership_story(item[0])]
    non_partnerships = [item for item in pairs if not is_partnership_story(item[0])]
    partnerships.sort(key=lambda item: (-parse_pageviews(item[0].weekly_pvs), item[0].title.lower()))
    non_partnerships.sort(key=lambda item: (-parse_pageviews(item[0].weekly_pvs), item[0].title.lower()))
    return partnerships + non_partnerships


def ensure_output_sheet(
    sheets_service,
    spreadsheet_id: str,
    tab_name: str,
    values: list[list[str]],
) -> None:
    sheet_meta = (
        sheets_service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties")
        .execute()
    )
    existing = {
        str(sheet.get("properties", {}).get("title")): int(sheet.get("properties", {}).get("sheetId"))
        for sheet in sheet_meta.get("sheets", [])
        if sheet.get("properties", {}).get("title") is not None
    }
    if tab_name in existing:
        tab_id = existing[tab_name]
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"'{tab_name}'",
            body={},
        ).execute()
    else:
        response = (
            sheets_service.spreadsheets()
            .batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [
                        {
                            "addSheet": {
                                "properties": {
                                    "title": tab_name,
                                    "gridProperties": {
                                        "rowCount": max(len(values) + 20, 100),
                                        "columnCount": max(len(values[0]) if values else 1, 11),
                                    },
                                }
                            }
                        }
                    ]
                },
            )
            .execute()
        )
        tab_id = int(response["replies"][0]["addSheet"]["properties"]["sheetId"])

    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{tab_name}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                *[
                    {
                        "updateDimensionProperties": {
                            "range": {
                                "sheetId": tab_id,
                                "dimension": "COLUMNS",
                                "startIndex": column_index,
                                "endIndex": column_index + 1,
                            },
                            "properties": {"pixelSize": pixel_size},
                            "fields": "pixelSize",
                        }
                    }
                    for column_index, pixel_size in enumerate(OUTPUT_COLUMN_WIDTHS)
                ],
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": tab_id,
                            "gridProperties": {
                                "frozenRowCount": 1,
                                "rowCount": max(len(values) + 20, 100),
                                "columnCount": max(len(values[0]) if values else 1, 11),
                            },
                        },
                        "fields": "gridProperties.frozenRowCount,gridProperties.rowCount,gridProperties.columnCount",
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                },
                *[
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": tab_id,
                                "startColumnIndex": column_index,
                                "endColumnIndex": column_index + 1,
                                "startRowIndex": 0,
                                "endRowIndex": max(len(values) + 20, 100),
                            },
                            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                            "fields": "userEnteredFormat.wrapStrategy",
                        }
                    }
                    for column_index in OUTPUT_WRAP_COLUMNS
                ],
                *[
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": tab_id,
                                "startColumnIndex": column_index,
                                "endColumnIndex": column_index + 1,
                                "startRowIndex": 0,
                                "endRowIndex": max(len(values) + 20, 100),
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": OUTPUT_HIGHLIGHT_COLOR,
                                }
                            },
                            "fields": "userEnteredFormat.backgroundColor",
                        }
                    }
                    for column_index in OUTPUT_HIGHLIGHT_COLUMNS
                ],
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": tab_id,
                            "startRowIndex": 1,
                            "endRowIndex": max(len(values) + 20, 100),
                            "startColumnIndex": 0,
                            "endColumnIndex": 2,
                        },
                        "rule": {
                            "condition": {"type": "BOOLEAN"},
                            "showCustomUi": True,
                            "strict": False,
                        },
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": tab_id,
                            "startRowIndex": 1,
                            "endRowIndex": max(len(values) + 20, 100),
                            "startColumnIndex": 4,
                            "endColumnIndex": 5,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"},
                            }
                        },
                        "fields": "userEnteredFormat.horizontalAlignment,userEnteredFormat.numberFormat",
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": tab_id,
                            "startRowIndex": 1,
                            "endRowIndex": max(len(values) + 20, 100),
                            "startColumnIndex": 0,
                            "endColumnIndex": 2,
                        },
                        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                        "fields": "userEnteredFormat.horizontalAlignment",
                    }
                },
            ]
        },
    ).execute()


def normalize_story_report(report: str) -> str:
    lines = []
    for raw_line in report.strip().splitlines():
        stripped = raw_line.strip()
        peel_match = re.match(r"^Peel Option #([1-3])(?:\s*[—-].*)?$", stripped)
        if peel_match:
            lines.append(f"Peel Option #{peel_match.group(1)}")
            continue
        if stripped == "Suggested new headline:":
            lines.append("**Suggested new headline:**")
            continue
        if stripped in {
            "Original story question:",
            "New story question:",
            "Why these questions are materially different:",
            "Why this could support a separate story:",
            "Duplication risk:",
            "Final Recommendation:",
            "Reason:",
            "Keep",
            "Reject",
        }:
            continue
        if stripped in {"[ ]", "OR"}:
            continue
        lines.append(raw_line.rstrip())
    normalized = "\n".join(lines).strip()
    normalized_lines = normalized.splitlines()
    for index, line in enumerate(normalized_lines):
        if line.strip().startswith("Peel Option #1"):
            return "\n".join(normalized_lines[index:]).strip()
    return normalized


def normalize_output(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def analyze_story(client: OpenAI, model: str, prompt_template: str, story: StoryRow) -> str:
    prompt = build_story_prompt(prompt_template, story)
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return normalize_story_report(normalize_output(response.output_text))


def final_recommendation(report: str) -> str:
    match = re.search(r"Final Recommendation:\s*(Keep|Reject)", report, flags=re.IGNORECASE)
    if match:
        return match.group(1).title()
    return "Reject"


def count_recommendations(reports: Sequence[str]) -> tuple[int, int]:
    kept = sum(1 for report in reports if final_recommendation(report) == "Keep")
    rejected = sum(1 for report in reports if final_recommendation(report) == "Reject")
    return kept, rejected


def format_story_heading(story: StoryRow, rank: int) -> str:
    weekly_pvs = story.weekly_pvs or "[none]"
    authors = story.authors or "[none]"
    return f"## <u>Title: {rank}. {story.title}</u>\nWeekly PVs: **{weekly_pvs}** | Author: {authors}"


def render_story_block(story: StoryRow, report: str, rank: int) -> str:
    header = format_story_heading(story, rank)
    return f"{header}\nURL: {story.url}\n\n{report}"


def render_section(title: str, blocks: Sequence[str]) -> str:
    heading = f"**__{title}__**"
    return "\n\n".join([heading, *blocks])


def render_report(stories: Sequence[StoryRow], reports: Sequence[str]) -> str:
    pairs = order_story_reports(stories, reports)
    if any(story.team for story in stories):
        sections: list[str] = []
        for section_name in ("Partnerships Stories", "Non-partnerships Stories"):
            section_pairs = [
                (story, report)
                for story, report in pairs
                if (story.team or "Non-partnerships Stories") == section_name
            ]
            if not section_pairs:
                continue
            blocks = [
                render_story_block(story, report, rank)
                for rank, (story, report) in enumerate(section_pairs, start=1)
            ]
            sections.append(render_section(section_name, blocks))
        body = "\n\n".join(sections)
    else:
        body = "\n\n".join(
            render_story_block(story, report, rank)
            for rank, (story, report) in enumerate(pairs, start=1)
        )
    summary = f"Total stories reviewed: {len(stories)}"
    return body + "\n\n" + summary + "\n"


def make_output_path(output_dir: Path, prefix: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    date_stamp = datetime.now().strftime("%Y-%m-%d")
    return output_dir / f"{date_stamp}_{prefix}.txt"


def create_google_doc(drive_service, docs_service, folder_id: str, title: str, content: str) -> dict:
    doc_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## <u>") and stripped.endswith("</u>"):
            doc_lines.append(stripped[6:-4])
            continue
        if stripped.startswith("## "):
            doc_lines.append(stripped[3:])
            continue
        doc_lines.append(
            line.replace("**__", "")
            .replace("__**", "")
            .replace("**", "")
            .replace("<u>", "")
            .replace("</u>", "")
        )
    doc_text = "\n".join(doc_lines)
    metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [folder_id],
    }
    created = (
        drive_service.files()
        .create(
            body=metadata,
            fields="id, name, webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )
    document_id = created["id"]
    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": doc_text,
                    }
                }
            ]
        },
    ).execute()
    style_requests = []
    for heading in ("Partnerships Stories", "Non-partnerships Stories"):
        for match in re.finditer(rf"(?m)^{re.escape(heading)}$", doc_text):
            start = match.start() + 1
            end = match.end() + 1
            style_requests.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start, "endIndex": end},
                        "textStyle": {"bold": True, "underline": True},
                        "fields": "bold,underline",
                    }
                }
            )

    for match in re.finditer(r"(?m)^Title: \d+\..*$", doc_text):
        start = match.start() + 1
        end = match.end() + 1
        style_requests.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": {"namedStyleType": "HEADING_2"},
                    "fields": "namedStyleType",
                }
            }
        )
        style_requests.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "textStyle": {"underline": True},
                    "fields": "underline",
                }
            }
        )

    for match in re.finditer(re.escape("Suggested new headline:"), doc_text):
        start = match.start() + 1
        end = match.end() + 1
        style_requests.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            }
        )

    for match in re.finditer(r"Weekly PVs:\s*\*\*([0-9,]+(?:\.[0-9]+)?)\*\*", doc_text):
        start = match.start(1) + 1
        end = match.end(1) + 1
        style_requests.append(
            {
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            }
        )

    if style_requests:
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": style_requests},
        ).execute()
    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MSN story peel workflow with OpenAI.")
    parser.add_argument(
        "--csv",
        default=os.getenv("PEEL_SOURCE_CSV", ""),
        help="Path to a local CSV file containing stories to peel.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of CSV stories to process after sorting by pageviews.",
    )
    parser.add_argument(
        "--sheet",
        default=os.getenv("PEEL_SOURCE_SPREADSHEET_ID", DEFAULT_SOURCE_SHEET_ID),
        help="Google Sheets spreadsheet ID or full spreadsheet URL.",
    )
    parser.add_argument(
        "--tab",
        default=os.getenv("PEEL_SOURCE_TAB", "To Peel"),
        help="Google Sheets tab name containing the source stories.",
    )
    parser.add_argument(
        "--creds",
        default=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or DEFAULT_GOOGLE_SERVICE_ACCOUNT_FILE,
        help="Path to the Google service account JSON file.",
    )
    parser.add_argument(
        "--folder-id",
        default=os.getenv("PEEL_DRIVE_FOLDER_ID", DEFAULT_DRIVE_FOLDER_ID),
        help="Google Drive folder ID to receive the final report.",
    )
    parser.add_argument(
        "--output-sheet",
        default=os.getenv("PEEL_OUTPUT_SPREADSHEET_ID", os.getenv("PEEL_SOURCE_SPREADSHEET_ID", DEFAULT_SOURCE_SHEET_ID)),
        help="Google Sheets spreadsheet ID or full spreadsheet URL for the output tab.",
    )
    parser.add_argument(
        "--output-tab",
        default=os.getenv("PEEL_OUTPUT_TAB", DEFAULT_OUTPUT_TAB_NAME),
        help="Google Sheets tab name for the output spreadsheet.",
    )
    parser.add_argument(
        "--prompt-file",
        default=str(DEFAULT_PROMPT_FILE),
        help="Path to the prompt template file.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Local directory for the generated report.",
    )
    parser.add_argument(
        "--output-prefix",
        default=os.getenv("PEEL_REPORT_PREFIX", DEFAULT_REPORT_PREFIX),
        help="Filename prefix for the generated report.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        help="OpenAI model to use.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate the local report but skip the Drive upload.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.creds:
        raise RuntimeError("Missing service account credentials. Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_APPLICATION_CREDENTIALS, or pass --creds.")

    creds_path = resolve_path(args.creds)
    prompt_template = load_prompt_template(resolve_path(args.prompt_file))

    sheets_service, drive_service, docs_service = build_google_services(creds_path)
    if args.csv:
        stories = load_csv_story_rows(resolve_path(args.csv), limit=args.limit)
        if not stories:
            raise RuntimeError("No valid stories were found in the CSV file.")
        print(f"Loaded {len(stories)} stories from CSV: {resolve_path(args.csv)}")
    else:
        if not args.sheet:
            raise RuntimeError("Missing source spreadsheet ID. Set PEEL_SOURCE_SPREADSHEET_ID or pass --sheet.")
        sheet_id = parse_sheet_id(args.sheet)
        values = fetch_sheet_values_with_fallback(sheets_service, sheet_id, args.tab)
        log_sheet_preview(values)
        stories = load_story_rows(values)
        if not stories:
            raise RuntimeError(
                "No valid stories were found in the source sheet. "
                "The tab may not contain title, URL, and story text in recognizable columns."
            )

    client = build_openai_client()
    reports: list[str] = []
    for index, story in enumerate(stories, start=1):
        print(f"[{index}/{len(stories)}] Analyzing: {story.title}")
        report = analyze_story(client, args.model, prompt_template, story)
        reports.append(report)

    rendered_report = render_report(stories, reports)
    output_path = make_output_path(resolve_path(args.output_dir), args.output_prefix)
    output_path.write_text(rendered_report, encoding="utf-8")
    print(f"Wrote local preview: {output_path}")

    if not args.dry_run:
        if args.output_sheet:
            output_sheet_id = parse_sheet_id(args.output_sheet)
            output_values = build_output_sheet_values(stories, reports)
            ensure_output_sheet(sheets_service, output_sheet_id, args.output_tab, output_values)
            print(f"Wrote Google Sheet tab: {args.output_tab} in {output_sheet_id}")
        if not args.folder_id:
            raise RuntimeError("Missing Drive folder ID. Set PEEL_DRIVE_FOLDER_ID or pass --folder-id.")
        created = create_google_doc(
            drive_service,
            docs_service,
            args.folder_id,
            title=output_path.stem,
            content=rendered_report,
        )
        print(f"Created Google Doc: {created.get('webViewLink', created.get('id', 'unknown'))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
