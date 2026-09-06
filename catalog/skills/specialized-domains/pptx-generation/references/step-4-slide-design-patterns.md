### Step 4: Slide Design Patterns

Consistent slide design requires a defined system of layout types, spacing rules, and visual hierarchy. The following patterns cover the most common slide types needed in automated presentation generation.

**Slide Type Taxonomy**:

| Slide Type | Purpose | Layout | Key Elements |
|------------|---------|--------|-------------|
| Title Slide | Opening, section start | Full background color | Title (36pt), subtitle (18pt), logo |
| Content Slide | Body information | Header bar + white body | Title (22pt), bullets/text (14pt) |
| Two-Column | Comparison, dual info | Header bar + two panels | Title, left column, right column |
| Section Divider | Topic transition | Accent background | Section title (32pt), section number |
| Data Slide | Charts and tables | Header bar + data area | Title, chart/table, source note |
| Image Slide | Visuals, screenshots | Header bar + image area | Title, image (contain fit), caption |
| Key Takeaway | Emphasis, callout | Accent background | Icon, headline (28pt), supporting text |
| Closing Slide | End, contact info | Full background color | Thank you text, contact details, logo |

**Design System Constants** (python-pptx):

```python
from dataclasses import dataclass
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt


@dataclass(frozen=True)
class DesignSystem:
    """Centralized design constants for consistent slide generation."""

    # Colors
    primary: RGBColor = RGBColor(0x2E, 0x4A, 0x7A)
    secondary: RGBColor = RGBColor(0x5B, 0x8D, 0xEF)
    accent: RGBColor = RGBColor(0xE8, 0x6C, 0x00)
    text_dark: RGBColor = RGBColor(0x33, 0x33, 0x33)
    text_light: RGBColor = RGBColor(0xFF, 0xFF, 0xFF)
    background_light: RGBColor = RGBColor(0xF5, 0xF7, 0xFA)
    border: RGBColor = RGBColor(0xDD, 0xDD, 0xDD)

    # Typography
    font_family: str = "Segoe UI"
    title_size: Pt = Pt(28)
    heading_size: Pt = Pt(22)
    body_size: Pt = Pt(14)
    caption_size: Pt = Pt(10)

    # Spacing (16:9 slide = 13.333 x 7.5 inches)
    margin_left: Inches = Inches(0.75)
    margin_top: Inches = Inches(1.0)
    content_width: Inches = Inches(11.83)
    content_height: Inches = Inches(5.75)
    header_height: Inches = Inches(0.75)
    footer_height: Inches = Inches(0.4)


DESIGN = DesignSystem()
```

**Two-Column Layout**:

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

def add_two_column_slide(
    prs: Presentation,
    title: str,
    left_title: str,
    left_points: list[str],
    right_title: str,
    right_points: list[str],
) -> None:
    """Add a two-column comparison slide with independent bullet lists."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title Only
    slide.placeholders[0].text = title

    column_width = Inches(5.5)
    left_x = Inches(0.75)
    right_x = Inches(7.0)
    top_y = Inches(1.5)
    height = Inches(5.0)

    for col_x, col_title, points in [
        (left_x, left_title, left_points),
        (right_x, right_title, right_points),
    ]:
        text_box = slide.shapes.add_textbox(col_x, top_y, column_width, height)
        tf = text_box.text_frame
        tf.word_wrap = True

        # Column header
        p = tf.paragraphs[0]
        p.text = col_title
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = DESIGN.primary
        p.space_after = Pt(12)

        # Bullet points
        for point in points:
            p = tf.add_paragraph()
            p.text = point
            p.font.size = Pt(13)
            p.font.color.rgb = DESIGN.text_dark
            p.level = 0
            p.space_after = Pt(6)
```

**Section Divider Slide**:

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

def add_section_divider(
    prs: Presentation,
    section_number: int,
    section_title: str,
) -> None:
    """Add a section divider slide with number and title on accent background."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Full-slide background
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = DESIGN.primary

    # Section number
    num_box = slide.shapes.add_textbox(
        Inches(1.0), Inches(2.0), Inches(11.0), Inches(1.5),
    )
    num_tf = num_box.text_frame
    num_tf.paragraphs[0].text = f"0{section_number}" if section_number < 10 else str(section_number)
    num_tf.paragraphs[0].font.size = Pt(60)
    num_tf.paragraphs[0].font.bold = True
    num_tf.paragraphs[0].font.color.rgb = DESIGN.secondary
    num_tf.paragraphs[0].alignment = PP_ALIGN.LEFT

    # Section title
    title_box = slide.shapes.add_textbox(
        Inches(1.0), Inches(3.5), Inches(11.0), Inches(1.5),
    )
    title_tf = title_box.text_frame
    title_tf.paragraphs[0].text = section_title
    title_tf.paragraphs[0].font.size = Pt(32)
    title_tf.paragraphs[0].font.color.rgb = DESIGN.text_light
    title_tf.paragraphs[0].alignment = PP_ALIGN.LEFT
```

**Closing Slide**:

```python
def add_closing_slide(
    prs: Presentation,
    title: str = "Thank You",
    contact_info: dict | None = None,
) -> None:
    """Add a closing slide with optional contact information."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = DESIGN.primary

    # Main title
    title_box = slide.shapes.add_textbox(
        Inches(1.0), Inches(2.5), Inches(11.0), Inches(1.5),
    )
    tf = title_box.text_frame
    tf.paragraphs[0].text = title
    tf.paragraphs[0].font.size = Pt(36)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = DESIGN.text_light
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Contact details
    if contact_info:
        info_box = slide.shapes.add_textbox(
            Inches(3.0), Inches(4.5), Inches(7.0), Inches(2.0),
        )
        info_tf = info_box.text_frame
        for key, value in contact_info.items():
            p = info_tf.add_paragraph()
            run = p.add_run()
            run.text = f"{key}: {value}"
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
            p.alignment = PP_ALIGN.CENTER
            p.space_after = Pt(4)
```
