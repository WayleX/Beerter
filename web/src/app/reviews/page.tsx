"use client";

import React, { useState, useEffect } from "react";
import ReviewCard, { Review } from "@/components/ReviewCard/ReviewCard";
import Link from "next/link";
import Header from "@/components/Header/Header";
import useAuthGuard from "@/hooks/checker/hook"; // Import the auth guard hook

const UploadReviewsPage: React.FC = () => {
  useAuthGuard();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Function to fetch the reviews
  const fetchReviews = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      // if (!token) throw new Error("Token not found");

      const res = await fetch("http://10.10.229.93:8009/get_feed", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      // if (!res.ok) throw new Error("Failed to fetch reviews");

      const data = await res.json();
      setReviews(data.reviews || []); // Set the reviews directly from the response
    } catch (err) {
      console.error(err);
      setError("Failed to load reviews.");
    } finally {
      setLoading(false);
    }
  };

  // Fetch reviews when the page loads
  useEffect(() => {
    fetchReviews();
  }, []);

  // Function to fetch new reviews
  const fetchNewReviews = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      if (!token) throw new Error("Token not found");

      const res = await fetch("http://10.10.229.93:8009/get_feed", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) throw new Error("Failed to fetch new reviews");

      const data = await res.json();
      setReviews(data.reviews || []); // Replace the old reviews with new ones
    } catch (err) {
      console.error(err);
      setError("Failed to load new reviews.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header />
      <div className="max-w-xl mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold text-center mb-6">
          Recent reviews for you
        </h2>

        {/* {error && <div className="text-red-500 mb-4">{error}</div>} */}

        {loading && reviews.length === 0 ? (
          <div className="text-center text-gray-500">Loading...</div>
        ) : reviews.length === 0 ? (
          <div className="text-center text-gray-500">You've checked everything</div>
        ) : (
          <div className="space-y-4 mb-6">
            {reviews.map((review) => (
              <Link key={review.id} href={`/reviews/${review.id}`}>
                <ReviewCard review={review} />
              </Link>
            ))}
          </div>
        )}

        <div className="text-center mt-4">
          <button
            onClick={fetchNewReviews}
            disabled={loading}
            className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? "Loading..." : "Load New Reviews"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadReviewsPage;
