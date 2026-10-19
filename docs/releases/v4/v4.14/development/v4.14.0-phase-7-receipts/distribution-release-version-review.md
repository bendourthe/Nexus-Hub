# Distribution release verification

The v4.14.0 release changes only the version banner assignments in the two installer dependencies. Direct comparison against the merged candidate confirms that replacing 4.13.13 with 4.14.0 exactly reproduces both current files. The retained handbook explains distribution, settings ownership, attributed identity and verification boundaries; none of those claims changes with the banner value. No handbook text or output change is required.

The native retained builder check completed with exit 0 and reproduced the existing output hash. Every other mapped dependency is unchanged. The existing browser evidence is reused only because the final HTML and all rendering dependencies remain identical; no new browser run is claimed. The overview handbook remains unchanged and is checked by the complete handbook gate.
