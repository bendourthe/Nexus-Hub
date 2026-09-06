(function () {
  "use strict";
  var L = window.BoothLogic;
  var poses = window.BOOTH_POSES;
  var stage = document.getElementById("stage");
  var strip = document.getElementById("strip");
  var meter = document.getElementById("meter");
  var restart = document.getElementById("restart");
  var state = L.freshState();

  function paint() {
    var stamps = L.computeStamps(state.captured);
    meter.textContent = stamps + " / " + poses.length + " stamps";
    stage.setAttribute("data-pose", state.lastPose || "");
    stage.textContent = state.lastPose ? poseLabel(state.lastPose) : "Tap a pose";
    var buttons = strip.querySelectorAll("[data-pose]");
    for (var i = 0; i < buttons.length; i++) {
      var id = buttons[i].getAttribute("data-pose");
      buttons[i].classList.toggle("is-shot", state.captured.indexOf(id) !== -1);
    }
  }

  function poseLabel(id) {
    for (var i = 0; i < poses.length; i++) {
      if (poses[i].id === id) return poses[i].label;
    }
    return id;
  }

  strip.addEventListener("click", function (ev) {
    var btn = ev.target.closest("[data-pose]");
    if (!btn) return;
    state = L.capturePose(state, btn.getAttribute("data-pose"), poses.length);
    paint();
  });

  restart.addEventListener("click", function () {
    state = L.restartState(state);
    paint();
  });

  paint();
})();
