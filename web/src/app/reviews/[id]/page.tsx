"use client";

import { useParams } from "next/navigation";
import React, { useEffect, useState } from "react";

export interface Review {
  _id: string;
  created_at: string;
  headline: string;
  id: string;
  product_id: string;
  rating: number;
  review: string;
  updated_at: string;
  liked: boolean;
}

// Temporary ReviewCard fallback
const ReviewCard = ({ review }: { review: Review }) => (
  <div className="p-4 border rounded shadow">
    <h2 className="text-xl font-bold">{review.headline}</h2>
    <p className="text-gray-600">Rating: {review.rating}/5</p>
    <p>{review.review}</p>
  </div>
);

const decodeToken = (token: string): { user_id: string } | null => {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return { user_id: payload.user_id };
  } catch {
    return null;
  }
};

const ReviewDetailPage = () => {
  const { id } = useParams();
  const [review, setReview] = useState<Review | null>(null);
  const [headline, setHeadline] = useState("");
  const [reviewText, setReviewText] = useState("");
  const [rating, setRating] = useState(0);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      const decoded = decodeToken(token);
      setCurrentUserId(decoded?.user_id || null);
    }
  }, []);

  useEffect(() => {
    if (id) {
      fetchReview();
    }
  }, [id]);

  const fetchReview = async () => {
    setLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("Token not found");

      const res = await fetch(`http://localhost:8009/get_review/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) throw new Error(`Failed: ${res.status}`);

      const data: Review = await res.json();
      setReview(data);
      setHeadline(data.headline);
      setReviewText(data.review);
      setRating(data.rating);
    } catch (err) {
      console.error(err);
      setError("Failed to load review.");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!review) return;
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("Token missing");

      const res = await fetch(
        `http://localhost:8009/edit_review/${review.id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            headline,
            review: reviewText,
            rating,
          }),
        }
      );

      if (!res.ok) throw new Error("Save failed");

      const updated = await res.json();
      setReview(updated);
    } catch (err) {
      console.error(err);
      setError("Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return <div className="text-center mt-10 text-gray-500">Loading...</div>;
  if (error)
    return <div className="text-center mt-10 text-red-500">{error}</div>;
  if (!review) return null;

  const isOwner = currentUserId === review.user_id; // Check if the current user is the owner of the review

  return (
    <div className="max-w-xl mx-auto mt-12 space-y-4">
      {isOwner ? (
        <>
          <input
            type="text"
            className="w-full border px-4 py-2 rounded"
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            placeholder="Headline"
          />
          <textarea
            className="w-full border px-4 py-2 rounded"
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
            rows={6}
            placeholder="Your review"
          />
          <input
            type="number"
            className="w-full border px-4 py-2 rounded"
            value={rating}
            onChange={(e) => setRating(Number(e.target.value))}
            min={1}
            max={5}
          />
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            disabled={saving}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </>
      ) : (
        <ReviewCard review={review} />
      )}
    </div>
  );
};

export default ReviewDetailPage;
