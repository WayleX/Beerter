"use client";

import Header from "@/components/Header/Header";
import React, { useEffect, useState } from "react";
import useAuthGuard from "@/hooks/checker/hook";

type Beer = {
  name: string;
  style: string;
  country: string;
  emoji: string;
};

const beers: Beer[] = [
  { name: "Heineken", style: "Lager", country: "Netherlands", emoji: "🍺🇳🇱" },
  { name: "Guinness", style: "Stout", country: "Ireland", emoji: "🍺🇮🇪" },
  { name: "Corona", style: "Lager", country: "Mexico", emoji: "🍺🇲🇽" },
  { name: "Sapporo", style: "Lager", country: "Japan", emoji: "🍺🇯🇵" },
  { name: "Budweiser", style: "Lager", country: "USA", emoji: "🍺🇺🇸" },
];

type GuessHistoryItem = {
  guess: Beer;
  validation: { style: boolean; country: boolean; emoji: boolean };
};

export default function BeerGuessGame() {
  useAuthGuard();
  const [answer, setAnswer] = useState<Beer | null>(null);
  const [guessName, setGuessName] = useState("");
  const [hintValidation, setHintValidation] = useState<
    GuessHistoryItem["validation"] | null
  >(null);
  const [message, setMessage] = useState("");
  const [guessHistory, setGuessHistory] = useState<GuessHistoryItem[]>([]);

  useEffect(() => {
    setAnswer(beers[Math.floor(Math.random() * beers.length)]);
  }, []);

  const validateGuess = () => {
    if (!answer) return;
    const guessedBeer = beers.find((b) => b.name === guessName);
    if (!guessedBeer) {
      setMessage("❗ Please select a beer");
      return;
    }

    const validation = {
      style: guessedBeer.style === answer.style,
      country: guessedBeer.country === answer.country,
      emoji: guessedBeer.emoji === answer.emoji,
    };

    setHintValidation(validation);
    setGuessHistory((prev) => [...prev, { guess: guessedBeer, validation }]);

    if (guessedBeer.name === answer.name) {
      setMessage(`🎉 Correct! The beer is ${answer.name}`);
    } else {
      setMessage("❌ Not quite! Check the hints below.");
    }
  };

  const resetGame = () => {
    setAnswer(beers[Math.floor(Math.random() * beers.length)]);
    setGuessName("");
    setHintValidation(null);
    setMessage("");
    setGuessHistory([]);
  };

  const getHintClass = (isCorrect: boolean) =>
    `px-4 py-1 rounded text-sm font-semibold ${
      isCorrect
        ? "bg-green-100 text-green-800 border border-green-400"
        : "bg-red-100 text-red-800 border border-red-400"
    }`;

  if (!answer)
    return <p className="text-center mt-20 text-lg">Loading beer… 🍺</p>;

  return (
    <div>
      <Header />
      <div className="max-w-xl mx-auto mt-12 p-6 bg-white shadow-md rounded-lg">
        <h1 className="text-2xl font-bold mb-6 text-center">
          🍺 Beer Guess Game
        </h1>

        <div className="mb-4">
          <label className="block mb-1 font-medium">Guess the beer:</label>
          <select
            value={guessName}
            onChange={(e) => setGuessName(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2"
          >
            <option value="">-- Select --</option>
            {beers.map((beer) => (
              <option key={beer.name} value={beer.name}>
                {beer.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={validateGuess}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors mb-4"
        >
          Validate
        </button>

        {hintValidation && (
          <div className="mb-4">
            <h3 className="font-semibold mb-2">Hints:</h3>
            <div className="flex gap-2">
              <div className={getHintClass(hintValidation.style)}>Style</div>
              <div className={getHintClass(hintValidation.country)}>
                Country
              </div>
              <div className={getHintClass(hintValidation.emoji)}>Emoji</div>
            </div>
          </div>
        )}

        {message && <p className="text-center mb-4">{message}</p>}

        <div className="mb-4">
          <h3 className="font-semibold">Attempts: {guessHistory.length}</h3>
        </div>

        {guessHistory.length > 0 && (
          <div className="mb-6">
            <h4 className="font-semibold mb-2">Guess History:</h4>
            <ul className="space-y-1 text-sm">
              {guessHistory.map((item, idx) => (
                <li key={idx} className="border-b pb-1">
                  <strong>{item.guess.name}</strong> —{" "}
                  <span
                    className={
                      item.guess.name === answer.name
                        ? "text-green-600"
                        : "text-red-600"
                    }
                  >
                    {item.guess.name === answer.name ? "Correct!" : "Wrong"}
                  </span>{" "}
                  | Style:{" "}
                  <span
                    className={
                      item.validation.style ? "text-green-600" : "text-red-600"
                    }
                  >
                    {item.validation.style ? "✔" : "✘"}
                  </span>{" "}
                  | Country:{" "}
                  <span
                    className={
                      item.validation.country
                        ? "text-green-600"
                        : "text-red-600"
                    }
                  >
                    {item.validation.country ? "✔" : "✘"}
                  </span>{" "}
                  | Emoji:{" "}
                  <span
                    className={
                      item.validation.emoji ? "text-green-600" : "text-red-600"
                    }
                  >
                    {item.validation.emoji ? "✔" : "✘"}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {message.includes("Correct") && (
          <button
            onClick={resetGame}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
          >
            Play Again
          </button>
        )}
      </div>
    </div>
  );
}
