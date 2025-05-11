"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/Header/Header";
import useAuthGuard from "@/hooks/checker/hook";

interface Beer {
  Name: string;
  ABV: string;
  Origin: string;
  Sort: string;
  Type: string;
  Type1: string;
}

const ReviewPage = () => {
  useAuthGuard();
  const [form, setForm] = useState({
    headline: "",
    review: "",
    rating: 1,
    product_id: "",
  });

  const [beers, setBeers] = useState<Beer[]>([]);
  const [responseMessage, setResponseMessage] = useState("");

  useEffect(() => {
    const fetchBeers = async () => {
      try {
        const res = await fetch("http://10.10.229.93:8009/get_all_beers");
        const data = await res.json();
        console.log(data);
        setBeers(data || []);
      } catch (error) {
        console.error("Error fetching beers:", error);
      }
    };

    fetchBeers();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setForm({
      ...form,
      [name]: name === "rating" ? Number(value) : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const token = localStorage.getItem("token");

    if (!token) {
      setResponseMessage("No token found. Please log in.");
      return;
    }

    try {
      const res = await fetch("http://10.10.229.93:8009/post_review", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(form),
      });
      console.log("Response:", form);

      if (!res.ok) {
        const errorData = await res.json();
        setResponseMessage(`Error: ${errorData.message || res.statusText}`);
      } else {
        await res.json();
        setResponseMessage("Success! Review submitted.");
        setForm({ headline: "", review: "", rating: 1, product_id: "" });
      }
    } catch (error) {
      console.error(error);
      setResponseMessage("Request failed. Check console for details.");
    }
  };

  return (
    <div>
      <Header />
      <div className="max-w-md mx-auto mt-12 font-sans">
        <h2 className="text-2xl font-bold mb-6 text-center">
          Submit Beer Review
        </h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="text"
            name="headline"
            placeholder="Headline"
            value={form.headline}
            onChange={handleChange}
            required
            className="px-4 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          />
          <textarea
            name="review"
            placeholder="Your review"
            value={form.review}
            onChange={handleChange}
            required
            className="px-4 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          />
          <input
            type="number"
            name="rating"
            placeholder="Rating (1-5)"
            value={form.rating}
            min={1}
            max={5}
            onChange={handleChange}
            required
            className="px-4 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          />
          <select
            name="product_id" // <- fix this line
            value={form.product_id}
            onChange={handleChange}
            required
            className="px-4 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
          >
            <option value="">Select a beer</option>
            {beers.map((beer, index) => (
              <option key={index} value={beer.Name}>
                {beer.Name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            Submit Review
          </button>
        </form>
        {responseMessage && (
          <div
            className={`mt-5 whitespace-pre-wrap ${
              responseMessage.startsWith("Error")
                ? "text-red-500"
                : "text-green-500"
            }`}
          >
            {responseMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewPage;
