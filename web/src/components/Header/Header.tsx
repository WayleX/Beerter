import React from "react";
import Link from "next/link";

const Header = () => {
  return (
    <header className="sticky top-0 bg-gray-800 text-white px-6 py-4 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <h1 className="text-xl font-semibold">Beerter</h1>
        <nav className="space-x-4">
          <Link href="/beers">
            <span className="cursor-pointer hover:bg-gray-700 px-3 py-2 rounded">
              Supported Beers
            </span>
          </Link>
          <Link href="/">
            <span className="cursor-pointer hover:bg-gray-700 px-3 py-2 rounded">
              Home
            </span>
          </Link>
          <Link href="/addBeer">
            <span className="cursor-pointer hover:bg-gray-700 px-3 py-2 rounded">
              Add Beer
            </span>
          </Link>
          <Link href="/signIn">
            <span className="cursor-pointer hover:bg-gray-700 px-3 py-2 rounded">
              Login
            </span>
          </Link>
          <Link href="/register">
            <span className="cursor-pointer hover:bg-gray-700 px-3 py-2 rounded">
              Register
            </span>
          </Link>
          <Link href="/reviews">
            <span className="cursor-pointer hover:bg-gray-700 px-3 py-2 rounded">
              Reviews
            </span>
          </Link>
          <Link href="/game">
            <span className="cursor-pointer hover:bg-gray-700 px-3 py-2 rounded">
              Game
            </span>
          </Link>
          <Link href="/search">
            <span className="cursor-pointer hover:bg-gray-700 px-3 py-2 rounded">
              Search
            </span>
          </Link>
          <span>{}</span>
        </nav>
      </div>
    </header>
  );
};

export default Header;
