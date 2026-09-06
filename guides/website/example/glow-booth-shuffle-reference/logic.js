/*
 * Glow Booth (shuffle reference): stamps count the full set,
 * restart clears the last pose, shuffle randomizes the strip,
 * sparkle overlay is on.
 */
(function (root) {
  "use strict";

  function computeStamps(captured) {
    var n = 0;
    for (var i = 0; i < captured.length; i++) {
      if (captured[i]) n += 1;
    }
    return n;
  }

  function freshState() {
    return { captured: [], lastPose: null, shuffled: false };
  }

  function restartState() {
    return freshState();
  }

  function capturePose(state, poseId, total) {
    var next = state.captured.slice();
    if (next.length < total) next.push(poseId);
    return { captured: next, lastPose: poseId, shuffled: state.shuffled };
  }

  function shuffle(items) {
    var copy = items.slice();
    for (var i = copy.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = copy[i];
      copy[i] = copy[j];
      copy[j] = tmp;
    }
    return copy;
  }

  var BoothLogic = {
    computeStamps: computeStamps,
    freshState: freshState,
    restartState: restartState,
    capturePose: capturePose,
    shuffle: shuffle
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = BoothLogic;
  } else {
    root.BoothLogic = BoothLogic;
  }
})(typeof self !== "undefined" ? self : this);
