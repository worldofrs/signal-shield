const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function protectAudio(file: File): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1/protect`, {
      method: "POST",
      body: formData,
      // Do NOT set Content-Type header — browser sets it automatically
      // with the correct multipart boundary string
    });
  } catch {
    throw new Error(
      "Could not reach the server. It may be starting up — please wait a moment and try again."
    );
  }

  if (!response.ok) {
    if (response.status === 502 || response.status === 504) {
      throw new Error(
        "The server timed out processing your file. Try a shorter audio clip or try again later."
      );
    }
    const error = await response.json().catch(() => ({ detail: `Server error (${response.status})` }));
    throw new Error(error.detail);
  }

  return response.blob();
}
