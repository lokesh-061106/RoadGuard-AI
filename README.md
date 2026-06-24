# RoadGuard AI: Citizen-Powered Infrastructure Intelligence & Civic Rewards Agent Platform

**RoadGuard AI** is an AI-powered smart city governance platform developed as a portfolio-grade Kaggle × Google Capstone project. It enables citizens to report infrastructure failures (potholes, dark streetlights, clogged drains) and get rewarded with civic points while a multi-agent system assesses risks, logs dispatches, and updates city-level dashboards.

---

## 🛠️ Multi-Agent Architecture
RoadGuard AI operates a 6-agent workflow built on top of Gemini models:
1. **Infrastructure Detection Agent (AI Inspector)**: Analyzes reported descriptions and images to identify hazard types and severities.
2. **Risk Assessment Agent (Public Safety Officer)**: Invokes MCP tools to determine local traffic density, school zone proximity, and accident history to compile a 0-100 hazard index.
3. **Repair Recommendation Agent (Engineering Advisor)**: Formulates repair blueprints, estimates repair costs, and determines labor timelines.
4. **Government Assistance Agent (Public Works Coordinator)**: Generates work orders and registers incidents with municipal departments.
5. **Civic Rewards Agent (Rewards Evaluator)**: Triggers duplicate report checks to prevent spam, allocates points (up to 100 per report), and awards milestone badges.
6. **Governance Analytics Agent (Smart Governance Agent)**: Refreshes aggregated data feeds, predicting degradation budgets and hotspot weights.

---

## 🔗 Model Context Protocol (MCP) Server
Exposes 9 tools to the agents:
* `get_location_context(lat, lon)`: Returns traffic, school zone, and population conditions.
* `save_incident(incident_data)`: Saves incident details into the JSON database registry.
* `get_incident_registry()`: Returns all logged incidents.
* `award_reward_points(user_id, points, reason)`: Appends reward ledger points and evaluates badge thresholds.
* `get_user_rewards(user_id)`: Fetches active balances and history.
* `generate_city_analytics()`: Synthesizes risk reports and expenditures.
* `get_leaderboard()`: Retrieves rank list.
* `detect_duplicate_reports(lat, lon, damage_type)`: Scans for nearby duplicates (within 50 meters).
* `generate_monthly_report()`: Generates markdown briefings.

---

## 🚀 How to Connect this Project to GitHub

To upload this completed project to your personal GitHub account, execute the following commands in your shell:

1. **Initialize Git**:
   ```bash
   git init
   ```

2. **Add all files**:
   ```bash
   git add .
   ```

3. **Commit the changes**:
   ```bash
   git commit -m "feat: complete roadguard ai capstone platform"
   ```

4. **Link to your GitHub Repository**:
   * Create a new repository named `RoadGuardAI` on your GitHub dashboard (e.g., [github.com/new](https://github.com/new)).
   * Link your local repository to the remote origin:
     ```bash
     git branch -M main
     git remote add origin https://github.com/YOUR_GITHUB_USERNAME/RoadGuardAI.git
     ```

5. **Push code to GitHub**:
     ```bash
     git push -u origin main
     ```

---

## 🌐 How to Get a Publicly Usable Live App Link

You can host this self-contained Python Flask application online for free or low cost:

### Option A: Deploy to Render (Easiest / Free Tier)
1. Sign up/log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New** -> **Web Service**.
3. Select your connected `RoadGuardAI` GitHub repository.
4. Set the configuration details:
   * **Language**: `Python`
   * **Branch**: `main`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `python run.py`
5. In the **Environment Variables** section, add your optional key:
   * `GEMINI_API_KEY` = `your_actual_gemini_api_key`
6. Click **Deploy Web Service**. Render will build your Docker environment and provide a public URL like `https://roadguard-ai.onrender.com`.

### Option B: Deploy to Google Cloud Run (Enterprise-Grade)
1. Install Google Cloud SDK and authenticate:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
2. Build the Docker container using Google Cloud Build:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/roadguard-ai
   ```
3. Deploy the container to Cloud Run:
   ```bash
   gcloud run deploy roadguard-ai \
     --image gcr.io/YOUR_PROJECT_ID/roadguard-ai \
     --platform managed \
     --allow-unauthenticated \
     --region us-central1 \
     --set-env-vars="GEMINI_API_KEY=your_gemini_key"
   ```
4. Once completed, Google Cloud Run will display a secure, scalable HTTPS public direct link.

---

## 💻 Local Setup & Execution

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables (Optional)**:
   ```bash
   # On Windows (PowerShell)
   $env:GEMINI_API_KEY="your_api_key_here"

   # On Linux/macOS
   export GEMINI_API_KEY="your_api_key_here"
   ```

3. **Launch the platform**:
   ```bash
   python run.py
   ```
4. Open your browser and navigate to: **`http://localhost:5000`**

---

## 📂 Database Schema Files
Database operations are committed to local JSON files under `backend/db/`:
* `users.json`: Credentials, roles (`citizen`, `authority`, `admin`), points.
* `incidents.json`: Full analytical logs, GPS coordinates, and media paths.
* `rewards.json`: Transaction ledger for earned/redeemed points.
* `workorders.json`: Dispatch summaries and crew logs.
* `leaderboard.json`: Cached rank list.
* `analytics.json`: Aggregated metrics.

---
*RoadGuard AI is developed in Planning Mode on the Antigravity framework.*
