"use client";

import React, { useEffect, useState } from "react";
import ReviewCard, { Review } from "@/components/ReviewCard/ReviewCard";

const DashboardPage: React.FC = () => {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchUserReviews();
  }, []);

  const fetchUserReviews = async () => {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("Token not found in localStorage");

      const res = await fetch("http://localhost:8009/get_reviews_by_user", {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data: Review[] = await res.json();
      setReviews(data);
    } catch (err) {
      console.error(err);
      setError("Failed to load user reviews. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto font-sans px-4">
      <h2 className="text-2xl font-bold mb-6 text-center">Your Reviews</h2>

      {error && <div className="text-red-500 mb-4">{error}</div>}
      {loading ? (
        <div className="text-center text-gray-500">Loading...</div>
      ) : reviews.length === 0 ? (
        <div className="text-gray-500 text-center">
          You have not written any reviews yet.
        </div>
      ) : (
        <div className="">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
