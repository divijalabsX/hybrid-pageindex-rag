# NexusAI — React frontend

React (Vite) frontend for `hybrid-pageindex-rag`, replacing the earlier
custom HTML/CSS/JS frontend. The FastAPI backend is unchanged — this just
calls it over HTTP.

## 1. Install & run (on your Windows laptop)

```bash
cd nexusai-react
npm install
npm run dev
```

This starts the dev server at **http://localhost:5173**.

Make sure your FastAPI backend is running separately, as before:

```bash
uvicorn main:app --reload
```

(default: **http://localhost:8000** — matches `BASE_URL` in `src/api/api.js`)

## 2. IMPORTANT — enable CORS on the FastAPI backend

Your old frontend was plain HTML served in a way that avoided CORS issues.
React's dev server runs on a **different port** (5173), so the browser will
block API calls unless FastAPI explicitly allows it. Add this to `main.py`,
near the top, before your routes:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Without this, every request from React will fail with a CORS error in the
browser console — this is the #1 thing to check if pages show "Could not
reach the assistant" or similar.

## 3. Project structure

```
src/
  api/api.js          <- all backend calls live here (upload, build-index,
                         generate-okf, okf-files, page-index, ask)
  components/
    Sidebar.jsx        <- left nav
    ChatBar.jsx         <- persistent bottom chat input (all pages)
    Layout.jsx          <- combines Sidebar + page content + ChatBar
  pages/
    UploadPage.jsx      <- drag-drop upload -> /upload -> /build-index
    DocumentsListPage.jsx <- table of docs + status -> /page-index
    OKFPage.jsx         <- generate + browse OKF -> /generate-okf, /okf-files
    ChatPage.jsx        <- full ask/answer history -> /ask
    LoginPage.jsx       <- UI-only placeholder (no backend auth yet)
  App.jsx              <- routes
  main.jsx             <- entry point
  styles/index.css     <- theme (same indigo/cyan palette + Plus Jakarta Sans)
```

## 4. Things to double check against your real backend

The page components make reasonable assumptions about response shapes
(e.g. `/page-index` returning an array of documents with `filename` and
`status`). If your actual endpoints return different field names, the
fastest fix is inside `src/api/api.js` or right where each page reads the
response (`res.data`) — everything is centralized so this should be a
small, localized change per page.

## 5. Login / user CRUD

There's no backend support for this yet (checked — your FastAPI only has
`/upload`, `/build-index`, `/generate-okf`, `/ask`, `/page-index`,
`/okf-files`). `LoginPage.jsx` is a UI-only placeholder. Tell me when
you're ready to add real auth and we'll design the endpoints + wire it up.
