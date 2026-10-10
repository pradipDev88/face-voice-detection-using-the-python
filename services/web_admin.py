"""
Mr. Beast AI — Zero-Dependency Web Admin Dashboard
Built using Python's standard library `http.server`.
Runs on http://localhost:8080 without requiring Flask or external web frameworks.
Provides complete visual management for:
- User Profiles (CRUD, Search, Photo Preview, Export)
- Multi-Turn Conversation Logs
- Registration State Machine Sessions
- Durable Offline Sync Queue & Manual Flush
- Real-Time System Health & Diagnostics
"""
import os
import sys
import json
import time
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

from services.admin_service import AdminService

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAPTURES_DIR = os.path.join(PROJECT_ROOT, "captures")


class WebAdminHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Mr. Beast Web Admin Dashboard"""

    admin_service: AdminService = None

    def log_message(self, format, *args):
        # Keep console output concise
        if self.path.startswith("/api/") or self.path == "/":
            sys.stdout.write(f"[WebAdmin] {self.command} {self.path} - {args[1]}\n")
            sys.stdout.flush()

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_str: str, status: int = 200):
        body = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: str, mime_type: str = "image/jpeg"):
        if not os.path.exists(file_path):
            self.send_error(404, "File Not Found")
            return
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Main Dashboard Web Page
        if path == "/" or path == "/index.html":
            self._send_html(HTML_TEMPLATE)
            return

        # 2. Serve Captured Profile Photos
        if path.startswith("/captures/"):
            filename = os.path.basename(path)
            safe_path = os.path.join(CAPTURES_DIR, filename)
            # Prevent path traversal
            if os.path.commonpath([CAPTURES_DIR, safe_path]) == CAPTURES_DIR and os.path.exists(safe_path):
                self._send_file(safe_path, "image/jpeg")
            else:
                self.send_error(404, "Photo not found")
            return

        # 3. REST API Endpoints
        if path == "/api/stats":
            stats = self.admin_service.get_overview_stats()
            self._send_json(stats)
            return

        if path == "/api/users":
            search_q = query.get("q", [None])[0]
            users = self.admin_service.get_all_users(search_query=search_q)
            self._send_json(users)
            return

        if path == "/api/conversations":
            limit = int(query.get("limit", [100])[0])
            speaker = query.get("speaker", [None])[0]
            logs = self.admin_service.get_conversation_logs(limit=limit, speaker=speaker)
            self._send_json(logs)
            return

        if path == "/api/sessions":
            limit = int(query.get("limit", [50])[0])
            sessions = self.admin_service.get_registration_sessions(limit=limit)
            self._send_json(sessions)
            return

        if path == "/api/sync-queue":
            queue_items = self.admin_service.get_sync_queue()
            self._send_json(queue_items)
            return

        if path == "/api/diagnostics":
            diag = self.admin_service.health_service.check_health()
            self._send_json(diag)
            return

        if path == "/api/export":
            export_data = self.admin_service.export_all_data()
            self._send_json(export_data)
            return

        self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Read JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if path == "/api/users":
            res = self.admin_service.save_user(payload)
            self._send_json({"success": bool(res), "profile": res})
            return

        if path == "/api/users/delete":
            user_id = payload.get("id") or payload.get("name")
            if not user_id:
                self._send_json({"success": False, "error": "User ID or name required"}, 400)
                return
            success = self.admin_service.delete_user(user_id)
            self._send_json({"success": success, "deleted_id": user_id})
            return

        if path == "/api/sync/trigger":
            result = self.admin_service.trigger_sync()
            self._send_json({"success": True, "result": result})
            return

        self.send_error(404, "Endpoint Not Found")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/users/"):
            user_id = path.replace("/api/users/", "").strip()
            success = self.admin_service.delete_user(user_id)
            self._send_json({"success": success, "deleted_id": user_id})
            return
        self.send_error(404, "Endpoint Not Found")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🛡️ Mr. Beast AI — Web Admin Dashboard</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-hover: #26354a;
      --border: #334155;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #8b5cf6;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: #1e293b;
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .header-brand h1 {
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.025em;
    }
    .header-brand span {
      font-size: 0.8rem;
      color: var(--text-muted);
      background: #0f172a;
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid var(--border);
    }
    .telemetry-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      padding: 20px 24px 0 24px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 18px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .stat-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 600;
      color: var(--text-muted);
    }
    .stat-val {
      font-size: 1.5rem;
      font-weight: 700;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .badge-success { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #059669; }
    .badge-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #d97706; }
    .badge-danger  { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #dc2626; }

    /* Nav Tabs */
    .tabs-nav {
      display: flex;
      gap: 8px;
      padding: 16px 24px;
      border-bottom: 1px solid var(--border);
      background: #131d2e;
    }
    .tab-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s ease;
    }
    .tab-btn:hover {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
    }
    .tab-btn.active {
      background: var(--primary);
      color: white;
      border-color: var(--primary);
    }

    /* Content Area */
    main {
      flex: 1;
      padding: 20px 24px;
    }
    .tab-panel {
      display: none;
    }
    .tab-panel.active {
      display: block;
    }

    /* Toolbar */
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      gap: 12px;
      flex-wrap: wrap;
    }
    .search-input {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 0.9rem;
      width: 280px;
      outline: none;
    }
    .search-input:focus { border-color: var(--primary); }
    .btn {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn:hover { background: var(--card-hover); }
    .btn-primary { background: var(--primary); border-color: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-accent { background: var(--accent); border-color: var(--accent); color: white; }
    .btn-danger { background: var(--danger); border-color: var(--danger); color: white; }

    /* Tables */
    .table-container {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow-x: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.875rem;
    }
    th {
      background: #172033;
      color: var(--text-muted);
      text-transform: uppercase;
      font-size: 0.72rem;
      letter-spacing: 0.05em;
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      color: var(--text);
    }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255, 255, 255, 0.02); }

    .avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      object-fit: cover;
      background: #334155;
      display: inline-block;
      vertical-align: middle;
      border: 1px solid var(--border);
    }

    /* Modal */
    .modal-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 200;
    }
    .modal-overlay.active { display: flex; }
    .modal {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      width: 90%;
      max-width: 540px;
      max-height: 90vh;
      overflow-y: auto;
      padding: 24px;
    }
    .modal-title { font-size: 1.2rem; font-weight: 700; margin-bottom: 16px; }
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 4px; font-weight: 600; }
    .form-control {
      width: 100%;
      background: #0f172a;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.9rem;
      outline: none;
    }
    .form-control:focus { border-color: var(--primary); }
    .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }

    pre.code-view {
      background: #0f172a;
      border: 1px solid var(--border);
      padding: 14px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 0.8rem;
      color: #38bdf8;
      max-height: 400px;
      overflow-y: auto;
    }
  </style>
</head>
<body>

  <!-- Top Header -->
  <header>
    <div class="header-brand">
      <h1>🛡️ Mr. Beast AI Admin Dashboard</h1>
      <span>v2.0 Master Console</span>
    </div>
    <div style="display: flex; gap: 10px; align-items: center;">
      <button class="btn btn-accent" onclick="triggerSyncNow()">🔄 Sync to MySQL Now</button>
      <button class="btn" onclick="exportDataJSON()">📥 Export JSON</button>
      <button class="btn" onclick="refreshCurrentTab()">↻ Refresh</button>
    </div>
  </header>

  <!-- Telemetry Bar -->
  <div class="telemetry-row">
    <div class="stat-card">
      <span class="stat-label">Registered Users</span>
      <span class="stat-val" id="statUsers">--</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Conversations Logged</span>
      <span class="stat-val" id="statConvos">--</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">Pending Sync Queue</span>
      <span class="stat-val" id="statSyncQ">--</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">MySQL Connection</span>
      <span class="stat-val" id="statDB">Checking</span>
    </div>
    <div class="stat-card">
      <span class="stat-label">AI Engine</span>
      <span class="stat-val" id="statAI" style="font-size: 1.1rem; padding-top: 4px;">--</span>
    </div>
  </div>

  <!-- Navigation Tabs -->
  <div class="tabs-nav">
    <button class="tab-btn active" onclick="switchTab('users')">👥 User Profiles</button>
    <button class="tab-btn" onclick="switchTab('convos')">💬 Conversation History</button>
    <button class="tab-btn" onclick="switchTab('sessions')">📋 Registration Sessions</button>
    <button class="tab-btn" onclick="switchTab('sync')">🔄 Offline Queue & Health</button>
  </div>

  <!-- Main Content -->
  <main>
    <!-- TAB 1: USERS -->
    <div id="tab-users" class="tab-panel active">
      <div class="toolbar">
        <input type="text" id="userSearchInput" class="search-input" placeholder="🔍 Search by name, city, job, email..." oninput="filterUsers()">
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-primary" onclick="openAddUserModal()">+ Add New User</button>
        </div>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Photo</th>
              <th>ID</th>
              <th>Full Name</th>
              <th>Age</th>
              <th>Gender</th>
              <th>Job / College</th>
              <th>City / Address</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="usersTableBody">
            <tr><td colspan="11" style="text-align: center; color: var(--text-muted);">Loading profiles...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 2: CONVERSATIONS -->
    <div id="tab-convos" class="tab-panel">
      <div class="toolbar">
        <div style="display: flex; gap: 8px; align-items: center;">
          <label style="font-size: 0.85rem; color: var(--text-muted);">Speaker:</label>
          <select id="convoSpeakerFilter" class="form-control" style="width: 140px;" onchange="loadConversations()">
            <option value="All">All Speakers</option>
            <option value="User">User Only</option>
            <option value="Robot">Robot Only</option>
          </select>
        </div>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Speaker</th>
              <th>Message Utterance</th>
              <th>Lang</th>
              <th>Intent</th>
              <th>Confidence</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody id="convosTableBody">
            <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading conversation history...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 3: SESSIONS -->
    <div id="tab-sessions" class="tab-panel">
      <div class="toolbar">
        <span style="font-size: 0.85rem; color: var(--text-muted);">Stateful interactive registration sessions tracked across turns</span>
      </div>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Session ID</th>
              <th>User ID</th>
              <th>Language</th>
              <th>Current State</th>
              <th>Status</th>
              <th>Confirmed</th>
              <th>Updated At</th>
              <th>Collected Data</th>
            </tr>
          </thead>
          <tbody id="sessionsTableBody">
            <tr><td colspan="8" style="text-align: center; color: var(--text-muted);">Loading sessions...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 4: SYNC & HEALTH -->
    <div id="tab-sync" class="tab-panel">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div>
          <div class="toolbar">
            <h3 style="font-size: 1rem; font-weight: 600;">🔄 Durable Offline Sync Queue</h3>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>UUID</th>
                  <th>Entity</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Retries</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody id="syncQueueTableBody">
                <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Queue is empty</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <div class="toolbar">
            <h3 style="font-size: 1rem; font-weight: 600;">🩺 System Diagnostic Telemetry</h3>
            <button class="btn" onclick="loadDiagnostics()">Refresh Health</button>
          </div>
          <pre id="diagJson" class="code-view">Checking component telemetry...</pre>
        </div>
      </div>
    </div>
  </main>

  <!-- USER MODAL (ADD / EDIT) -->
  <div id="userModal" class="modal-overlay">
    <div class="modal">
      <h2 id="modalTitle" class="modal-title">Add User Profile</h2>
      <form id="userForm" onsubmit="saveUserForm(event)">
        <input type="hidden" id="formUserId">
        <div class="form-group">
          <label>Full Name *</label>
          <input type="text" id="formName" class="form-control" required placeholder="e.g. Ashish Ojha">
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
          <div class="form-group">
            <label>Age</label>
            <input type="text" id="formAge" class="form-control" placeholder="e.g. 25">
          </div>
          <div class="form-group">
            <label>Gender</label>
            <select id="formGender" class="form-control">
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>Job / College</label>
          <input type="text" id="formJob" class="form-control" placeholder="e.g. Software Engineer">
        </div>
        <div class="form-group">
          <label>Address / City</label>
          <input type="text" id="formAddress" class="form-control" placeholder="e.g. Delhi, India">
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="formEmail" class="form-control" placeholder="name@example.com">
          </div>
          <div class="form-group">
            <label>Phone</label>
            <input type="text" id="formPhone" class="form-control" placeholder="+91 9876543210">
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn" onclick="closeUserModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Profile</button>
        </div>
      </form>
    </div>
  </div>

  <!-- INSPECT JSON MODAL -->
  <div id="inspectModal" class="modal-overlay">
    <div class="modal" style="max-width: 650px;">
      <h2 class="modal-title">Inspect Session Payload</h2>
      <pre id="inspectJsonContent" class="code-view" style="max-height: 450px;"></pre>
      <div class="modal-actions">
        <button class="btn btn-primary" onclick="closeInspectModal()">Close</button>
      </div>
    </div>
  </div>

  <script>
    let currentTab = 'users';
    let cachedUsers = [];

    async function loadStats() {
      try {
        const res = await fetch('/api/stats');
        const s = await res.json();
        document.getElementById('statUsers').innerText = s.total_users ?? 0;
        document.getElementById('statConvos').innerText = s.total_conversations ?? 0;
        document.getElementById('statSyncQ').innerText = s.pending_sync ?? 0;
        
        const dbBadge = document.getElementById('statDB');
        if (s.db_connected) {
          dbBadge.innerHTML = `<span class="badge badge-success">Online (${s.db_latency_ms}ms)</span>`;
        } else {
          dbBadge.innerHTML = `<span class="badge badge-warning">Offline (Fallback)</span>`;
        }

        document.getElementById('statAI').innerText = s.ai_provider || 'Local Brain';
      } catch (e) {
        console.error('Stats error:', e);
      }
    }

    async function loadUsers() {
      try {
        const res = await fetch('/api/users');
        cachedUsers = await res.json();
        renderUsers(cachedUsers);
      } catch (e) {
        console.error('Load users error:', e);
      }
    }

    function renderUsers(users) {
      const tbody = document.getElementById('usersTableBody');
      if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;color:var(--text-muted);">No profiles found</td></tr>';
        return;
      }
      tbody.innerHTML = users.map(u => {
        const photoUrl = u.photo_path && u.photo_path.trim() ? '/' + u.photo_path : '';
        const imgTag = photoUrl 
          ? `<img src="${photoUrl}" class="avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(u.name)}&background=334155&color=fff'">` 
          : `<img src="https://ui-avatars.com/api/?name=${encodeURIComponent(u.name)}&background=334155&color=fff" class="avatar">`;
        
        const syncBadge = u.sync_status === 'synced' 
          ? '<span class="badge badge-success">Synced</span>' 
          : '<span class="badge badge-warning">Pending</span>';

        return `
          <tr>
            <td>${imgTag}</td>
            <td><strong>#${u.id}</strong></td>
            <td><strong>${escapeHtml(u.name)}</strong></td>
            <td>${escapeHtml(u.age || '--')}</td>
            <td>${escapeHtml(u.gender || '--')}</td>
            <td>${escapeHtml(u.college_or_job || '--')}</td>
            <td>${escapeHtml(u.address || '--')}</td>
            <td>${escapeHtml(u.email || '--')}</td>
            <td>${escapeHtml(u.phone || '--')}</td>
            <td>${syncBadge}</td>
            <td>
              <div style="display:flex;gap:6px;">
                <button class="btn" style="padding:4px 8px;font-size:0.75rem;" onclick="openEditUserModal(${u.id})">✏️</button>
                <button class="btn btn-danger" style="padding:4px 8px;font-size:0.75rem;" onclick="deleteUserConfirm(${u.id}, '${escapeHtml(u.name)}')">🗑️</button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    function filterUsers() {
      const q = document.getElementById('userSearchInput').value.toLowerCase().trim();
      if (!q) {
        renderUsers(cachedUsers);
        return;
      }
      const filtered = cachedUsers.filter(u => 
        (u.name && u.name.toLowerCase().includes(q)) ||
        (u.address && u.address.toLowerCase().includes(q)) ||
        (u.college_or_job && u.college_or_job.toLowerCase().includes(q)) ||
        (u.email && u.email.toLowerCase().includes(q)) ||
        (u.phone && u.phone.toLowerCase().includes(q))
      );
      renderUsers(filtered);
    }

    async function loadConversations() {
      const speaker = document.getElementById('convoSpeakerFilter').value;
      try {
        const res = await fetch(`/api/conversations?limit=100&speaker=${encodeURIComponent(speaker)}`);
        const logs = await res.json();
        const tbody = document.getElementById('convosTableBody');
        if (!logs || logs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">No conversation logs recorded yet</td></tr>';
          return;
        }
        tbody.innerHTML = logs.map(l => {
          const spBadge = l.speaker === 'User' ? '<span class="badge badge-success">User</span>' : '<span class="badge" style="background:#4338ca;color:#c7d2fe;">Robot</span>';
          return `
            <tr>
              <td>#${l.log_id || '--'}</td>
              <td>${spBadge}</td>
              <td style="max-width:350px;">${escapeHtml(l.message)}</td>
              <td>${escapeHtml(l.language || 'en')}</td>
              <td><code>${escapeHtml(l.intent || '--')}</code></td>
              <td>${l.confidence ?? 0}</td>
              <td style="font-size:0.78rem;color:var(--text-muted);">${escapeHtml(l.timestamp)}</td>
            </tr>
          `;
        }).join('');
      } catch (e) {
        console.error('Convos error:', e);
      }
    }

    async function loadSessions() {
      try {
        const res = await fetch('/api/sessions?limit=50');
        const sessions = await res.json();
        const tbody = document.getElementById('sessionsTableBody');
        if (!sessions || sessions.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted);">No registration sessions found in database</td></tr>';
          return;
        }
        tbody.innerHTML = sessions.map(s => {
          const stBadge = s.status === 'confirmed' || s.status === 'completed' 
            ? '<span class="badge badge-success">Completed</span>'
            : '<span class="badge badge-warning">' + escapeHtml(s.status) + '</span>';
          
          return `
            <tr>
              <td><strong>#${s.session_id}</strong></td>
              <td>${s.user_id || '--'}</td>
              <td>${escapeHtml(s.language || 'en')}</td>
              <td><code>${escapeHtml(s.current_state || '--')}</code></td>
              <td>${stBadge}</td>
              <td>${s.is_confirmed ? '✅ Yes' : '⏳ Pending'}</td>
              <td style="font-size:0.78rem;color:var(--text-muted);">${escapeHtml(s.updated_at)}</td>
              <td>
                <button class="btn" style="padding:4px 8px;font-size:0.75rem;" onclick='inspectSessionData(${JSON.stringify(s.collected_data)})'>🔍 View JSON</button>
              </td>
            </tr>
          `;
        }).join('');
      } catch (e) {
        console.error('Sessions error:', e);
      }
    }

    async function loadSyncQueue() {
      try {
        const res = await fetch('/api/sync-queue');
        const q = await res.json();
        const tbody = document.getElementByIdSync ? document.getElementByIdSync('syncQueueTableBody') : document.getElementById('syncQueueTableBody');
        if (!q || q.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#34d399;">✓ All offline records are synchronized! Queue is empty.</td></tr>';
          return;
        }
        tbody.innerHTML = q.map(item => `
          <tr>
            <td style="font-size:0.75rem;font-family:monospace;">${escapeHtml(item.uuid || '--')}</td>
            <td>${escapeHtml(item.entity_type || '--')}</td>
            <td><span class="badge badge-warning">${escapeHtml(item.action || 'INSERT')}</span></td>
            <td>${escapeHtml(item.status || 'pending')}</td>
            <td>${item.retry_count ?? 0}</td>
            <td style="font-size:0.75rem;color:var(--text-muted);">${escapeHtml(item.created_at || '--')}</td>
          </tr>
        `).join('');
      } catch (e) {
        console.error('Sync queue error:', e);
      }
    }

    async function loadDiagnostics() {
      try {
        const res = await fetch('/api/diagnostics');
        const d = await res.json();
        document.getElementById('diagJson').innerText = JSON.stringify(d, null, 2);
      } catch (e) {
        console.error('Diag error:', e);
      }
    }

    function switchTab(tab) {
      currentTab = tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      
      const targetBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.innerText.toLowerCase().includes(tab));
      if (targetBtn) targetBtn.classList.add('active');
      
      const targetPanel = document.getElementById(`tab-${tab}`);
      if (targetPanel) targetPanel.classList.add('active');

      refreshCurrentTab();
    }

    function refreshCurrentTab() {
      loadStats();
      if (currentTab === 'users') loadUsers();
      else if (currentTab === 'convos') loadConversations();
      else if (currentTab === 'sessions') loadSessions();
      else if (currentTab === 'sync') { loadSyncQueue(); loadDiagnostics(); }
    }

    async function triggerSyncNow() {
      if (!confirm("Trigger immediate synchronization of offline items to MySQL?")) return;
      try {
        const res = await fetch('/api/sync/trigger', { method: 'POST' });
        const data = await res.json();
        alert(`Sync Complete! Synced: ${data.result.synced}, Remaining: ${data.result.failed}`);
        refreshCurrentTab();
      } catch (e) {
        alert('Error triggering sync: ' + e);
      }
    }

    async function exportDataJSON() {
      window.open('/api/export', '_blank');
    }

    function openAddUserModal() {
      document.getElementById('modalTitle').innerText = 'Add User Profile';
      document.getElementById('formUserId').value = '';
      document.getElementById('formName').value = '';
      document.getElementById('formAge').value = '';
      document.getElementById('formGender').value = 'Male';
      document.getElementById('formJob').value = '';
      document.getElementById('formAddress').value = '';
      document.getElementById('formEmail').value = '';
      document.getElementById('formPhone').value = '';
      document.getElementById('userModal').classList.add('active');
    }

    function openEditUserModal(id) {
      const u = cachedUsers.find(x => x.id === id);
      if (!u) return;
      document.getElementById('modalTitle').innerText = `Edit Profile #${u.id}`;
      document.getElementById('formUserId').value = u.id;
      document.getElementById('formName').value = u.name || '';
      document.getElementById('formAge').value = u.age || '';
      document.getElementById('formGender').value = u.gender || 'Male';
      document.getElementById('formJob').value = u.college_or_job || '';
      document.getElementById('formAddress').value = u.address || '';
      document.getElementById('formEmail').value = u.email === '--' ? '' : u.email || '';
      document.getElementById('formPhone').value = u.phone === '--' ? '' : u.phone || '';
      document.getElementById('userModal').classList.add('active');
    }

    function closeUserModal() {
      document.getElementById('userModal').classList.remove('active');
    }

    async function saveUserForm(event) {
      event.preventDefault();
      const id = document.getElementById('formUserId').value;
      const payload = {
        name: document.getElementById('formName').value.trim(),
        age: document.getElementById('formAge').value.trim(),
        gender: document.getElementById('formGender').value,
        college_or_job: document.getElementById('formJob').value.trim(),
        address: document.getElementById('formAddress').value.trim(),
        email: document.getElementById('formEmail').value.trim(),
        phone: document.getElementById('formPhone').value.trim()
      };
      if (id) {
        payload.id = parseInt(id);
      }

      try {
        const res = await fetch('/api/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const d = await res.json();
        if (d.success) {
          closeUserModal();
          loadUsers();
          loadStats();
        } else {
          alert('Error saving profile: ' + (d.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Request failed: ' + e);
      }
    }

    async function deleteUserConfirm(id, name) {
      if (!confirm(`Are you sure you want to permanently delete profile #${id} (${name})?`)) return;
      try {
        const res = await fetch('/api/users/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: id })
        });
        const d = await res.json();
        if (d.success) {
          loadUsers();
          loadStats();
        } else {
          alert('Could not delete user');
        }
      } catch (e) {
        alert('Delete request failed: ' + e);
      }
    }

    function inspectSessionData(raw) {
      let content = '';
      try {
        content = typeof raw === 'string' ? JSON.stringify(JSON.parse(raw), null, 2) : JSON.stringify(raw, null, 2);
      } catch (e) {
        content = String(raw);
      }
      document.getElementById('inspectJsonContent').innerText = content || '{}';
      document.getElementById('inspectModal').classList.add('active');
    }

    function closeInspectModal() {
      document.getElementById('inspectModal').classList.remove('active');
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    // Auto-load on page ready
    window.addEventListener('DOMContentLoaded', () => {
      loadStats();
      loadUsers();
      // Auto-poll stats every 10 seconds
      setInterval(loadStats, 10000);
    });
  </script>
</body>
</html>
"""


def run_web_admin(host: str = "0.0.0.0", port: int = 8080, open_browser: bool = True):
    """Run Web Admin Dashboard HTTP server"""
    handler_class = WebAdminHandler
    handler_class.admin_service = AdminService()
    
    server_address = (host, port)
    httpd = HTTPServer(server_address, handler_class)
    
    local_url = f"http://localhost:{port}"
    print("=" * 64)
    print("🌐 MR. BEAST AI — WEB ADMIN DASHBOARD RUNNING")
    print("=" * 64)
    print(f"👉 Local Access URL: {local_url}")
    print(f"👉 Serving profiles from captures/: {CAPTURES_DIR}")
    print("Zero external web dependencies (pure standard Python http.server)")
    print("Press Ctrl+C to stop server.")
    print("=" * 64 + "\n")

    if open_browser:
        try:
            webbrowser.open(local_url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Web Admin Dashboard stopped. Goodbye!")
        httpd.server_close()


if __name__ == "__main__":
    run_web_admin()
