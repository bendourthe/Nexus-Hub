### Step 2: Python python-pptx Fundamentals

python-pptx is the most popular Python library for creating and modifying PowerPoint files. It provides full access to the OOXML presentation model including slides, layouts, placeholders, shapes, text frames, tables, charts, and images.

**Core Object Model**:

```
Presentation
  -> SlideMasters[]
       -> SlideLayouts[]
  -> Slides[]
       -> Shapes[]
            -> TextFrame -> Paragraphs[] -> Runs[]
            -> Table -> Rows[] -> Cells[]
            -> Chart -> ChartData
            -> Picture
```

**Creating a Presentation from Scratch**:

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

def create_presentation() -> Presentation:
    """Create a new presentation with standard 16:9 dimensions."""
    prs = Presentation()
    # Set slide dimensions to 16:9 (13.333 x 7.5 inches)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs
```

**Understanding Slide Layouts**:

Every presentation has a slide master that contains slide layouts. The default template provides these standard layouts:

```python
def list_available_layouts(prs: Presentation) -> list[dict]:
    """List all available slide layouts from the slide master."""
    layouts = []
    for idx, layout in enumerate(prs.slide_masters[0].slide_layouts):
        layouts.append({
            "index": idx,
            "name": layout.name,
            "placeholders": [
                {"idx": ph.placeholder_format.idx, "name": ph.name, "type": ph.placeholder_format.type}
                for ph in layout.placeholders
            ],
        })
    return layouts

# Standard layout indices (default template):
# 0 = Title Slide (title + subtitle)
# 1 = Title and Content (title + body)
# 2 = Section Header
# 3 = Two Content (title + two body columns)
# 4 = Comparison (title + two columns with subtitles)
# 5 = Title Only
# 6 = Blank
# 7 = Content with Caption
# 8 = Picture with Caption
```

**Adding Slides with Text**:

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def add_title_slide(
    prs: Presentation,
    title: str,
    subtitle: str,
) -> None:
    """Add a title slide (layout index 0) with title and subtitle."""
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)

    slide.placeholders[0].text = title
    slide.placeholders[1].text = subtitle


def add_content_slide(
    prs: Presentation,
    title: str,
    body_text: str,
    bullet_points: list[str] | None = None,
) -> None:
    """Add a title-and-content slide (layout index 1) with formatted text."""
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)

    # Set title
    slide.placeholders[0].text = title

    # Set body content
    text_frame = slide.placeholders[1].text_frame
    text_frame.clear()

    if body_text:
        paragraph = text_frame.paragraphs[0]
        paragraph.text = body_text
        paragraph.font.size = Pt(18)
        paragraph.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    if bullet_points:
        for point in bullet_points:
            paragraph = text_frame.add_paragraph()
            paragraph.text = point
            paragraph.level = 0
            paragraph.font.size = Pt(16)
            paragraph.space_after = Pt(6)
```

**Working with Text Frames and Runs**:

```python
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def add_formatted_text(
    prs: Presentation,
    title: str,
    content_blocks: list[dict],
) -> None:
    """Add a slide with rich text formatting using runs.

    Each content_block: {"text": str, "bold": bool, "size": int, "color": str}
    """
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title Only layout
    slide.placeholders[0].text = title

    # Add a text box for custom-positioned content
    from pptx.util import Inches
    left = Inches(1.0)
    top = Inches(2.0)
    width = Inches(11.0)
    height = Inches(4.5)
    text_box = slide.shapes.add_textbox(left, top, width, height)
    text_frame = text_box.text_frame
    text_frame.word_wrap = True

    for idx, block in enumerate(content_blocks):
        if idx == 0:
            paragraph = text_frame.paragraphs[0]
        else:
            paragraph = text_frame.add_paragraph()

        run = paragraph.add_run()
        run.text = block["text"]
        run.font.size = Pt(block.get("size", 14))
        run.font.bold = block.get("bold", False)
        run.font.italic = block.get("italic", False)

        color_hex = block.get("color", "333333")
        run.font.color.rgb = RGBColor.from_string(color_hex)

    # Set paragraph alignment
    for paragraph in text_frame.paragraphs:
        paragraph.alignment = PP_ALIGN.LEFT
```

**Adding Images**:

```python
from pptx.util import Inches

def add_image_slide(
    prs: Presentation,
    title: str,
    image_path: str,
    left: float = 2.0,
    top: float = 2.0,
    width: float = 9.0,
) -> None:
    """Add a slide with a positioned image.

    The height is calculated automatically to maintain aspect ratio.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title Only
    slide.placeholders[0].text = title

    slide.shapes.add_picture(
        image_path,
        left=Inches(left),
        top=Inches(top),
        width=Inches(width),
        # height omitted: auto-calculated from aspect ratio
    )
```

**Adding Tables**:

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

def add_table_slide(
    prs: Presentation,
    title: str,
    headers: list[str],
    rows: list[list[str]],
) -> None:
    """Add a slide with a formatted data table."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title Only
    slide.placeholders[0].text = title

    row_count = len(rows) + 1  # +1 for header
    col_count = len(headers)
    left = Inches(1.0)
    top = Inches(2.0)
    width = Inches(11.0)
    height = Inches(0.5 * row_count)

    table_shape = slide.shapes.add_table(
        row_count, col_count, left, top, width, height,
    )
    table = table_shape.table

    # Style header row
    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = header
        for paragraph in cell.text_frame.paragraphs:
            paragraph.font.bold = True
            paragraph.font.size = Pt(12)
            paragraph.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            paragraph.alignment = PP_ALIGN.CENTER
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0x2E, 0x4A, 0x7A)

    # Populate data rows
    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_value in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = str(cell_value)
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(11)
                paragraph.alignment = PP_ALIGN.LEFT

    # Set column widths proportionally
    total_width = Inches(11.0)
    col_width = int(total_width / col_count)
    for col_idx in range(col_count):
        table.columns[col_idx].width = col_width
```

**Saving the Presentation**:

```python
from pathlib import Path

def save_presentation(prs: Presentation, output_path: str | Path) -> Path:
    """Save presentation to disk and return the resolved path."""
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))
    return output
```
