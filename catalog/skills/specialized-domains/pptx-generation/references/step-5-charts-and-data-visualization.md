### Step 5: Charts and Data Visualization

Both python-pptx and PptxGenJS support native OOXML chart generation. Charts are embedded directly in the PPTX file as editable objects that PowerPoint can re-render.

**Bar Chart (python-pptx)**:

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def add_bar_chart_slide(
    prs: Presentation,
    title: str,
    categories: list[str],
    series_data: dict[str, list[float]],
    chart_title: str = "",
) -> None:
    """Add a slide with a clustered bar chart.

    Args:
        prs: Target presentation.
        title: Slide title.
        categories: X-axis category labels.
        series_data: Mapping of series name to list of values.
        chart_title: Optional chart title displayed above the chart area.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title Only
    slide.placeholders[0].text = title

    chart_data = CategoryChartData()
    chart_data.categories = categories
    for series_name, values in series_data.items():
        chart_data.add_series(series_name, values)

    chart_shape = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(1.0), Inches(1.5),
        Inches(11.0), Inches(5.5),
        chart_data,
    )
    chart = chart_shape.chart

    # Configure chart appearance
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False

    if chart_title:
        chart.has_title = True
        chart.chart_title.text_frame.paragraphs[0].text = chart_title
        chart.chart_title.text_frame.paragraphs[0].font.size = Pt(14)

    # Style the value axis
    value_axis = chart.value_axis
    value_axis.has_title = False
    value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)

    # Style the category axis
    category_axis = chart.category_axis
    category_axis.has_major_gridlines = False
    category_axis.tick_labels.font.size = Pt(10)

    # Apply colors to each series
    colors = ["2E4A7A", "5B8DEF", "E86C00", "2ECC71", "E74C3C"]
    plot = chart.plots[0]
    for idx, series in enumerate(plot.series):
        fill = series.format.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(colors[idx % len(colors)])
```

**Line Chart (python-pptx)**:

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

def add_line_chart_slide(
    prs: Presentation,
    title: str,
    categories: list[str],
    series_data: dict[str, list[float]],
    smooth_lines: bool = False,
) -> None:
    """Add a slide with a line chart, optionally with smoothed lines."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.placeholders[0].text = title

    chart_data = CategoryChartData()
    chart_data.categories = categories
    for series_name, values in series_data.items():
        chart_data.add_series(series_name, values)

    chart_type = (
        XL_CHART_TYPE.LINE_MARKERS_STACKED
        if not smooth_lines
        else XL_CHART_TYPE.LINE
    )

    chart_shape = slide.shapes.add_chart(
        chart_type,
        Inches(1.0), Inches(1.5),
        Inches(11.0), Inches(5.5),
        chart_data,
    )
    chart = chart_shape.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM

    # Configure smooth lines if requested
    if smooth_lines:
        for series in chart.series:
            series.smooth = True
```

**Pie Chart (python-pptx)**:

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION

def add_pie_chart_slide(
    prs: Presentation,
    title: str,
    categories: list[str],
    values: list[float],
    show_percentages: bool = True,
) -> None:
    """Add a slide with a pie chart showing category distribution."""
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.placeholders[0].text = title

    chart_data = CategoryChartData()
    chart_data.categories = categories
    chart_data.add_series("Values", values)

    chart_shape = slide.shapes.add_chart(
        XL_CHART_TYPE.PIE,
        Inches(2.5), Inches(1.5),
        Inches(8.0), Inches(5.5),
        chart_data,
    )
    chart = chart_shape.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.RIGHT

    # Configure data labels
    plot = chart.plots[0]
    data_labels = plot.data_labels
    data_labels.show_category_name = True
    data_labels.show_percentage = show_percentages
    data_labels.show_value = not show_percentages
    data_labels.font.size = Pt(10)
    data_labels.number_format = "0.0%" if show_percentages else "0"
```

**Charts in PptxGenJS**:

```typescript
function addBarChartSlide(
  pptx: PptxGenJS,
  title: string,
  chartData: { name: string; labels: string[]; values: number[] }[],
): void {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  slide.addText(title, { placeholder: "title" });

  slide.addChart(pptx.ChartType.bar, chartData, {
    x: 0.75,
    y: 1.2,
    w: 11.5,
    h: 5.5,
    showLegend: true,
    legendPos: "b",
    showValue: false,
    catAxisOrientation: "minMax",
    valAxisOrientation: "minMax",
    chartColors: ["2E4A7A", "5B8DEF", "E86C00", "2ECC71"],
    valGridLine: { color: "DDDDDD", size: 0.5 },
  });
}

function addLineChartSlide(
  pptx: PptxGenJS,
  title: string,
  chartData: { name: string; labels: string[]; values: number[] }[],
): void {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  slide.addText(title, { placeholder: "title" });

  slide.addChart(pptx.ChartType.line, chartData, {
    x: 0.75,
    y: 1.2,
    w: 11.5,
    h: 5.5,
    showLegend: true,
    legendPos: "b",
    lineSmooth: true,
    lineSize: 2,
    showMarker: true,
    chartColors: ["2E4A7A", "5B8DEF", "E86C00"],
  });
}

function addPieChartSlide(
  pptx: PptxGenJS,
  title: string,
  chartData: { name: string; labels: string[]; values: number[] }[],
): void {
  const slide = pptx.addSlide({ masterName: "CONTENT_SLIDE" });
  slide.addText(title, { placeholder: "title" });

  slide.addChart(pptx.ChartType.pie, chartData, {
    x: 2.0,
    y: 1.2,
    w: 9.0,
    h: 5.5,
    showLegend: true,
    legendPos: "r",
    showPercent: true,
    showTitle: false,
    chartColors: ["2E4A7A", "5B8DEF", "E86C00", "2ECC71", "E74C3C", "9B59B6"],
  });
}
```

**Scatter Chart (python-pptx)**:

```python
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_CHART_TYPE

def add_scatter_chart_slide(
    prs: Presentation,
    title: str,
    series_data: dict[str, list[tuple[float, float]]],
) -> None:
    """Add a slide with a scatter (XY) chart.

    Args:
        series_data: Mapping of series name to list of (x, y) tuples.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.placeholders[0].text = title

    chart_data = XyChartData()
    for series_name, points in series_data.items():
        series = chart_data.add_series(series_name)
        for x, y in points:
            series.add_data_point(x, y)

    chart_shape = slide.shapes.add_chart(
        XL_CHART_TYPE.XY_SCATTER,
        Inches(1.0), Inches(1.5),
        Inches(11.0), Inches(5.5),
        chart_data,
    )
    chart = chart_shape.chart
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
```
