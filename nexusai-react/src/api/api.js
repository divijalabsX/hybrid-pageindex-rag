import axios from "axios";

// Point this at wherever `uvicorn main:app --reload` is running.
// Change to your deployed URL later (e.g. via a .env file + import.meta.env).
export const BASE_URL = "http://localhost:8000";

const client = axios.create({
  baseURL: BASE_URL,
});

// ---- Upload ----
export async function uploadDocument(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await client.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded * 100) / evt.total));
      }
    },
  });
  return res.data;
}

// ---- Build index (parse + index step) ----
export async function buildIndex(payload) {
  const res = await client.post("/build-index", payload);
  return res.data;
}

// ---- OKF generation ----
export async function generateOKF(payload) {
  const res = await client.post("/generate-okf", payload);
  return res.data;
}

export async function listOKFFiles() {
  const res = await client.get("/okf-files");
  return res.data;
}

// ---- Documents / page-index (status list) ----
export async function getPageIndex() {
  const res = await client.get("/page-index");
  return res.data;
}

// ---- Ask / chat ----
// NOTE: the backend declares `async def ask_question(question: str)` with no
// Pydantic model, so FastAPI treats `question` as a QUERY parameter, not a
// JSON body field. Sending it as a body causes a 422 Unprocessable Entity.
export async function askQuestion(question) {
  const res = await client.post("/ask", null, { params: { question } });
  return res.data;
}

// ---- Derived status ----
// The backend doesn't expose a dedicated "document status" endpoint (it
// tracks a single in-memory "current document" via globals). We infer
// workspace progress by probing the two read endpoints that already exist.
export async function getWorkspaceStatus() {
  const [indexResult, okfResult] = await Promise.allSettled([
    getPageIndex(),
    listOKFFiles(),
  ]);

  const index =
    indexResult.status === "fulfilled" && !indexResult.value?.error
      ? indexResult.value.index
      : null;

  const okfFiles =
    okfResult.status === "fulfilled" && !okfResult.value?.error
      ? okfResult.value.files ?? []
      : [];

  return { index, okfFiles };
}

export default client;
