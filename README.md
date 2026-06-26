# GitHub Repository QA Bot

An AI-powered interactive chat assistant designed to help developers explore, analyze, and query any public GitHub repository. With a fully responsive React dashboard and a stateless FastAPI backend, users can index codebases, visualize structure using the **Code Inspector**, and stream code analysis answers dynamically.

---

## 🏗️ Architecture & Data Flow

The application is built using a modern, stateless architecture. Session storage is managed in a managed Postgres database, while repository file caches, hashes, and structural graphs are stored in S3-compatible cloud object storage.

```mermaid
graph TD
    User([User Device]) -->|HTTPS / WSS| Frontend[Vite React Frontend]
    Frontend -->|API Requests| Backend[FastAPI Backend]
    Backend -->|Auth & User Accounts| Database[(Neon Postgres Database)]
    Backend -->|ZIP Archives & Graphs| S3Store[(Backblaze B2 / Cloudflare R2)]
    Backend -->|LLM Chat Queries| LLM[Gemini / OpenRouter API]
    Backend -->|Fetch Repository ZIP| GitHub[GitHub API]
```

* **Frontend**: Built using React, Vite, and custom Vanilla CSS with a premium Obsidian Purple glassmorphism style. It is fully responsive on mobile, tablet, and desktop viewports.
* **Backend**: Powered by FastAPI and Uvicorn, handling repository downloads, dependency graph mapping, code analysis, and user credentials.
* **Database**: Neon Serverless Postgres running SQLAlchemy to persist secure user accounts.
* **Cloud Storage**: Backblaze B2 (or Cloudflare R2) storing cached codebase archives, keeping the backend completely stateless and free of local disk dependency.

---

## 📁 Repository Structure

```
├── .github/workflows/      # Automated deployment GitHub Actions
├── frontend/               # React Frontend Dashboard
│   ├── src/
│   │   ├── App.jsx         # Main UI component with sidebar, chat, and inspector
│   │   ├── index.css       # Obsidian Purple design system and mobile media queries
│   │   └── api.js          # API client for authentication and streaming
│   ├── index.html          # Viewport meta tags
│   └── package.json        # Vite React dependencies
├── github_qa_bot/          # FastAPI Backend Server
│   ├── cache/              # Caching mechanisms for repository states
│   ├── graph/              # Codebase dependency mapping tools
│   ├── tools/              # GitHub archiving, indexing, and vector storage tools
│   ├── utils/              # S3 connection and storage utility modules
│   ├── config.py           # Environment variables loader
│   ├── main.py             # FastAPI entry point, CORS settings, and routes
│   └── requirements.txt    # Python dependencies
├── Dockerfile              # Docker configuration for backend deployments
├── DEPLOYMENT.md           # Backend deployment instructions
└── README.md               # Main project manual (This file)
```

---

## 📱 Features

1. **All-Device Responsiveness**: The interface scales gracefully across mobile, tablet, and desktop screens.
2. **Drawer Overlays**: Sidebar options and the Code Inspector automatically convert to floating drawers with blurred dark backdrops on screens narrower than `1024px`.
3. **Auto-Collapse UX**: Tapping the sidebar backdrop or submitting a question automatically collapses overlays so you can see responses instantly.
4. **Code Inspector**: A vertical panel listing all repository files in an interactive folder tree. View any file's code directly inside the web browser and click "Ask About File" to query it.
5. **Streaming Chat Bubbles**: Markdown responses stream line-by-line using Server-Sent Events (SSE).

---

## 📸 App Screenshots

### 1. Chat Interface & Repository Indexing
![Chat Interface](assets/chat_interface.png)

### 2. Code Inspector Tree
The Code Inspector lets you explore the file tree layout of your repo on the right-hand panel.
![Code Inspector](assets/code_inspector.png)

### 3. Integrated Code Viewer
View any source file directly inside the browser and ask specific questions about it.
![Code Viewer](assets/code_viewer.png)

### 4. Maximized Chat View (Collapsed Sidebar)
Collapse the configuration panel to get a wider view of the conversation stream.
![Maximized Chat View](assets/chat_collapsed_view.png)

---

## 🚀 Local Setup Guide

### 1. Backend Configuration
1. Navigate to the backend directory:
   ```bash
   cd github_qa_bot
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `github_qa_bot/` directory:
   ```env
   DATABASE_URL=postgresql://user:password@host/dbname
   GEMINI_API_KEY=your-gemini-key
   
   # Optional: S3 Object Storage (e.g. Backblaze B2)
   S3_ENDPOINT_URL=https://s3.region.backblazeb2.com
   R2_ACCESS_KEY_ID=your-keyID
   R2_SECRET_ACCESS_KEY=your-applicationKey
   R2_BUCKET_NAME=your-bucket-name
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend will be running at `http://localhost:8000`.

### 2. Frontend Configuration
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `frontend/` directory:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
4. Run the local Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will be running at `http://localhost:5173`.

---

## 🌐 Production Deployment

### Backend (Render / Docker)
The backend is configured to build using the root [Dockerfile](file:///c:/Users/lokes/OneDrive/Desktop/full_start/Dockerfile). Refer to [DEPLOYMENT.md](file:///c:/Users/lokes/OneDrive/Desktop/full_start/DEPLOYMENT.md) for a detailed walkthrough on setting up database connections, environment variables, health checks, and deploying to **Render**.

### Frontend (Vercel)
Deploy the `frontend/` directory directly to **Vercel**:
* **Framework Preset**: `Vite`
* **Root Directory**: `frontend`
* **Build Command**: `npm run build`
* **Output Directory**: `dist`
* **Environment Variables**: Set `VITE_API_URL` to your production backend URL.

### 🤖 CI/CD Workflow (GitHub Actions)
The repository includes an automated GitHub Actions deployment workflow at [.github/workflows/deploy.yml](file:///c:/Users/lokes/OneDrive/Desktop/full_start/.github/workflows/deploy.yml).

Whenever code is pushed to the `main` branch, the runner:
1. Triggers the **Render** backend deployment.
2. Polls the `/health` endpoint up to 5 minutes to verify the service started successfully and passes health checks.
3. Triggers the frontend deployment hook.

#### Required GitHub Secrets:
To enable automated deployments and keep-alive cron jobs, navigate to **Settings ➡️ Secrets and variables ➡️ Actions** in your GitHub repository and add the following repository secrets:
* `RENDER_BACKEND_DEPLOY_HOOK`: The backend service webhook deploy URL generated by Render.
* `RENDER_BACKEND_HOST`: The domain host of your deployed backend API (e.g. `github-url-qanda.onrender.com`).
* `RENDER_FRONTEND_DEPLOY_HOOK`: The frontend service webhook deploy URL.

### ⏱️ Keep-Alive Cron Job (GitHub Actions)
To prevent the Render Free Tier backend from spinning down due to inactivity (which happens after 15 minutes of zero traffic), the repository includes a keep-alive workflow at [.github/workflows/keep_alive.yml](file:///c:/Users/lokes/OneDrive/Desktop/full_start/.github/workflows/keep_alive.yml).

This workflow automatically pings the backend `/health` endpoint every 10 minutes, keeping the container active and warm 24/7. It requires the `RENDER_BACKEND_HOST` secret to be set in your GitHub repository.


