"""
Mr. Beast AI — Desktop Admin Dashboard
Unified graphical control center for viewing and managing:
- User Profiles (CRUD, Search, Photo Preview, Export)
- Multi-Turn Conversation Logs
- Registration State Machine Sessions
- Durable Offline Synchronization Queue
- Live System Diagnostics & Provider Health
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import threading
from datetime import datetime
from PIL import Image, ImageTk
from typing import Optional, Dict, Any, List

from services.admin_service import AdminService


class MrBeastAdminDashboard:
    """Desktop Graphical Administration Console"""

    def __init__(self, parent_or_root=None):
        if parent_or_root is None:
            self.root = tk.Tk()
            self.is_toplevel = False
        else:
            self.root = tk.Toplevel(parent_or_root)
            self.is_toplevel = True

        self.root.title("🛡️ Mr. Beast AI — Administration Console")
        self.root.geometry("1100x720")
        self.root.minsize(950, 600)
        self.root.configure(bg="#ecf0f1")

        self.admin_service = AdminService()
        self.current_selected_user = None
        self.photo_image_tk = None

        self._setup_styles()
        self._build_ui()
        self._load_initial_data()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#ecf0f1')
        style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'), padding=[12, 6])
        style.configure('Treeview', font=('Arial', 9), rowheight=24)
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'), background='#34495e', foreground='white')

    def _build_ui(self):
        # 1. Top Header & Metrics Banner
        header = tk.Frame(self.root, bg="#2c3e50", height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_box = tk.Frame(header, bg="#2c3e50")
        title_box.pack(side=tk.LEFT, padx=20, pady=12)

        tk.Label(
            title_box,
            text="🛡️ Mr. Beast AI Admin Dashboard",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2c3e50"
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Master Data & System Operations Console",
            font=("Arial", 9),
            fg="#bdc3c7",
            bg="#2c3e50"
        ).pack(anchor="w")

        # Metric Badges
        metrics_frame = tk.Frame(header, bg="#2c3e50")
        metrics_frame.pack(side=tk.RIGHT, padx=20, pady=14)

        self.badge_users = self._create_metric_card(metrics_frame, "👥 Users", "--", "#2980b9")
        self.badge_convos = self._create_metric_card(metrics_frame, "💬 Convos", "--", "#8e44ad")
        self.badge_sync = self._create_metric_card(metrics_frame, "🔄 Sync Q", "--", "#e67e22")
        self.badge_db = self._create_metric_card(metrics_frame, "🗄️ Database", "Checking", "#27ae60")

        # 2. Main Tabbed Interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Tab 1: User Profiles
        self.tab_users = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.tab_users, text=" 👥 User Profiles ")
        self._build_users_tab()

        # Tab 2: Conversation Logs
        self.tab_convos = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.tab_convos, text=" 💬 Conversation History ")
        self._build_conversations_tab()

        # Tab 3: Registration Sessions
        self.tab_sessions = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.tab_sessions, text=" 📋 Registration Sessions ")
        self._build_sessions_tab()

        # Tab 4: Durable Sync Queue & Health
        self.tab_sync = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.tab_sync, text=" 🔄 Sync Queue & Health ")
        self._build_sync_tab()

        # 3. Bottom Status Bar
        self.status_bar = tk.Label(
            self.root,
            text="Admin Console ready.",
            font=("Arial", 9),
            bg="#34495e",
            fg="white",
            anchor="w",
            padx=10,
            pady=3
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_metric_card(self, parent, title, val, color):
        card = tk.Frame(parent, bg=color, padx=10, pady=4)
        card.pack(side=tk.LEFT, padx=5)
        tk.Label(card, text=title, font=("Arial", 8, "bold"), fg="white", bg=color).pack()
        val_lbl = tk.Label(card, text=val, font=("Arial", 11, "bold"), fg="white", bg=color)
        val_lbl.pack()
        return val_lbl

    # =========================================================================
    # TAB 1: User Profiles Manager
    # =========================================================================
    def _build_users_tab(self):
        # Top Search & Action Bar
        toolbar = tk.Frame(self.tab_users, bg="#ecf0f1")
        toolbar.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(toolbar, text="🔍 Search:", font=("Arial", 10, "bold"), bg="#ecf0f1").pack(side=tk.LEFT, padx=4)
        self.user_search_var = tk.StringVar()
        search_entry = tk.Entry(toolbar, textvariable=self.user_search_var, font=("Arial", 10), width=25)
        search_entry.pack(side=tk.LEFT, padx=4)
        search_entry.bind("<Return>", lambda e: self.refresh_users())

        tk.Button(toolbar, text="Filter", font=("Arial", 9, "bold"), bg="#34495e", fg="white", command=self.refresh_users).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="Clear", font=("Arial", 9), bg="#95a5a6", fg="white", command=self._clear_user_search).pack(side=tk.LEFT, padx=2)

        # Right Action Buttons
        tk.Button(toolbar, text="🔄 Refresh", font=("Arial", 9, "bold"), bg="#2980b9", fg="white", command=self.refresh_users).pack(side=tk.RIGHT, padx=3)
        tk.Button(toolbar, text="📥 Export JSON", font=("Arial", 9, "bold"), bg="#16a085", fg="white", command=self._export_users_json).pack(side=tk.RIGHT, padx=3)
        tk.Button(toolbar, text="🗑 Delete User", font=("Arial", 9, "bold"), bg="#c0392b", fg="white", command=self._delete_selected_user).pack(side=tk.RIGHT, padx=3)
        tk.Button(toolbar, text="✏ Edit User", font=("Arial", 9, "bold"), bg="#f39c12", fg="white", command=self._edit_selected_user).pack(side=tk.RIGHT, padx=3)
        tk.Button(toolbar, text="➕ Add User", font=("Arial", 9, "bold"), bg="#27ae60", fg="white", command=self._add_new_user_dialog).pack(side=tk.RIGHT, padx=3)

        # Split pane: Table on left, Photo / detail card on right
        content_pane = tk.PanedWindow(self.tab_users, orient=tk.HORIZONTAL, bg="#ecf0f1", sashwidth=4)
        content_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left: Users Treeview
        table_frame = tk.Frame(content_pane, bg="white")
        content_pane.add(table_frame, minsize=550)

        cols = ("id", "name", "age", "gender", "address", "job", "email", "phone", "lang", "sync")
        self.users_tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.users_tree.heading("id", text="ID")
        self.users_tree.heading("name", text="Full Name")
        self.users_tree.heading("age", text="Age")
        self.users_tree.heading("gender", text="Gender")
        self.users_tree.heading("address", text="City / Address")
        self.users_tree.heading("job", text="Profession / Job")
        self.users_tree.heading("email", text="Email")
        self.users_tree.heading("phone", text="Phone")
        self.users_tree.heading("lang", text="Lang")
        self.users_tree.heading("sync", text="Sync Status")

        self.users_tree.column("id", width=45, anchor="center")
        self.users_tree.column("name", width=130)
        self.users_tree.column("age", width=45, anchor="center")
        self.users_tree.column("gender", width=70, anchor="center")
        self.users_tree.column("address", width=110)
        self.users_tree.column("job", width=120)
        self.users_tree.column("email", width=110)
        self.users_tree.column("phone", width=95)
        self.users_tree.column("lang", width=45, anchor="center")
        self.users_tree.column("sync", width=75, anchor="center")

        tree_scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.users_tree.xview)
        self.users_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.users_tree.bind("<<TreeviewSelect>>", self._on_user_selected)

        # Right: Detail Card & Photo Preview
        self.user_preview_frame = tk.LabelFrame(content_pane, text="👤 Profile Snapshot", font=("Arial", 10, "bold"), bg="#ecf0f1", width=260)
        content_pane.add(self.user_preview_frame, minsize=260)

        self.photo_label = tk.Label(self.user_preview_frame, text="No Image Selected", bg="#bdc3c7", width=30, height=12)
        self.photo_label.pack(padx=10, pady=10)

        self.detail_text = tk.Text(self.user_preview_frame, height=10, font=("Arial", 9), bg="white", wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.detail_text.config(state=tk.DISABLED)

    # =========================================================================
    # TAB 2: Conversation History
    # =========================================================================
    def _build_conversations_tab(self):
        toolbar = tk.Frame(self.tab_convos, bg="#ecf0f1")
        toolbar.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(toolbar, text="Speaker:", font=("Arial", 9, "bold"), bg="#ecf0f1").pack(side=tk.LEFT, padx=4)
        self.convo_speaker_var = tk.StringVar(value="All")
        speaker_combo = ttk.Combobox(toolbar, textvariable=self.convo_speaker_var, values=["All", "User", "Robot"], state="readonly", width=8)
        speaker_combo.pack(side=tk.LEFT, padx=4)
        speaker_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_conversations())

        tk.Button(toolbar, text="🔄 Refresh Logs", font=("Arial", 9, "bold"), bg="#2980b9", fg="white", command=self.refresh_conversations).pack(side=tk.RIGHT, padx=4)

        cols = ("id", "time", "speaker", "lang", "intent", "conf", "message")
        self.convo_tree = ttk.Treeview(self.tab_convos, columns=cols, show="headings", selectmode="browse")

        self.convo_tree.heading("id", text="#")
        self.convo_tree.heading("time", text="Timestamp")
        self.convo_tree.heading("speaker", text="Speaker")
        self.convo_tree.heading("lang", text="Lang")
        self.convo_tree.heading("intent", text="Intent")
        self.convo_tree.heading("conf", text="Confidence")
        self.convo_tree.heading("message", text="Utterance Message")

        self.convo_tree.column("id", width=45, anchor="center")
        self.convo_tree.column("time", width=140)
        self.convo_tree.column("speaker", width=75, anchor="center")
        self.convo_tree.column("lang", width=45, anchor="center")
        self.convo_tree.column("intent", width=120)
        self.convo_tree.column("conf", width=75, anchor="center")
        self.convo_tree.column("message", width=450)

        c_scroll = ttk.Scrollbar(self.tab_convos, orient=tk.VERTICAL, command=self.convo_tree.yview)
        self.convo_tree.configure(yscrollcommand=c_scroll.set)

        self.convo_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        c_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # =========================================================================
    # TAB 3: Registration Sessions
    # =========================================================================
    def _build_sessions_tab(self):
        toolbar = tk.Frame(self.tab_sessions, bg="#ecf0f1")
        toolbar.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(toolbar, text="Active & Completed Registration State Machine Sessions", font=("Arial", 10, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="🔄 Refresh Sessions", font=("Arial", 9, "bold"), bg="#2980b9", fg="white", command=self.refresh_sessions).pack(side=tk.RIGHT, padx=4)

        split = tk.PanedWindow(self.tab_sessions, orient=tk.HORIZONTAL, bg="#ecf0f1", sashwidth=4)
        split.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left: Session list
        left_f = tk.Frame(split, bg="white")
        split.add(left_f, minsize=500)

        cols = ("session_id", "state", "status", "lang", "confirmed", "time")
        self.sess_tree = ttk.Treeview(left_f, columns=cols, show="headings", selectmode="browse")

        self.sess_tree.heading("session_id", text="Session UUID")
        self.sess_tree.heading("state", text="Current State")
        self.sess_tree.heading("status", text="Status")
        self.sess_tree.heading("lang", text="Lang")
        self.sess_tree.heading("confirmed", text="Confirmed")
        self.sess_tree.heading("time", text="Updated At")

        self.sess_tree.column("session_id", width=180)
        self.sess_tree.column("state", width=130)
        self.sess_tree.column("status", width=80, anchor="center")
        self.sess_tree.column("lang", width=45, anchor="center")
        self.sess_tree.column("confirmed", width=70, anchor="center")
        self.sess_tree.column("time", width=130)

        s_scroll = ttk.Scrollbar(left_f, orient=tk.VERTICAL, command=self.sess_tree.yview)
        self.sess_tree.configure(yscrollcommand=s_scroll.set)
        self.sess_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        s_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.sess_tree.bind("<<TreeviewSelect>>", self._on_session_selected)

        # Right: JSON State Inspector
        right_f = tk.LabelFrame(split, text="📦 Session JSON Payload", font=("Arial", 10, "bold"), bg="#ecf0f1", width=350)
        split.add(right_f, minsize=300)

        self.sess_json_text = tk.Text(right_f, font=("Courier", 9), bg="white", wrap=tk.WORD)
        self.sess_json_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    # =========================================================================
    # TAB 4: Durable Sync Queue & Health Diagnostics
    # =========================================================================
    def _build_sync_tab(self):
        toolbar = tk.Frame(self.tab_sync, bg="#ecf0f1")
        toolbar.pack(fill=tk.X, padx=8, pady=8)

        tk.Button(toolbar, text="🔄 Trigger Sync to MySQL Now", font=("Arial", 10, "bold"), bg="#27ae60", fg="white", command=self._trigger_sync_action).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="🩺 Run Diagnostics", font=("Arial", 10, "bold"), bg="#8e44ad", fg="white", command=self._run_diagnostics).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="🔄 Refresh Queue", font=("Arial", 9, "bold"), bg="#2980b9", fg="white", command=self.refresh_sync_queue).pack(side=tk.RIGHT, padx=4)

        split = tk.PanedWindow(self.tab_sync, orient=tk.VERTICAL, bg="#ecf0f1", sashwidth=4)
        split.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Top: Sync Queue Items
        top_f = tk.LabelFrame(split, text="📋 Durable Local & Database Sync Queue", font=("Arial", 10, "bold"), bg="#ecf0f1", height=240)
        split.add(top_f, minsize=180)

        cols = ("uuid", "entity", "action", "status", "retries", "time")
        self.sync_tree = ttk.Treeview(top_f, columns=cols, show="headings", selectmode="browse")

        self.sync_tree.heading("uuid", text="Record UUID")
        self.sync_tree.heading("entity", text="Entity Type")
        self.sync_tree.heading("action", text="Action")
        self.sync_tree.heading("status", text="Status")
        self.sync_tree.heading("retries", text="Retries")
        self.sync_tree.heading("time", text="Created At")

        self.sync_tree.column("uuid", width=180)
        self.sync_tree.column("entity", width=100)
        self.sync_tree.column("action", width=80, anchor="center")
        self.sync_tree.column("status", width=80, anchor="center")
        self.sync_tree.column("retries", width=60, anchor="center")
        self.sync_tree.column("time", width=140)

        sq_scroll = ttk.Scrollbar(top_f, orient=tk.VERTICAL, command=self.sync_tree.yview)
        self.sync_tree.configure(yscrollcommand=sq_scroll.set)
        self.sync_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        sq_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom: Health & Telemetry Inspector
        bottom_f = tk.LabelFrame(split, text="🩺 Live System & Provider Diagnostics Report", font=("Arial", 10, "bold"), bg="#ecf0f1")
        split.add(bottom_f, minsize=160)

        self.diag_text = tk.Text(bottom_f, font=("Courier", 9), bg="white", wrap=tk.WORD)
        self.diag_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

    # =========================================================================
    # Data Loading & Event Handlers
    # =========================================================================
    def _load_initial_data(self):
        self.refresh_all()

    def refresh_all(self):
        """Reload all metrics and data tables in background thread"""
        def worker():
            self._update_metrics()
            self.refresh_users()
            self.refresh_conversations()
            self.refresh_sessions()
            self.refresh_sync_queue()
            self._run_diagnostics()

        threading.Thread(target=worker, daemon=True).start()

    def _update_metrics(self):
        stats = self.admin_service.get_overview_stats()
        def update():
            self.badge_users.config(text=str(stats.get('total_users', 0)))
            self.badge_convos.config(text=str(stats.get('total_conversations', 0)))
            self.badge_sync.config(text=str(stats.get('pending_sync', 0)))
            if stats.get('db_connected'):
                self.badge_db.config(text=f"Online ({stats.get('db_latency_ms', 0)}ms)")
            else:
                self.badge_db.config(text="Offline (JSON)")
            self.status_bar.config(text=f"Telemetry refreshed at {datetime.now().strftime('%H:%M:%S')}")
        self.root.after(0, update)

    def refresh_users(self):
        query = self.user_search_var.get()
        users = self.admin_service.get_all_users(search_query=query)

        def update():
            for row in self.users_tree.get_children():
                self.users_tree.delete(row)
            for u in users:
                self.users_tree.insert("", tk.END, values=(
                    u.get('id'),
                    u.get('name'),
                    u.get('age'),
                    u.get('gender'),
                    u.get('address'),
                    u.get('college_or_job'),
                    u.get('email'),
                    u.get('phone'),
                    u.get('preferred_language'),
                    u.get('sync_status')
                ))
        self.root.after(0, update)

    def _clear_user_search(self):
        self.user_search_var.set("")
        self.refresh_users()

    def _on_user_selected(self, event=None):
        selected = self.users_tree.selection()
        if not selected:
            return

        values = self.users_tree.item(selected[0], "values")
        if not values:
            return

        user_id = values[0]
        # Find user record
        all_users = self.admin_service.get_all_users()
        user = next((u for u in all_users if str(u.get('id')) == str(user_id)), None)
        if not user:
            return

        self.current_selected_user = user

        # Update Photo
        photo_path = user.get('photo_path', '')
        if photo_path and os.path.exists(photo_path):
            try:
                img = Image.open(photo_path)
                img.thumbnail((220, 180))
                self.photo_image_tk = ImageTk.PhotoImage(img)
                self.photo_label.config(image=self.photo_image_tk, text="")
            except Exception:
                self.photo_label.config(image='', text="Image Load Error")
        else:
            self.photo_label.config(image='', text="No Photo Available")

        # Update Detail Card
        details = (
            f"ID: {user.get('id')}\n"
            f"UUID: {user.get('uuid')}\n"
            f"Name: {user.get('name')}\n"
            f"Age: {user.get('age')} years\n"
            f"Gender: {user.get('gender')}\n"
            f"City/Address: {user.get('address')}\n"
            f"Job/College: {user.get('college_or_job')}\n"
            f"Email: {user.get('email')}\n"
            f"Phone: {user.get('phone')}\n"
            f"Language: {user.get('preferred_language')}\n"
            f"Consent: {user.get('consent')}\n"
            f"Sync Status: {user.get('sync_status')}\n"
            f"Last Seen: {user.get('last_seen')}"
        )
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, details)
        self.detail_text.config(state=tk.DISABLED)

    def _add_new_user_dialog(self):
        self._user_form_dialog(title="Add New User Profile")

    def _edit_selected_user(self):
        if not self.current_selected_user:
            messagebox.showinfo("Select User", "Please select a user from the table to edit.")
            return
        self._user_form_dialog(title="Edit User Profile", initial_data=self.current_selected_user)

    def _user_form_dialog(self, title: str, initial_data: Optional[Dict[str, Any]] = None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x520")
        dialog.resizable(False, False)
        dialog.configure(bg="#ecf0f1")
        dialog.grab_set()

        data = initial_data or {}

        fields = [
            ("Name", data.get('name', '')),
            ("Age", data.get('age', '25')),
            ("Gender", data.get('gender', 'Male')),
            ("City / Address", data.get('address', '')),
            ("Job / College", data.get('college_or_job', '')),
            ("Email", data.get('email', '') if data.get('email') != '--' else ''),
            ("Phone", data.get('phone', '') if data.get('phone') != '--' else ''),
            ("Language", data.get('preferred_language', 'en'))
        ]

        entries = {}
        for label, val in fields:
            tk.Label(dialog, text=f"{label}:", font=("Arial", 9, "bold"), bg="#ecf0f1").pack(anchor="w", padx=20, pady=(6, 1))
            ent = tk.Entry(dialog, font=("Arial", 10), width=36)
            ent.insert(0, str(val))
            ent.pack(padx=20, pady=(0, 3))
            entries[label] = ent

        def save():
            payload = {
                'name': entries["Name"].get().strip() or "Anonymous",
                'age': entries["Age"].get().strip() or "25",
                'gender': entries["Gender"].get().strip() or "Not specified",
                'address': entries["City / Address"].get().strip() or "Not specified",
                'job': entries["Job / College"].get().strip() or "Not specified",
                'email': entries["Email"].get().strip(),
                'phone': entries["Phone"].get().strip(),
                'preferred_language': entries["Language"].get().strip() or "en",
                'consent': 'Yes'
            }
            if initial_data and initial_data.get('id'):
                payload['user_id'] = initial_data['id']
                payload['uuid'] = initial_data.get('uuid')

            try:
                self.admin_service.save_user(payload)
                messagebox.showinfo("Success", f"User profile for '{payload['name']}' saved successfully.")
                dialog.destroy()
                self.refresh_users()
                self._update_metrics()
            except Exception as e:
                messagebox.showerror("Error", f"Could not save user: {e}")

        btn_f = tk.Frame(dialog, bg="#ecf0f1")
        btn_f.pack(pady=15)
        tk.Button(btn_f, text="💾 Save", font=("Arial", 10, "bold"), bg="#27ae60", fg="white", command=save, padx=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="Cancel", font=("Arial", 10), bg="#95a5a6", fg="white", command=dialog.destroy, padx=10).pack(side=tk.LEFT, padx=5)

    def _delete_selected_user(self):
        if not self.current_selected_user:
            messagebox.showinfo("Select User", "Please select a user from the table to delete.")
            return

        name = self.current_selected_user.get('name')
        uid = self.current_selected_user.get('id')

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete profile for '{name}' (ID: {uid})?"):
            success = self.admin_service.delete_user(uid)
            if success:
                messagebox.showinfo("Deleted", f"User '{name}' has been deleted.")
                self.current_selected_user = None
                self.refresh_users()
                self._update_metrics()
            else:
                messagebox.showerror("Error", f"Failed to delete profile '{name}'.")

    def _export_users_json(self):
        data = self.admin_service.export_all_data()
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile=f"mr_beast_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Export Successful", f"Database records exported successfully to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    def refresh_conversations(self):
        speaker = self.convo_speaker_var.get()
        logs = self.admin_service.get_conversation_logs(limit=150, speaker=speaker)

        def update():
            for row in self.convo_tree.get_children():
                self.convo_tree.delete(row)
            for l in logs:
                self.convo_tree.insert("", tk.END, values=(
                    l.get('log_id'),
                    l.get('timestamp'),
                    l.get('speaker'),
                    l.get('language'),
                    l.get('intent'),
                    l.get('confidence'),
                    l.get('message')
                ))
        self.root.after(0, update)

    def refresh_sessions(self):
        sessions = self.admin_service.get_registration_sessions(limit=50)

        def update():
            for row in self.sess_tree.get_children():
                self.sess_tree.delete(row)
            for s in sessions:
                self.sess_tree.insert("", tk.END, values=(
                    s.get('session_id'),
                    s.get('current_state'),
                    s.get('status'),
                    s.get('language'),
                    "Yes" if s.get('is_confirmed') else "No",
                    s.get('updated_at')
                ))
        self.root.after(0, update)

    def _on_session_selected(self, event=None):
        sel = self.sess_tree.selection()
        if not sel:
            return
        vals = self.sess_tree.item(sel[0], "values")
        if not vals:
            return
        sess_id = vals[0]
        sessions = self.admin_service.get_registration_sessions()
        target = next((s for s in sessions if str(s.get('session_id')) == str(sess_id)), None)
        if target:
            raw_data = target.get('collected_data')
            try:
                formatted = json.dumps(json.loads(raw_data), indent=2) if isinstance(raw_data, str) else json.dumps(raw_data, indent=2)
            except Exception:
                formatted = str(raw_data)

            self.sess_json_text.delete("1.0", tk.END)
            self.sess_json_text.insert(tk.END, formatted)

    def refresh_sync_queue(self):
        queue_items = self.admin_service.get_sync_queue()

        def update():
            for row in self.sync_tree.get_children():
                self.sync_tree.delete(row)
            for item in queue_items:
                self.sync_tree.insert("", tk.END, values=(
                    item.get('uuid'),
                    item.get('entity_type'),
                    item.get('action'),
                    item.get('status'),
                    item.get('retry_count', 0),
                    item.get('created_at')
                ))
        self.root.after(0, update)

    def _trigger_sync_action(self):
        def worker():
            self.status_bar.config(text="Synchronizing queue to MySQL database...")
            res = self.admin_service.trigger_sync()
            synced = res.get('synced', 0)
            failed = res.get('failed', 0)
            messagebox.showinfo("Sync Result", f"Synchronization complete!\n• Successfully synced: {synced}\n• Remaining / Failed: {failed}")
            self.refresh_all()

        threading.Thread(target=worker, daemon=True).start()

    def _run_diagnostics(self):
        def worker():
            health = self.admin_service.health_service.check_health()
            formatted = json.dumps(health, indent=2)
            def update():
                self.diag_text.delete("1.0", tk.END)
                self.diag_text.insert(tk.END, formatted)
            self.root.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    def run(self):
        if not self.is_toplevel:
            self.root.mainloop()


def launch_admin_dashboard(parent=None):
    """Entry point to open the admin dashboard"""
    app = MrBeastAdminDashboard(parent_or_root=parent)
    if parent is None:
        app.run()
    return app


if __name__ == "__main__":
    launch_admin_dashboard()
