"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const useAuthGuard = () => {
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        router.push("/signIn");
        return;
      }

      try {
        const res = await fetch("http://10.10.229.93:8009/verify", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        // Check if token is invalid
        if (data.detail === "Invalid token" || data === false) {
          router.push("/signIn");
        }
      } catch (error) {
        console.error("Auth check failed:", error);
        router.push("/signIn");
      }
    };

    checkAuth();
  }, [router]);
};

export default useAuthGuard;
