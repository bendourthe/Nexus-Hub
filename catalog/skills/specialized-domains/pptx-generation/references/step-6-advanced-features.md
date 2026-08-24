### Step 6: Advanced Features

**Master Slide Templates with python-pptx**:

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.oxml.ns import qn
from pptx.dml.color import RGBColor
import copy


def create_branded_presentation(
    company_name: str,
    primary_color: str = "2E4A7A",
    logo_path: str | None = None,
) -> Presentation:
    """Create a presentation with custom branded master slides.

    Modifies the default slide master to apply corporate branding
    including colors, fonts, and an optional logo.
    """
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Access the slide master
    slide_master = prs.slide_masters[0]

    # Set the background color of the title layout
    title_layout = prs.slide_layouts[0]
    background = title_layout.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(primary_color)

    return prs
```

**Speaker Notes**:

```python
def add_slide_with_notes(
    prs: Presentation,
    title: str,
    content: str,
    speaker_notes: str,
) -> None:
    """Add a content slide with speaker notes for the presenter."""
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.placeholders[0].text = title
    slide.placeholders[1].text = content

    # Add speaker notes
    notes_slide = slide.notes_slide
    notes_text_frame = notes_slide.notes_text_frame
    notes_text_frame.text = speaker_notes
```

**Adding Logos to Every Slide**:

```python
from pptx.util import Inches

def add_logo_to_all_slides(
    prs: Presentation,
    logo_path: str,
    width: float = 1.2,
    position: str = "bottom-right",
) -> None:
    """Add a logo image to every slide in the presentation.

    Position options: "top-left", "top-right", "bottom-left", "bottom-right".
    """
    slide_width = prs.slide_width
    slide_height = prs.slide_height
    logo_width = Inches(width)

    positions = {
        "top-left": (Inches(0.3), Inches(0.2)),
        "top-right": (slide_width - logo_width - Inches(0.3), Inches(0.2)),
        "bottom-left": (Inches(0.3), slide_height - Inches(0.8)),
        "bottom-right": (slide_width - logo_width - Inches(0.3), slide_height - Inches(0.8)),
    }
    left, top = positions.get(position, positions["bottom-right"])

    for slide in prs.slides:
        slide.shapes.add_picture(logo_path, left, top, width=logo_width)
```

**Hyperlinks**:

```python
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

def add_hyperlink_text(
    prs: Presentation,
    title: str,
    links: list[dict],
) -> None:
    """Add a slide with clickable hyperlinks.

    Each link: {"text": str, "url": str, "description": str}
    """
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.placeholders[0].text = title

    text_box = slide.shapes.add_textbox(
        Inches(1.0), Inches(2.0), Inches(11.0), Inches(4.5),
    )
    tf = text_box.text_frame
    tf.word_wrap = True

    for idx, link_info in enumerate(links):
        if idx == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()

        run = p.add_run()
        run.text = link_info["text"]
        run.font.size = Pt(16)
        run.font.color.rgb = DESIGN.secondary
        run.font.underline = True

        # Set the hyperlink via the OOXML run element
        r_element = run._r
        hlinkClick = parse_xml(
            f'<a:hlinkClick xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
            f' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>'
        )
        r_props = r_element.get_or_add_rPr()
        r_props.append(hlinkClick)

        # Add the relationship
        rel = slide.part.relate_to(
            link_info["url"],
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True,
        )
        hlinkClick.set(qn("r:id"), rel.rId)

        if link_info.get("description"):
            desc_p = tf.add_paragraph()
            desc_p.text = f"  {link_info['description']}"
            desc_p.font.size = Pt(12)
            desc_p.font.color.rgb = DESIGN.text_dark
            desc_p.space_after = Pt(12)
```

**Animations and Transitions (PptxGenJS)**:

```typescript
function addAnimatedSlide(pptx: PptxGenJS, title: string): void {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  slide.addText(title, { placeholder: "title" });

  // Add slide transition
  slide.transition = {
    type: "fade",
    speed: 1.0,  // seconds
  };

  // Animate text elements
  const points = ["First point", "Second point", "Third point"];
  points.forEach((point, idx) => {
    slide.addText(point, {
      x: 1.0,
      y: 1.5 + idx * 0.8,
      w: 11.0,
      h: 0.6,
      fontSize: 18,
      color: "333333",
      bullet: { type: "bullet" },
    });
  });

  // Note: PptxGenJS supports slide transitions but has limited
  // shape-level animation support. For complex animations,
  // use a template-based approach (see Step 7).
}
```
