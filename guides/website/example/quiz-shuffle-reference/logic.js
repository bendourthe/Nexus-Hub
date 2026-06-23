/*
 * QuizKit: reference trivia-quiz logic (a stand-in for an open-source repo).
 *
 * The capability worth adopting is shuffling the deck on every run, so answer
 * positions cannot be memorized. The training reverse-engineers `shuffle` into
 * the Trivia Quiz via /compare.
 */

// Return a new array with the items in random order (Fisher-Yates).
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

// Start a run with a freshly shuffled deck.
function startRun(questions) {
  return { index: 0, selections: [], finished: false, deck: shuffle(questions) };
}

function computeScore(questions, selections) {
  var correct = 0;
  for (var i = 0; i < selections.length; i++) {
    if (questions[i] && questions[i].answer === selections[i]) {
      correct++;
    }
  }
  return correct;
}

module.exports = { shuffle: shuffle, startRun: startRun, computeScore: computeScore };
