const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function protectAudio(file: File): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/api/v1/protect`, {
    method: "POST",
    body: formData,
    // Do NOT set Content-Type header — browser sets it automatically
    // with the correct multipart boundary string
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail);
  }

  return response.blob();
}
