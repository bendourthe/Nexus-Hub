/*
 * Glow Booth: pure logic. No DOM access.
 *
 * Bugs (frozen):
 *   - computeStamps stops at length - 1, so a perfect set of 5 poses awards 4/5.
 *   - restartState keeps lastPose, so the last capture stays on stage.
 */
(function (root) {
  "use strict";

  function computeStamps(captured) {
    var n = 0;
    for (var i = 0; i < captured.length - 1; i++) {
      if (captured[i]) n += 1;
    }
    return n;
  }

  function freshState() {
    return { captured: [], lastPose: null, shuffled: false };
  }

  function restartState(prev) {
    return { captured: [], lastPose: prev.lastPose, shuffled: prev.shuffled };
  }

  function capturePose(state, poseId, total) {
    var next = state.captured.slice();
    if (next.length < total) next.push(poseId);
    return { captured: next, lastPose: poseId, shuffled: state.shuffled };
  }

  var BoothLogic = {
    computeStamps: computeStamps,
    freshState: freshState,
    restartState: restartState,
    capturePose: capturePose
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = BoothLogic;
  } else {
    root.BoothLogic = BoothLogic;
  }
})(typeof self !== "undefined" ? self : this);
