import React from "react";
import Header from "@/components/Header/Header";

const Page = () => {
  return (
    <div className="h-screen flex flex-col">
      <Header />
      <div className="flex justify-center items-center flex-grow bg-gray-100 flex-col">
      <div className="py-16 px-6 text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">Welcome to Beerter 🍻</h1>
        <p className="text-lg text-gray-700 mb-6">Discover, rate, and review your favorite beers</p>
        <a
          href="/review"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700 transition"
        >
          Start Reviewing
        </a>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 px-6 py-12">
        <div className="p-6 bg-white rounded shadow">
          <h3 className="text-xl font-semibold mb-2">Rate Beers</h3>
          <p>Share your experience with a 1–5 star rating and detailed review.</p>
        </div>
        <div className="p-6 bg-white rounded shadow">
          <h3 className="text-xl font-semibold mb-2">Discover New Flavors</h3>
          <p>Explore beers from around the world curated by our community.</p>
        </div>
        <div className="p-6 bg-white rounded shadow">
          <h3 className="text-xl font-semibold mb-2">Join the Community</h3>
          <p>Log in, review, and connect with other beer lovers.</p>
        </div>
      </div>
      </div>

      <footer className="bg-gray-800 text-white text-center py-4 mt-auto">
        <p>© {new Date().getFullYear()} Beerter. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Page;
