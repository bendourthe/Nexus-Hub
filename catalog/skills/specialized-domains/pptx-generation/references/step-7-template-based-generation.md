### Step 7: Template-Based Generation

Template-based generation loads an existing .pptx file (designed in PowerPoint or Google Slides) and populates it with dynamic data. This approach separates design from code and is ideal for branded report generation.

**Loading and Inspecting a Template** (python-pptx):

```python
from pptx import Presentation
from pptx.util import Inches


def inspect_template(template_path: str) -> dict:
    """Inspect a template to discover its layouts and placeholders.

    Run this first when working with a new template to understand
    which placeholder indices and names are available.
    """
    prs = Presentation(template_path)
    template_info = {
        "slide_width": str(prs.slide_width),
        "slide_height": str(prs.slide_height),
        "slide_count": len(prs.slides),
        "layouts": [],
    }

    for layout_idx, layout in enumerate(prs.slide_layouts):
        layout_info = {
            "index": layout_idx,
            "name": layout.name,
            "placeholders": [],
        }
        for ph in layout.placeholders:
            layout_info["placeholders"].append({
                "idx": ph.placeholder_format.idx,
                "name": ph.name,
                "type": str(ph.placeholder_format.type),
                "left": str(ph.left),
                "top": str(ph.top),
                "width": str(ph.width),
                "height": str(ph.height),
            })
        template_info["layouts"].append(layout_info)

    return template_info


def load_template(template_path: str) -> Presentation:
    """Load an existing .pptx template for population."""
    return Presentation(template_path)
```

**Populating Template Placeholders**:

```python
from pptx import Presentation
from pptx.util import Pt


def populate_template_slide(
    prs: Presentation,
    layout_index: int,
    placeholder_data: dict[int, str],
) -> None:
    """Add a new slide from a template layout and fill its placeholders.

    Args:
        prs: Presentation loaded from template.
        layout_index: Index of the slide layout to use.
        placeholder_data: Mapping of placeholder index to text content.
    """
    layout = prs.slide_layouts[layout_index]
    slide = prs.slides.add_slide(layout)

    for ph_idx, text in placeholder_data.items():
        if ph_idx in [ph.placeholder_format.idx for ph in slide.placeholders]:
            slide.placeholders[ph_idx].text = text


def populate_with_formatting(
    prs: Presentation,
    layout_index: int,
    placeholder_content: dict[int, list[dict]],
) -> None:
    """Populate placeholders with formatted text runs.

    Each entry in placeholder_content maps a placeholder index to a list of
    run descriptors: {"text": str, "bold": bool, "size": int, "color": str}.
    """
    layout = prs.slide_layouts[layout_index]
    slide = prs.slides.add_slide(layout)

    for ph_idx, runs in placeholder_content.items():
        if ph_idx not in [ph.placeholder_format.idx for ph in slide.placeholders]:
            continue

        text_frame = slide.placeholders[ph_idx].text_frame
        text_frame.clear()

        for run_idx, run_data in enumerate(runs):
            if run_idx == 0:
                paragraph = text_frame.paragraphs[0]
            else:
                paragraph = text_frame.add_paragraph()

            run = paragraph.add_run()
            run.text = run_data["text"]
            run.font.size = Pt(run_data.get("size", 14))
            run.font.bold = run_data.get("bold", False)
            if "color" in run_data:
                from pptx.dml.color import RGBColor
                run.font.color.rgb = RGBColor.from_string(run_data["color"])
```

**Batch Generation from Data (Mail Merge Pattern)**:

```python
from pathlib import Path
from pptx import Presentation
import json


def batch_generate_decks(
    template_path: str,
    data_records: list[dict],
    output_dir: str,
    filename_field: str = "name",
) -> list[Path]:
    """Generate one presentation per data record using a shared template.

    This implements a mail merge pattern where each record produces
    a complete deck with its own data.

    Args:
        template_path: Path to the .pptx template.
        data_records: List of dicts, each containing fields for one deck.
        output_dir: Directory to write generated files.
        filename_field: Key in each record to use for the output filename.

    Returns:
        List of paths to generated files.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []

    for record in data_records:
        prs = Presentation(template_path)

        # Remove template example slides (keep only layouts)
        while len(prs.slides) > 0:
            rId = prs.slides._sldIdLst[0].get("r:id")
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[0]

        # Build slides from record data
        _build_deck_from_record(prs, record)

        # Save with sanitized filename
        safe_name = "".join(
            c if c.isalnum() or c in "-_ " else "" for c in record.get(filename_field, "output")
        ).strip()
        file_path = output / f"{safe_name}.pptx"
        prs.save(str(file_path))
        generated_files.append(file_path)

    return generated_files


def _build_deck_from_record(prs: Presentation, record: dict) -> None:
    """Build slides for a single record. Customize per template structure."""
    # Title slide (layout 0)
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.placeholders[0].text = record.get("title", "Untitled")
    slide.placeholders[1].text = record.get("subtitle", "")

    # Content slides (layout 1)
    for section in record.get("sections", []):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.placeholders[0].text = section.get("heading", "")
        slide.placeholders[1].text = section.get("body", "")
```

**Data-Driven Generation from JSON**:

```python
from pathlib import Path
from pptx import Presentation
import json


def generate_from_json(
    json_path: str,
    template_path: str | None = None,
    output_path: str = "output.pptx",
) -> Path:
    """Generate a presentation from a JSON specification.

    JSON schema:
    {
      "metadata": {"title": str, "author": str},
      "theme": {"primary_color": str, "font": str},
      "slides": [
        {
          "type": "title|content|two_column|chart|table|image",
          "title": str,
          "content": {...type-specific fields...}
        }
      ]
    }
    """
    with open(json_path) as f:
        spec = json.load(f)

    prs = Presentation(template_path) if template_path else Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    for slide_spec in spec.get("slides", []):
        slide_type = slide_spec.get("type", "content")

        if slide_type == "title":
            add_title_slide(
                prs,
                slide_spec.get("title", ""),
                slide_spec.get("content", {}).get("subtitle", ""),
            )
        elif slide_type == "content":
            add_content_slide(
                prs,
                slide_spec.get("title", ""),
                slide_spec.get("content", {}).get("body", ""),
                slide_spec.get("content", {}).get("bullets", []),
            )
        elif slide_type == "two_column":
            content = slide_spec.get("content", {})
            add_two_column_slide(
                prs,
                slide_spec.get("title", ""),
                content.get("left_title", ""),
                content.get("left_points", []),
                content.get("right_title", ""),
                content.get("right_points", []),
            )
        elif slide_type == "chart":
            content = slide_spec.get("content", {})
            chart_type = content.get("chart_type", "bar")
            if chart_type == "bar":
                add_bar_chart_slide(
                    prs,
                    slide_spec.get("title", ""),
                    content.get("categories", []),
                    content.get("series", {}),
                )
            elif chart_type == "pie":
                add_pie_chart_slide(
                    prs,
                    slide_spec.get("title", ""),
                    content.get("categories", []),
                    content.get("values", []),
                )
        elif slide_type == "table":
            content = slide_spec.get("content", {})
            add_table_slide(
                prs,
                slide_spec.get("title", ""),
                content.get("headers", []),
                content.get("rows", []),
            )

    output = Path(output_path)
    prs.save(str(output))
    return output
```

**Example JSON Specification**:

```json
{
  "metadata": {
    "title": "Q4 Performance Report",
    "author": "Analytics Team"
  },
  "slides": [
    {
      "type": "title",
      "title": "Q4 2025 Performance Report",
      "content": { "subtitle": "Analytics Team | January 2026" }
    },
    {
      "type": "content",
      "title": "Executive Summary",
      "content": {
        "bullets": [
          "Revenue grew 23% year-over-year to $4.2M",
          "Customer acquisition cost decreased by 15%",
          "Net promoter score improved from 42 to 58",
          "Three new enterprise clients onboarded"
        ]
      }
    },
    {
      "type": "chart",
      "title": "Revenue by Quarter",
      "content": {
        "chart_type": "bar",
        "categories": ["Q1", "Q2", "Q3", "Q4"],
        "series": {
          "2024": [2800000, 3100000, 3400000, 3600000],
          "2025": [3200000, 3500000, 3900000, 4200000]
        }
      }
    },
    {
      "type": "table",
      "title": "Regional Performance",
      "content": {
        "headers": ["Region", "Revenue", "Growth", "Clients"],
        "rows": [
          ["North America", "$2.1M", "+18%", "45"],
          ["Europe", "$1.2M", "+28%", "32"],
          ["Asia Pacific", "$0.9M", "+35%", "21"]
        ]
      }
    }
  ]
}
```
