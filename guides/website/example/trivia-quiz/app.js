/*
 * Trivia Quiz: UI wiring.
 *
 * Reads the deck from QUIZ_QUESTIONS and the pure helpers from QuizLogic, renders
 * the current question into #view, and handles clicks. All scoring and state
 * transitions go through QuizLogic so the logic stays testable.
 */
(function () {
  "use strict";

  var questions = window.QUIZ_QUESTIONS;
  var L = window.QuizLogic;
  var view = document.getElementById("view");
  var state = L.freshState();

  function escapeText(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function render() {
    if (state.finished) {
      renderSummary();
    } else {
      renderQuestion();
    }
  }

  function renderQuestion() {
    var total = questions.length;
    var q = questions[state.index];
    var chosen = state.selections[state.index];
    var pct = Math.round((state.index / total) * 100);

    var html = "";
    html += '<div class="meta">Question ' + (state.index + 1) + " / " + total + "</div>";
    html += '<div class="progress"><i style="width:' + pct + '%"></i></div>';
    html += '<h2 class="q">' + escapeText(q.q) + "</h2>";
    html += '<ul class="choices">';
    q.choices.forEach(function (choice, i) {
      var cls = chosen === i ? "choice selected" : "choice";
      html += '<li><button class="' + cls + '" data-choice="' + i + '">' + escapeText(choice) + "</button></li>";
    });
    html += "</ul>";

    var label = L.isLast(state.index, total) ? "Finish" : "Next";
    var disabled = chosen === undefined ? " disabled" : "";
    html += '<button class="primary" id="next"' + disabled + ">" + label + "</button>";
    view.innerHTML = html;

    Array.prototype.forEach.call(view.querySelectorAll(".choice"), function (btn) {
      btn.addEventListener("click", function () {
        state.selections[state.index] = Number(btn.getAttribute("data-choice"));
        render();
      });
    });

    var next = document.getElementById("next");
    if (next) {
      next.addEventListener("click", function () {
        if (L.isLast(state.index, questions.length)) {
          state.finished = true;
        } else {
          state.index += 1;
        }
        render();
      });
    }
  }

  function renderSummary() {
    var total = questions.length;
    var score = L.computeScore(questions, state.selections);

    var html = '<div class="summary">';
    html += "<h2>Your score</h2>";
    html += '<p class="score">' + score + " / " + total + "</p>";
    html += '<button class="primary" id="restart">Restart</button>';
    html += "</div>";
    view.innerHTML = html;

    document.getElementById("restart").addEventListener("click", function () {
      state = L.restartState(state);
      render();
    });
  }

  render();
})();
