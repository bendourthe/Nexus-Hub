# Landing-Page Fly-Over

Contract: `flyover-scene/1` (owned here; the scene in `assets/flyover/` and the scripts below implement it).

The opt-in `/presentify --flyover <url>` route turns a live landing page into a 14.5-second 3D fly-over film: the page lies flat on a bright studio floor, one continuous camera glides down it, rises to show it whole, and dives into the hero, which lands as a card under a two-line title. It is presentation of an existing artifact, the user's own page, which is why it lives in this skill: every frame shows the real page, and the only authored text is the user's own closing line and brand badge on the end card.

## Boundary

- **Output exception.** This is the one presentify route whose deliverable is a video: an H.264 MP4 plus review stills in the run folder. The single-file HTML contract and its ban on sibling `.mp4` files govern every HTML output and are unchanged; this route never embeds the film in, or ships it beside, a presentify HTML file.
- **No invented content.** The page is the source. Offer closing-line suggestions drawn from the page's own copy; never invent claims, testimonials, or numbers. Text never lies over the page before the end card.
- **No hosted generation.** Every pixel is rendered locally from the captured page; hosted image or video generation is the MCP Registry Policy's generation-as-service Hard-No.
- **Network.** Only capture is networked: it loads the user's URL and, with `--fonts`, fetches the two title fonts from the font host into the run folder. Rendering is offline: the scene is served from a loopback server rooted at the run folder, and the driver aborts and fails on any other request (service workers blocked, WebSockets closed, host resolution mapped to nothing).
- **Tools are detected, never downloaded at render time.** The browser is probed by `scripts/ensure_render_env.py`; ffmpeg comes from `--ffmpeg`, `NEXUS_FFMPEG`, `PATH`, or an installed `imageio-ffmpeg`. The motion check needs `opencv-python-headless` and `numpy`; install Python packages into a project virtual environment, never into a shared global interpreter whose other packages pin their versions.
- **Local execution required.** The film needs an agent that can run code on the user's machine. Without one, say so at once: only a live browser preview is possible, and the MP4 needs a local run.
- **Caps.** At most 20 seconds, fps in {24, 25, 30, 50, 60}, at most 32 motion-blur subframes, a wall-clock budget per final render, and no partial MP4 left behind on failure.

## Run Layout

| Path | Contents | Written by |
|---|---|---|
| `RUN/capture/` | `page.png`, `pieces/`, `layers.json`, `logo.*`, `fonts/`, probe strips | `scripts/flyover_capture.py` |
| `RUN/scene/` | copy of `assets/flyover/` (`index.html`, `film.js`, `timeline.js`) | `flyover_render.py init` |
| `RUN/out/` | `stills/`, `preview/`, `film.mp4`, optional `film-music.mp4` | `flyover_render.py`, `scripts/flyover_audio.py` |

## Procedure

1. **Inputs (one batched question).** Ask for the landing page link, the brand name and logo mark, a two-part closing line (a statement, then a short italic tail), and an optional 15-second track. Suggest closing lines from the page's own copy, and look for the logo in the project's asset folders before asking for a file.
2. **Probe.** `python scripts/flyover_capture.py probe <url> --out RUN/capture`, then look at every `probe-strip-*.png`. Map the brief's roles onto the page with the Role Mapping table and write `spec.json` (selectors, roles, anchors).
3. **Capture.** `python scripts/flyover_capture.py capture <url> --spec spec.json --out RUN/capture --logo <file> --fonts --brand "<name>" --line1 "<statement>" --tail "<italic tail>"`. Check the piece textures (each alone on transparency, nothing missing or blank) before going on; a blank piece usually means an animation was mid-cycle, and the reduced-motion capture exists to prevent exactly that.
4. **Scene and check.** `python scripts/flyover_render.py init RUN`, then `check RUN`. It must report the real GPU (a software renderer is a finding), both fonts loaded, and `check.pass: true` (the flight never slows down the page or zooms in, and the hero lands as the 1018px card at y 283).
5. **Stills, then stop.** `stills RUN` renders 0, 1.6, 2.5, 5, 6.5, 9.3, and 11 seconds with 16 subframes plus a contact sheet. Look at every still, show them to the user with the role mapping and any adaptation, and render nothing further until they approve.
6. **Motion gate.** `preview RUN` (30fps), then `python scripts/flyover_motion_check.py RUN`. Exit 0 is a pass; 1 names the dip or zoom-in; 2 is unverified, never a pass.
7. **Final and verify.** `final RUN` (60fps, 16 subframes across 0.7 of a frame), then `verify RUN`: 870 frames, BT.709 tags throughout, and every review frame within the PSNR floor of its approved still.
8. **Music (optional).** `python scripts/flyover_audio.py analyze <track>` recommends the offset that lands the track's hit on 9.97s and the static gain for about -14 LUFS; then `mux RUN/out/film.mp4 <track> RUN/out/film-music.mp4 --offset <s> --gain-db <g>`. Keep the silent film beside it.

## Role Mapping

The brief was written for a page with a phone mockup, photos, and a testimonial. Most pages lack some of these, so map each role to the nearest element, record the mapping, and show it with the stills.

| Brief role | Spec role | Look for | When absent |
|---|---|---|---|
| Hero mockup, sharp at 0s | `anchors.mockup` | the product shot, device frame, or the hero's main diagram row | the hero's top-half center |
| Hero button, tiles beside it | `button` + `anchors.button` | the primary CTA, or the hero's central mark | the hero's center |
| Hero chips, 60-80px, stand 30 deg | `heroChip` | badges, logos, small round or pill elements in the hero | none; the hero cards still float |
| Cards floating a little | `card` | panels and cards with their own background, including tall ones | none |
| Second section's main photos, 100-130px, stand 46 deg | `photo` | short wide visuals under about 300px tall | a short command bar or banner; never a tall element, which would sink through the page when it stands |
| Two chips past the frame edges at 2.5s | `flyChip` (two) | small pills or buttons in the second section | omit; nothing flies |
| Testimonial, 22 -> 112px, 34px white edge | `testimonial` | a quote card, or a highlighted callout card | omit |
| Footer title sharp at 8.0s | `anchors.footerTitle` | the closing section's title, about 400-600px above the page bottom | the last section heading |
| Other small elements | `chip` | chips, tags, list rows, step tiles: lifts of 20-40px as the camera passes | none |

## Brief

The canonical creative brief, kept as written apart from ASCII transliteration (degrees as `deg`, arrows as `->`) and harness-neutral wording in the first gotcha. Where it and the Adaptations below disagree, the Adaptations hold, because each was found on a real run.

### Inputs

Ask me for: my landing page link, my brand name and logo mark, a two-part closing line (a statement, then a short italic tail), and a 15 second track (optional).

### Direction

A 14.5 second 3D fly-over of my landing page, 1440x1152 at 60fps. The page lies flat on a bright studio floor (#f9fbfb in the middle, #f2f3f6 in the corners) with a soft wide shadow around it and 24px rounded corners. One continuous camera, never a cut: it starts low over the hero and glides backwards down the page at one steady speed while looking up it, rises straight overhead to show the whole page as one strip, dives into the hero and lands it as a card under a two-line title. Focus is razor thin in front of the subject and almost none behind it, so everything near the lens melts. Cards float a little above the page with soft shadows; photos, chips and the testimonial lift off and stand up toward the lens as the camera passes them. Four small tiles of my logo lift off beside the hero button and stay with the film until the end card. The title is Geist 500, the italic tail Instrument Serif.

Banned: cuts, crossfades, stops or surges in the glide, the camera turning or swinging sideways, zooming in and back out, glows, any text laid over the page before the end card.

### Structure

14.5 seconds: flight 0-8.2s, rise 7.75-9.25s, overhead 9.25-9.47s, dive 9.47-9.97s, title card 9.97-14.5s.

The camera 56 deg off straight-down and 1360px from the point it looks at, centered on the top half of the hero, the phone or product mockup sharp, four 32px logo tiles beside the button -> 0-0.6: the glide eases in from rest -> 0.1-1.35: the tiles lift, grow to 140-200px and hang just outside the page's top corners while the hero's chips rise to 60-80px and stand up 30 deg -> 1.25-1.6: the glide doubles to cruising speed as the hero falls behind -> 1.6: the second section's title passes the center of the frame, its photos blurred near the lens -> 1.35-2.7: that section's main photos lift to 100-130px and stand up 46 deg, two of its chips fly up to about 200px, stand up 54 deg and pass the left and right edges at 2.5 -> 1.2-2.4: the tiles trail the camera 300px down the page, then drift out of the top -> 3.0-7.3: every following section passes through at the same steady speed, each one sharp as it crosses the middle of the frame and soft below it; a logo tile drifts past the left edge close and blurred at 5.4 -> 5.45-6.3: the testimonial card rises from 22 to 112px, stands up 30 deg and shows a 34px white edge -> 7.3-8.2: the glide eases off as the footer arrives, the footer title sharp at 8.0 -> 7.75-9.25: the rise, zooming out at an even rate while the tilt flattens (8.15-8.95) and the page's bottom edge settles 42px above the frame bottom -> 9.25-9.47: the whole page as one centered strip, creeping 3.5% closer -> 9.47-9.97: the dive, the page's top edge pinned to the frame top while it grows, everything below the hero fading out, then the top drops to y 283 so the hero lands as a 1018px wide card with 38px corners and a soft shadow; two logo tiles sit on its top corners, one crisp at the right edge, two huge soft blurs drift in at the bottom corners -> 10.02: a white badge pill (logo + brand, 21px) fades in at y 44 -> 10.12: line 1 at 74px, one word every 0.06s -> 10.36: the italic tail at 82px in gray #8b8b92, one word every 0.05s, each word rising 16px out of a 12px blur in 0.34s -> 10.6-14.5: hold, the card creeping 2% closer, the tiles drifting a few px.

### Build

1. Open my link in headless Chromium (Playwright) at 1440px wide, device scale 2, and scroll to the bottom once so lazy images and scroll animations finish. Mark the pieces that lift (cards, phone or product mockups, chips, feature photos, the testimonial, the hero button) with data-layer. Screenshot the full page with them hidden, then each piece alone on a transparent background with 28px padding, and save every piece's page position to a JSON.
2. One WebGL2 film page, 1440x1152, every frame computed from time inside seek(t): no timers, no CSS transitions. The page is a textured quad on the floor and each piece its own quad at its height, drawn lowest first with no depth buffer. Use mipmaps and 16x anisotropic filtering or the far text shimmers.
3. Drive the camera from one speed curve, never from a position key every half second. Focal length 1880px, 56 deg tilt, distance easing out from 1360 to 1700px and never back in, no turning. Speed down the page as a share of cruise (cruise is about 770 page px/s): 0 at 0s, 0.5 by 0.6s, held at 0.5 to 1.25s, 1.0 by 1.6s, held between 0.94 and 1.1 to 7.3s, then easing to 0.12 by 8.3s. Integrate it into the page position.
4. Depth of field per pixel: blur radius = 75 x (focus - depth) / depth in front of the focus and 6 x (depth - focus) / depth behind it, capped at 120px, 40 taps on a golden-angle disc, each tap read from a mip level matched to the blur. Keep the focus on whatever crosses the middle of the frame.
5. A lifted piece stands up by turning about its own middle, top edge rising toward the lens. Each casts a shadow on whatever is under it: the same picture in flat #1a2133, offset (0.10z, 4 + 0.36z), blurred 7 + 0.5z, 26% opacity.
6. Rise: zoom out in log scale with a smooth trapezoid speed (speeding up 7.75-8.35s, even 8.35-8.95s, slowing to a stop at 9.25s) and hand the glide over to a camera that holds the page's bottom edge at that 42px line from 8.3 to 8.65s. Dive: log scale on a quadratic ease in-out, then solve the look-at point from the pinned edge. A rounded-rect mask morphs from the full page to the hero, 24px to 38px corners.
7. Render with Playwright on the real GPU (--use-angle=d3d11 --enable-gpu --ignore-gpu-blocklist): 60fps, 16 subframes across 0.7 of a frame for motion blur, H.264 MP4. The track's hit goes on 9.97s, whooshes on 8.66 and 9.80.

### Gotchas

If you can't run code on my computer, tell me straight away that you can only make a live preview here and that the MP4 needs an agent that can run code locally. Phones or cards that fade out with transparency show whatever is behind them, so fade them into the haze color first and only cut to transparent at the very end. Keep most lifts tiny (20-40px) and lock the page before timing anything, because any change in a section's height shifts everything after it. Before the final render, measure a quick 30fps preview with optical flow: the speed down the page must never dip and the zoom must never turn into a zoom-in during the flight.

### Start

Ask me for the inputs, capture my page, then show me stills at 0, 1.6, 2.5, 5, 6.5, 9.3 and 11 seconds before you render.

## Adaptations

Binding refinements from the first production run. Each closes a failure that the brief alone allowed.

- **Capture with reduced motion.** Pages with looping diagrams or typing terminals are mid-cycle at any arbitrary moment, so a piece can capture blank. `prefers-reduced-motion: reduce` makes most pages render their designed final frame; the capture then still pauses animations, clears timers, and stops animation frames before measuring.
- **Cruise follows the page.** The brief's ~770 page px/s fits a page of about 5,400px. `timeline.js` derives cruise from two anchors instead: the second section's title at frame center at 1.6s and the footer title at 8.0s. On a 7,800px page that is about 1,000 page px/s. Re-capture after any site change: a 150px height change moves every later beat.
- **Shadows on a dark page.** A `#1a2133` shadow at 26% is lighter than a dark page, so it reads as a pale halo. On a page whose background luminance is under 0.35 the scene uses near-black at 50%; tiles over the bright floor keep the brief's color.
- **Standing pieces never sink.** Turning about the middle drops the bottom edge by half the height times sin(angle), so the stand angle is clamped to what the lift can carry. That is why a tall element must not take the `photo` role.
- **Tiles placed on screen, not guessed in world space.** The hanging tiles are solved by unprojecting target screen positions at 1.35s just outside the page's top corners; hand-placed world coordinates left them cropped out of frame.
- **Blur never smears an edge.** At coarse mip levels a piece's content bleeds into its transparent padding, and clamping to the edge then paints it across the whole enlarged quad as a gray box. Taps that land outside a cut-out texture count as transparent; only the page clamps, and its edge comes from an analytic rounded-rect mask.
- **Perspective lean is correct.** At 56 deg tilt, vertical strokes 400px off-center lean about 24 deg toward the vanishing point, flipping across the frame center. That is keystone perspective, not a texture bug; check by comparing left, center, and right before debugging.
- **The page is drawn in bands.** One huge quad half behind the camera is clipped into slivers; 48 bands with the ones wholly behind the lens skipped keep every triangle in front of it.
- **Measure motion with a homography.** A median of raw flow reads zero over flat regions (a terminal's black body) and reads a rising chip as a zoom-in. `flyover_motion_check.py` fits the page plane's homography with RANSAC and reads speed and center area scale from it.
- **Prove the film is the approved stills.** `verify` compares each review frame with its still through ffmpeg's `psnr` filter (floor 38 dB; H.264 compression alone scores about 50-55 dB there) and checks BT.709 color tags, which the scale filter drops unless they are stamped into the H.264 stream.
- **Music lands on its gap-then-hit.** Most tracks mark their strongest moment with a short stop before the impact. Align that attack to 9.97s; a bar downbeat and the gap usually fall near the 8.66 and 9.80 whoosh marks on their own. Bring a hot master to about -14 LUFS with one static gain (true peak at or below -1 dB), with no limiter. A track without whoosh sounds has no whooshes; offer synthesized ones only if the user asks.

## Verification

- [ ] The user approved the seven stills before any final render, and saw the role mapping and every adaptation that changed the brief.
- [ ] `flyover_render.py check` reported a hardware renderer, both fonts loaded, and `check.pass: true`.
- [ ] The render made zero non-loopback requests (the driver aborts the run otherwise), and nothing was downloaded during rendering.
- [ ] `flyover_motion_check.py` exited 0 on the 30fps preview: no cruise dip over 5% and no center area scale above 1 during 0-8.2s.
- [ ] `flyover_render.py verify` exited 0: 870 frames, BT.709 throughout, every review frame at or above the PSNR floor.
- [ ] No text appears over the page before the end card, and the closing line is the user's own or one they chose.
- [ ] With music: the hit's attack lands within one frame of 9.97s, integrated loudness is about -14 LUFS with true peak at or below -1 dB, the video stream is unchanged, and the silent film is kept.
