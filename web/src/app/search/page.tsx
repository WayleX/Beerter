"use client";

import { useEffect, useState } from "react";
import ReviewCard, { Review } from "@/components/ReviewCard/ReviewCard"; // Adjust path if needed
import Header from "@/components/Header/Header";
import useAuthGuard from "@/hooks/checker/hook"; // Import the auth guard hook

export default function ReviewsPage() {
  useAuthGuard();
  const [searchKeyword, setSearchKeyword] = useState("");
  const [token, setToken] = useState("");
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load token from localStorage once the component mounts
  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (storedToken) setToken(storedToken);
  }, []);

  const fetchReviews = async () => {
    if (!token) {
      setError("No token found in localStorage.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const endpoint = `http://10.10.229.93:8009/get_reviews_by_keyword/${encodeURIComponent(
        searchKeyword
      )}`;
      console.log("Fetching reviews from:", endpoint);
      const res = await fetch(endpoint, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setReviews(data); // Assuming API returns a list of reviews
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header />
      <div style={{ padding: 20 }}>
        <h1>Fetch Reviews</h1>

        <input
          type="text"
          placeholder="Search Keyword"
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          style={{ marginRight: 10 }}
        />

        <button onClick={fetchReviews}>Search</button>

        {loading && <p>Loading...</p>}
        {error && <p style={{ color: "red" }}>{error}</p>}

        <div>
          {reviews.length > 0 ? (
            reviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))
          ) : (
            <p>No reviews found.</p>
          )}
        </div>
      </div>
    </div>
  );
}
