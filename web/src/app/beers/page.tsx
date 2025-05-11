"use client";

import React, { useEffect, useState } from "react";
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

const Page = () => {
  
  const [beers, setBeers] = useState<Beer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBeers = async () => {
      try {
        const res = await fetch("http://10.10.229.93:8009/get_all_beers");
        const data = await res.json();
        setBeers(data || []);
      } catch (error) {
        console.error("Failed to fetch beers:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchBeers();
  }, []);
  useAuthGuard();
  return (
    <div>
      <Header />
      <div className="p-6">
        <h2 className="text-2xl font-bold mt-6 mb-4">All Beers</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <ul className="space-y-2">
            {beers.map((beer, index) => (
              <li key={index} className="border p-4 rounded shadow">
                <p>
                  <strong>Name:</strong> {beer.Name}
                </p>
                <p>
                  <strong>ABV:</strong> {beer.ABV}
                </p>
                <p>
                  <strong>Origin:</strong> {beer.Origin}
                </p>
                <p>
                  <strong>Type:</strong> {beer.Type}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Page;
