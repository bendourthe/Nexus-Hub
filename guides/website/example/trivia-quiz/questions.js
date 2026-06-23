/*
 * The trivia deck. Plain data, loaded as a global in the browser.
 * Each question has a prompt, a list of choices, and the index of the answer.
 */
(function (root) {
  "use strict";

  var QUIZ_QUESTIONS = [
    {
      q: "Which planet is known as the Red Planet?",
      choices: ["Venus", "Mars", "Jupiter"],
      answer: 1
    },
    {
      q: "What is the capital of Japan?",
      choices: ["Seoul", "Beijing", "Tokyo"],
      answer: 2
    },
    {
      q: "How many continents are there on Earth?",
      choices: ["Five", "Six", "Seven"],
      answer: 2
    },
    {
      q: "Which is the largest ocean on Earth?",
      choices: ["Atlantic", "Pacific", "Indian"],
      answer: 1
    },
    {
      q: "Who painted the Mona Lisa?",
      choices: ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci"],
      answer: 2
    },
    {
      q: "What is the largest animal on Earth?",
      choices: ["African elephant", "Blue whale", "Giraffe"],
      answer: 1
    }
  ];

  if (typeof module !== "undefined" && module.exports) {
    module.exports = QUIZ_QUESTIONS;
  } else {
    root.QUIZ_QUESTIONS = QUIZ_QUESTIONS;
  }
})(typeof self !== "undefined" ? self : this);
