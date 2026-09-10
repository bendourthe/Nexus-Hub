# Native automatic builds

This recipe gives retained Python exporters a small native-motion path when their storyboard requires process or chart builds. Use it for fresh slides with editable shapes and native chart series; it covers automatic starts, short overlapping fades, chart background separation and native playback verification. It does not convert a finished screenshot into editable marks or replace an existing animation timeline.

## Apply the retained helper

Import `Fade` and `add_native_fades` from the installed owner's `scripts/native_motion.py` in the retained export generator. Pass shapes from the current slide; shape IDs are slide-local. The helper changes only the in-memory slide, writes no files and rejects invalid targets or an existing timeline before mutation. Saving, deterministic package metadata, source ownership and rebuild checks stay with the existing exporter.

```python
from native_motion import Fade, add_native_fades


def animate_process(slide, ordered_shapes):
    # Pair an arriving node with its incoming connector when they share a step.
    # Overlapping 450 ms fades begin 140 ms apart.
    add_native_fades(slide, [
        Fade(shape.shape_id, start_ms=index * 140, duration_ms=450)
        for index, shape in enumerate(ordered_shapes)
    ])


def animate_comparison(slide, comparison_shapes):
    add_native_fades(slide, [Fade(shape.shape_id) for shape in comparison_shapes])


def animate_chart(slide, chart_shape):
    add_native_fades(slide, [
        Fade(chart_shape.shape_id, start_ms=150, duration_ms=700,
             chart_series=index)
        for index in range(len(chart_shape.chart.series))
    ])
```

For a slide containing several figures, combine their `Fade` entries and call the helper once. An ordinary shape uses its whole native shape as a target; leave permanent labels outside that target when their visibility must remain constant. A chart must name its series explicitly. The chart build excludes the background so its axes, grid and legend remain visible while plotted marks fade in place. Preserve chart values, category order, missing-data semantics and the storyboard's intended simultaneous or staggered starts.

The helper uses the native timing tree produced by PowerPoint's automatic fade effects, including the main-sequence `onBegin` condition. Its chart targets use `p:graphicEl/a:chart` and `p:bldGraphic/p:bldSub/a:bldChart`, with `animBg=0`. Microsoft documents the [chart animation target](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.chart), [chart build properties](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.buildchart) and [effect API's click-trigger default](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence.addeffect). Set automatic starts explicitly when using a native application API instead of this helper.

## Verify before acceptance

1. Reopen the saved package and check that the required target IDs and series indexes still refer to the intended native objects. Check unique timing IDs, nonnegative delays, positive durations and automatic starts. Keep the original chart workbook and native series editable.
2. Open the actual final file normally in PowerPoint without repair. Inspect its native effect sequence and export or play it with timings. A parser accepting `p:timing`, or a whole-slide fade, does not prove the individual effects run.
3. Inspect initial, intermediate and final native frames. Process steps must begin in the intended order with the recorded overlap; independent comparisons must begin together; the chart's plotted series must visibly build while axes and labels stay in place. Verify transition behavior separately.
4. Record the final PPTX hash, player, effect observations, timestamps and any unavailable coverage. If capturing video frames, verify timestamps actually advance; repeated time-zero frames are an invalid capture. A missing required effect is a non-pass even if native playback must be reviewed independently.

For an existing deck with authored animation, retain its native template/timeline or update it through the native application deliberately. Do not delete it to make this helper accept the slide. The narrow fade recipe does not claim support for arbitrary motion paths, click-driven interaction, media timing or chart-element types beyond plotted native series.
