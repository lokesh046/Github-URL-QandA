# Deploying to Render (Free Tier Guide)

This guide explains how to deploy the combined Python FastAPI backend + React frontend to Render's **Free Tier** as a single native Python web service.

---

## How It Works on the Free Tier:
* **No Docker**: Render's Free Tier does not support custom Docker builds, so we deploy using the native **Python** runtime.
* **No Paid Disks (Ephemeral Caching)**: Render's Free Tier doesn't allow persistent disk mounts. Instead, the application writes the repository ZIPs, SHA indices, and dependency graphs directly to its local directory. This is writable but **ephemeral** (caches reset whenever the server restarts or goes to sleep, which is standard for the free tier).
* **Serving Frontend from Backend**: We compile the React frontend locally, place the compiled files inside the backend folder, and push it to GitHub. The backend then serves both the API and the user interface.

---

## Step 1: Build the Frontend Locally

We have created a helper PowerShell script `build_frontend.ps1` in the project root to automate this:

1. Open PowerShell in your project root directory.
2. Run the script:
   ```powershell
   .\build_frontend.ps1
   ```
   *This compiles the React frontend under `frontend/` and automatically copies the output (`dist/`) into `github_qa_bot/dist/`.*

3. Commit and push the changes to GitHub:
   ```bash
   git add .
   git commit -m "Build and integrate frontend"
   git push
   ```

---

## Step 2: Create the Web Service on Render

1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your Git repository.
4. Set the following configuration:
   * **Name**: `github-qa-bot`
   * **Region**: Choose the one closest to you (e.g., Oregon, Frankfurt)
   * **Branch**: `main` (or your main branch)
   * **Root Directory**: `github_qa_bot`
   * **Runtime**: **Python**
   * **Instance Type**: **Free**

---

## Step 3: Configure Build and Start Commands

Under the configuration section, set:
* **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
* **Start Command**: 
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

---

## Step 4: Configure Environment Variables

Under the **Environment** tab, click **Add Environment Variable** and add the following required credentials:

| Key | Value | Description |
| :--- | :--- | :--- |
| `GITHUB_TOKEN_KEY` | `ghp_...` | Your GitHub Personal Access Token (PAT) |
| `GEMINI_API_KEY` | `AIzaSy...` | Your Gemini API Key |
| `OPENROUTER_API_KEY` | `sk-or-...` | Your OpenRouter API Key |
| `PINECONE_API_KEY` | `pcsk_...` | Your Pinecone API Key |
| `PINECONE_INDEX_NAME` | `your-index` | Your Pinecone index name |
| `DATABASE_URL` | `postgresql://...` | (Optional) Your Neon Postgres database connection URL to enable persistent user chat memory. |

---

## Step 5: Deploy!

Click **Create Web Service**. 
* Render will install the Python dependencies and launch the backend server.
* Because the built frontend is inside the `github_qa_bot/dist` directory, FastAPI will automatically serve the user interface when you visit your Render URL (e.g., `https://github-qa-bot.onrender.com`).
