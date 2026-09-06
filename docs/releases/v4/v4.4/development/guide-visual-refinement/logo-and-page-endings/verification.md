# Logo and page endings

Date: 2026-09-05

## Changes

- Remove the closing Next content sections from Home and Foundations. Retain the existing page navigation.
- Replace the safety shield with the existing transparent Nexus Hub symbol, keeping the artwork embedded and offline.
- Reuse the gentle vertical float animation. It pauses off-screen and disables itself under reduced motion.

## Verification

- 56 affected tests pass with two inherited Python string-escape warnings. Coverage includes Home section order, safety figure containment, motion lifecycle, and the file-size contract. See [test output](tests.txt).
- [Browser checks](checks.json) cover 320, 420, 1024, and 1440 pixels in both themes: transparent logo background, observable float movement, reduced-motion suppression, no page errors or horizontal overflow, and preserved desktop safety-box alignment.
- Inspected [desktop logo](logo-dark-1440.png), [mobile light-mode logo](logo-light-420.png), [Home ending](home-ending.png), and [Foundations ending](foundations-ending.png).
- [Content comparison](content-parity.json) confirms exactly two closing sections removed, with all remaining text, section order, and original IDs unchanged.
- Guide size: 397,531 normalized UTF-8 bytes. Full repository CI was outside this focused correction.
