# Tracker — React + Vite Frontend

Modern, high-performance activity and productivity dashboard powered by React, Vite, React Router, and Axios.

## Getting Started

### 1. Install Dependencies
```bash
cd c:\TRACKER\tracker-phase1-backend\frontend
npm install
```

### 2. Start Vite Dev Server
```bash
npm run dev
```
The frontend will start on **http://localhost:5173**.

### 3. Ensure Backend is Running
In another terminal:
```bash
cd c:\TRACKER\tracker-phase1-backend\backend
uvicorn app.main:app --reload
```
The FastAPI backend runs on **http://localhost:8000**.

---

## Architecture & Features

- **JWT Auth Flow**:
  - `POST /auth/login` and `POST /auth/signup`
  - JWT token persisted in `localStorage`
  - AuthContext provides reactive user state
- **Shared Axios Client (`src/api/client.js`)**:
  - Automatically attaches `Authorization: Bearer <token>`
  - Automatically intercepts `401 Unauthorized` and redirects to `/login`
- **Dashboard Shell (`src/pages/DashboardPage.jsx`)**:
  - Fetches live data from `GET /dashboard/summary`, `/dashboard/apps`, `/dashboard/browser`, `/dashboard/youtube`
  - Supports live time range filtering: `today`, `7d`, `30d`, `all`
  - Visual progress bars for application usage (Chrome, VS Code, Slack, etc.)
  - Domain visit lists and YouTube video history
- **Privacy Settings (`src/pages/SettingsPage.jsx`)**:
  - Toggles App Tracking, Browser Tracking, and YouTube Tracking via `GET /track/permissions` and `PUT /track/permissions`
