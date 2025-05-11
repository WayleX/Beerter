"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation"; // Import useRouter for redirection
import ReviewCard, { Review } from "@/components/ReviewCard/ReviewCard";
import Header from "@/components/Header/Header";
import useAuthGuard from "@/hooks/checker/hook";

const DashboardPage: React.FC = () => {
  useAuthGuard();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [nickname, setNickname] = useState<string>("");
  const router = useRouter(); // Initialize router

  useEffect(() => {
    verifyToken();
    fetchUserReviews();
  }, []);

  const verifyToken = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("Token not found in localStorage");

      const res = await fetch("http://10.10.229.93:8009/verify", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setNickname(data.nickname);
    } catch (err) {
      console.error(err);
      setNickname("Verification failed");
    }
  };

  const fetchUserReviews = async () => {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("Token not found in localStorage");

      const res = await fetch("http://10.10.229.93:8009/get_reviews_by_user", {
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

  const logout = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("Token not found in localStorage");

      const res = await fetch("http://10.10.229.93:8009/logout", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      localStorage.removeItem("token"); // Remove token from localStorage
      router.push("/signIn"); // Redirect to /signIn
    } catch (err) {
      console.error(err);
      setError("Failed to log out. Check console for details.");
    }
  };

  return (
    <div>
      <Header />
      <div className="max-w-xl mx-auto font-sans px-4">
        {nickname && (
          <div className="font-bold text-6xl mb-4 text-center">
            Welcome, {nickname}!
          </div>
        )}
        <button
          onClick={logout}
          className="bg-red-500 text-white px-4 py-2 rounded mb-6"
        >
          Logout
        </button>
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
    </div>
  );
};

export default DashboardPage;
