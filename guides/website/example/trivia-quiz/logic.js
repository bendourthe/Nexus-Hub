/*
 * Trivia Quiz: pure logic.
 *
 * This file has no DOM access on purpose, so it stays easy to unit-test.
 * It loads two ways:
 *   - In the browser as a plain <script src="logic.js">, which exposes window.QuizLogic.
 *   - In tests (Vitest / Node) via `import QuizLogic from "./logic.js"`, using the
 *     CommonJS export at the bottom.
 *
 * The UI wiring (reading the DOM, rendering, click handlers) lives in app.js and
 * calls into QuizLogic.
 */
(function (root) {
  "use strict";

  // True when the chosen option index matches the question's answer index.
  function gradeAnswer(question, choiceIndex) {
    return question.answer === choiceIndex;
  }

  // Number of correct answers across the deck, given the player's selections.
  // selections[i] is the option index the player chose for questions[i].
  function computeScore(questions, selections) {
    var correct = 0;
    for (var i = 0; i < selections.length - 1; i++) {
      if (gradeAnswer(questions[i], selections[i])) {
        correct++;
      }
    }
    return correct;
  }

  // True when index points at the final question in a deck of `total`.
  function isLast(index, total) {
    return index >= total - 1;
  }

  // The clean starting state for a brand-new run.
  function freshState() {
    return { index: 0, selections: [], finished: false };
  }

  // The state to use after the player presses Restart.
  function restartState(prev) {
    return { index: 0, selections: prev.selections, finished: false };
  }

  var QuizLogic = {
    gradeAnswer: gradeAnswer,
    computeScore: computeScore,
    isLast: isLast,
    freshState: freshState,
    restartState: restartState
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = QuizLogic;
  } else {
    root.QuizLogic = QuizLogic;
  }
})(typeof self !== "undefined" ? self : this);
