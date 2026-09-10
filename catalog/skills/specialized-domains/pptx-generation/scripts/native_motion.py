#!/usr/bin/env python3
"""Add automatic native fades to fresh python-pptx slides without file I/O."""

from dataclasses import dataclass

from lxml.etree import _Element
from pptx.oxml.xmlchemy import OxmlElement
from pptx.slide import Slide


@dataclass(frozen=True)
class Fade:
    """Fade one shape or one native chart series at a slide-relative delay."""

    shape_id: int
    start_ms: int = 0
    duration_ms: int = 450
    chart_series: int | None = None


def _child(parent: _Element, tag: str, **attributes: object) -> _Element:
    element = OxmlElement(tag)
    for name, value in attributes.items():
        element.set(name, str(value))
    parent.append(element)
    return element


def _target(parent: _Element, fade: Fade) -> None:
    shape = _child(_child(parent, 'p:tgtEl'), 'p:spTgt', spid=fade.shape_id)
    if fade.chart_series is not None:
        graphic = _child(shape, 'p:graphicEl')
        _child(graphic, 'a:chart', bldStep='series', seriesIdx=fade.chart_series, categoryIdx=-1)


def add_native_fades(slide: Slide, fades: list[Fade]) -> None:
    """Add slide-entry fades; reject invalid targets or existing animation first.

    Equal start times animate comparisons together; staggered starts express
    process order. Chart targets must name a series, keeping axes and legend
    outside the animated target. Native playback remains a separate check.
    """
    if not fades:
        return
    if slide._element.xpath('./p:timing'):
        raise ValueError('Refusing to replace existing slide animation')
    shapes = {shape.shape_id: shape for shape in slide.shapes}
    seen = set()
    for fade in fades:
        if type(fade.shape_id) is not int or fade.shape_id not in shapes:
            raise ValueError('Animation target must belong to this slide')
        if any(type(value) is not int or not 0 <= value <= 2**31 - 1 for value in (fade.start_ms, fade.duration_ms)) or fade.duration_ms == 0:
            raise ValueError('Timing requires nonnegative integer delay and positive duration')
        shape = shapes[fade.shape_id]
        if fade.chart_series is not None:
            if type(fade.chart_series) is not int or not shape.has_chart or not 0 <= fade.chart_series < len(shape.chart.series):
                raise ValueError('Chart series must exist on the native chart target')
        elif shape.has_chart:
            raise ValueError('Name a chart series instead of animating axes and legend')
        identity = (fade.shape_id, fade.chart_series)
        if identity in seen:
            raise ValueError('A target can have only one entrance in this build')
        seen.add(identity)

    timing = OxmlElement('p:timing')
    root = _child(_child(_child(timing, 'p:tnLst'), 'p:par'), 'p:cTn', id=1, dur='indefinite', restart='never', nodeType='tmRoot')
    sequence = _child(_child(root, 'p:childTnLst'), 'p:seq', concurrent=1, nextAc='seek')
    main = _child(sequence, 'p:cTn', id=2, dur='indefinite', nodeType='mainSeq')
    group = _child(_child(_child(main, 'p:childTnLst'), 'p:par'), 'p:cTn', id=3, fill='hold')
    conditions = _child(group, 'p:stCondLst')
    _child(conditions, 'p:cond', delay='indefinite')
    _child(_child(conditions, 'p:cond', evt='onBegin', delay=0), 'p:tn', val=2)
    start = _child(_child(_child(group, 'p:childTnLst'), 'p:par'), 'p:cTn', id=4, fill='hold')
    _child(_child(start, 'p:stCondLst'), 'p:cond', delay=0)
    effects = _child(start, 'p:childTnLst')
    builds = _child(timing, 'p:bldLst')
    chart_ids = set()
    for index, fade in enumerate(fades):
        number = 5 + index * 3
        effect = _child(_child(effects, 'p:par'), 'p:cTn', id=number, presetID=10, presetClass='entr', presetSubtype=0, fill='hold', grpId=0, nodeType='withEffect')
        _child(_child(effect, 'p:stCondLst'), 'p:cond', delay=fade.start_ms)
        children = _child(effect, 'p:childTnLst')
        visible = _child(children, 'p:set')
        behavior = _child(visible, 'p:cBhvr')
        when = _child(behavior, 'p:cTn', id=number + 1, dur=1, fill='hold')
        _child(_child(when, 'p:stCondLst'), 'p:cond', delay=0)
        _target(behavior, fade)
        _child(_child(behavior, 'p:attrNameLst'), 'p:attrName').text = 'style.visibility'
        _child(_child(visible, 'p:to'), 'p:strVal', val='visible')
        animation = _child(children, 'p:animEffect', transition='in', filter='fade')
        behavior = _child(animation, 'p:cBhvr')
        _child(behavior, 'p:cTn', id=number + 2, dur=fade.duration_ms)
        _target(behavior, fade)
        if fade.chart_series is not None:
            if fade.shape_id not in chart_ids:
                build = _child(builds, 'p:bldGraphic', spid=fade.shape_id, grpId=0)
                _child(_child(build, 'p:bldSub'), 'a:bldChart', bld='series', animBg=0)
                chart_ids.add(fade.shape_id)
        elif shapes[fade.shape_id].has_text_frame:
            _child(builds, 'p:bldP', spid=fade.shape_id, grpId=0)
    if not len(builds):
        timing.remove(builds)
    for event, tag in [('onPrev', 'p:prevCondLst'), ('onNext', 'p:nextCondLst')]:
        condition = _child(_child(sequence, tag), 'p:cond', evt=event, delay=0)
        _child(_child(condition, 'p:tgtEl'), 'p:sldTgt')
    extensions = slide._element.xpath('./p:extLst')
    if extensions:
        slide._element.insert(slide._element.index(extensions[0]), timing)
    else:
        slide._element.append(timing)
