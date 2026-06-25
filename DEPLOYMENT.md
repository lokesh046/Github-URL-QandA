# Deployment Guide

This guide explains how to deploy the **FastAPI Backend** and the **React Frontend** to Render's Free Tier. You can choose to deploy them together (integrated as one service) or separately (two services).

---

## ⚡ Option 1: Separate Deployment (Recommended for scalability)

In this approach, the React frontend is deployed as a **Static Site** (which is extremely fast and free on Render), and the FastAPI backend is deployed as a **Python Web Service**.

### 1. Deploy the Backend (Web Service)
1. Go to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** ➡️ Select **Web Service**.
3. Link your GitHub repository.
4. Set the following configuration:
   * **Name:** `github-qa-backend`
   * **Root Directory:** `github_qa_bot`
   * **Runtime:** `Python`
   * **Instance Type:** `Free`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Go to the **Environment** tab and add the environment variables listed in the configuration section below.

### 2. Deploy the Frontend (Static Site)
1. Go to your Render Dashboard.
2. Click **New +** ➡️ Select **Static Site**.
3. Link your GitHub repository.
4. Set the following configuration:
   * **Name:** `github-qa-frontend`
   * **Root Directory:** `frontend`
   * **Build Command:** `npm run build`
   * **Publish Directory:** `dist`
5. Go to the **Environment** tab and add the following environment variable:
   * `VITE_API_URL`: `https://github-qa-backend.onrender.com` (Your deployed Render backend URL)

### 3. Update Backend CORS Allowed Origins
Once your frontend Static Site is created, copy its URL (e.g., `https://github-qa-frontend.onrender.com`) and update your Backend Environment Variables:
   * Add / update `ALLOWED_ORIGINS`: `https://github-qa-frontend.onrender.com`
   * *This allows the React app to communicate with the FastAPI server without triggering CORS blocking.*

---

## 📦 Option 2: Integrated Deployment (Single Free Service)

In this approach, you compile the React frontend locally, copy the build assets into the backend folder, and deploy a single Python service that serves both the API and user interface.

### 1. Build Frontend locally
In your project root, run the pre-configured PowerShell script:
```powershell
.\build_frontend.ps1
```
*This compiles the React frontend and copies output files to `github_qa_bot/dist/`.*

### 2. Push to GitHub
```bash
git add .
git commit -m "build: compile frontend assets"
git push
```

### 3. Create Web Service on Render
1. Go to your Render Dashboard ➡️ click **New +** ➡️ select **Web Service**.
2. Link your GitHub repository.
3. Configure:
   * **Name:** `github-qa-bot`
   * **Root Directory:** `github_qa_bot`
   * **Runtime:** `Python`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add all configuration variables in the **Environment** tab.

---

## 🔑 Backend Environment Variables (Configured on Render)

Add these variables to your Render Backend Service:

| Key | Description |
| :--- | :--- |
| `ENVIRONMENT` | Set to `production`. |
| `JWT_SECRET_KEY` | Generate a secure, random 32-character string. |
| `ALLOWED_ORIGINS` | `https://your-frontend.onrender.com` (Needed for Option 1 separate deploy). |
| `GITHUB_TOKEN_KEY` | Your GitHub Personal Access Token (PAT). |
| `GEMINI_API_KEY` | Your Google Gemini API Key. |
| `OPENROUTER_API_KEY` | Your OpenRouter API Key. |
| `PINECONE_API_KEY` | Your Pinecone API Key. |
| `PINECONE_INDEX_NAME` | Your Pinecone Vector Database Index Name. |
| `DATABASE_URL` | Neon Postgres Connection String (for chat database checks). |
| `S3_ENDPOINT_URL` | `https://s3.us-east-005.backblazeb2.com` (Your B2 Endpoint URL). |
| `R2_ACCESS_KEY_ID` | Your Backblaze keyID. |
| `R2_SECRET_ACCESS_KEY` | Your Backblaze applicationKey. |
| `R2_BUCKET_NAME` | `github-qa-bot-storage`. |
