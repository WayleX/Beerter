import React, { useEffect, useState } from "react";

export interface Review {
  created_at: string;
  headline: string;
  id: string;
  product_id: string;
  rating: number;
  review: string;
  updated_at: string;
  liked: boolean;
}

const ReviewCard: React.FC<{ review: Review }> = ({ review }) => {
  const [liked, setLiked] = useState(review.liked);
  const [error, setError] = useState("");
  useEffect(() => {
    setLiked(review.liked);
  }, [review.liked]);

  const handleLike = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("Token not found");
      return;
    }

    try {
      const res = await fetch(
        `http://localhost:8009/post_like/${review.id}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      const data = await res.json();
      console.log(data);

      if (!res.ok && data?.msg !== "Already liked") {
        throw new Error("Failed to like the review");
      }

      setLiked(true);
      setError("");
      console.log("Like sent successfully");
    } catch (err) {
      console.error(err);
      setError("Could not send like");
    }
  };

  const handleRemoveLike = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("Token not found");
      return;
    }

    try {
      const res = await fetch(
        `http://localhost:8009/post_like/${review.id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!res.ok) {
        throw new Error("Failed to remove like");
      }

      setLiked(false);
      setError("");
      console.log("Like removed successfully");
    } catch (err) {
      console.error(err);
      setError("Could not remove like");
    }
  };

  return (
    <div className="my-10">
      <div className="border rounded p-4 shadow relative">
        <h3 className="text-lg font-semibold mb-2">{review.headline}</h3>
        <p className="mb-2">{review.review}</p>
        <div className="text-sm text-gray-600 mb-1">
          Rating: {review.rating}/5
        </div>
        <div className="text-sm text-gray-600">
          Product ID: {review.product_id}
        </div>
        <div className="text-sm text-gray-600">
          Created At: {new Date(review.created_at).toLocaleString()}
        </div>
      </div>
      <button
        onClick={liked ? handleRemoveLike : handleLike}
        className={`absolute top-4 right-4 text-xl ${
          liked ? "text-red-600" : "text-gray-400"
        } hover:text-red-500 transition`}
        title={liked ? "Remove like" : "Like this review"}
      >
        {liked ? "❤️" : "🤍"}
      </button>

      {error && <div className="text-sm text-red-500 mt-2">{error}</div>}
    </div>
  );
};

export default ReviewCard;
