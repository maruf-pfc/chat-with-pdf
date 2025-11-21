"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AiPageRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.push("/chat");
  }, [router]);
}
