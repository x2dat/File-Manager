# File Manager App
# Copyright (C) 2025, x2dat/x2.exe on github.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ----------------------- Full code: -----------------------

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
import os
import json
import datetime
import subprocess

DATA_FILE = "file_data.json"


class FileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 File Manager")
        self.root.geometry("800x500")
        self.root.configure(bg="#f5f5f5")

        self.data = self.load_data()
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.refresh_ui())  # live search

        # Style
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Header.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.configure("TLabel", font=("Segoe UI", 10))

        # Search Bar
        search_frame = ttk.Frame(root)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Scrollable Frame
        self.canvas = tk.Canvas(root, bg="#f5f5f5", highlightthickness=0)
        self.scroll_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", pady=5, padx=10)
        ttk.Button(btn_frame, text="➕ Add File", style="TButton", command=self.add_file).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="📝 Add Note", style="TButton", command=self.add_note).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🔗 Add Link", style="TButton", command=self.add_link).pack(fill="x", pady=2)

        self.refresh_ui()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_file(self):
        filepaths = filedialog.askopenfilenames()
        if not filepaths:
            return

        today = str(datetime.date.today())

        for path in filepaths:
            # Prevent duplicates for the same date
            if today in self.data and any("path" in f and f["path"] == path for f in self.data[today]):
                messagebox.showwarning("Duplicate", f"{os.path.basename(path)} is already added today.")
                continue

            # Wide title entry
            title_window = tk.Toplevel(self.root)
            title_window.title("File Title")
            title_window.geometry("400x150")

            ttk.Label(title_window, text=f"Enter title for:\n{os.path.basename(path)}").pack(anchor="w", padx=10, pady=10)
            entry = ttk.Entry(title_window, font=("Segoe UI", 12), width=40)
            entry.pack(fill="x", padx=10, pady=5)
            entry.focus()

            def save_title():
                desc = entry.get().strip()
                if not desc:
                    desc = os.path.basename(path)

                if today not in self.data:
                    self.data[today] = []

                self.data[today].append({"desc": desc, "path": path})
                self.save_data()
                self.refresh_ui()
                title_window.destroy()

            ttk.Button(title_window, text="Save", command=save_title).pack(pady=10)

    def add_note(self):
        today = str(datetime.date.today())

        note_window = tk.Toplevel(self.root)
        note_window.title("📝 Add Note")
        note_window.geometry("400x400")

        ttk.Label(note_window, text="Title:").pack(anchor="w", padx=10, pady=5)
        desc_entry = ttk.Entry(note_window, font=("Segoe UI", 12), width=40)
        desc_entry.pack(fill="x", padx=10)

        ttk.Label(note_window, text="Note:").pack(anchor="w", padx=10, pady=5)
        text_area = tk.Text(note_window, wrap="word", height=10)
        text_area.pack(fill="both", expand=True, padx=10, pady=5)

        def save_note():
            desc = desc_entry.get().strip()
            note_text = text_area.get("1.0", "end-1c").strip()
            if not desc:
                desc = "Untitled Note"
            if not note_text:
                messagebox.showwarning("Empty Note", "Note text cannot be empty.")
                return

            if today not in self.data:
                self.data[today] = []
            self.data[today].append({"desc": desc, "note": note_text})
            self.save_data()
            self.refresh_ui()
            note_window.destroy()

        ttk.Button(note_window, text="Save", command=save_note).pack(pady=5)

    def add_link(self):
        today = str(datetime.date.today())

        link_window = tk.Toplevel(self.root)
        link_window.title("🔗 Add Link")
        link_window.geometry("400x200")

        ttk.Label(link_window, text="Title:").pack(anchor="w", padx=10, pady=5)
        title_entry = ttk.Entry(link_window, font=("Segoe UI", 12), width=40)
        title_entry.pack(fill="x", padx=10, pady=5)

        ttk.Label(link_window, text="URL:").pack(anchor="w", padx=10, pady=5)
        url_entry = ttk.Entry(link_window, font=("Segoe UI", 12), width=40)
        url_entry.pack(fill="x", padx=10, pady=5)

        def save_link():
            title = title_entry.get().strip() or "Untitled Link"
            url = url_entry.get().strip()
            if not url:
                messagebox.showwarning("Empty URL", "URL cannot be empty.")
                return

            if today not in self.data:
                self.data[today] = []
            self.data[today].append({"desc": title, "url": url})
            self.save_data()
            self.refresh_ui()
            link_window.destroy()

        ttk.Button(link_window, text="Save", command=save_link).pack(pady=10)

    def refresh_ui(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().lower().strip()
        search_mode = bool(query)

        for date, items in sorted(self.data.items(), reverse=True):
            # Filter items by search
            filtered_items = [
                f for f in items
                if query in f["desc"].lower()
                or ("path" in f and query in os.path.basename(f["path"]).lower())
                or ("note" in f and query in f.get("note", "").lower())
                or ("url" in f and query in f.get("url", "").lower())
            ] if query else items

            if not filtered_items:
                continue

            section = CollapsibleSection(self.scroll_frame, date, filtered_items, self)
            if search_mode:
                section.expand()
            section.pack(fill="x", pady=4, padx=5)

    def open_file(self, path):
        if os.path.exists(path):
            if os.name == "nt":  # Windows
                os.startfile(path)
            elif os.name == "posix":  # macOS/Linux
                try:
                    subprocess.call(("open", path))  # macOS
                except Exception:
                    subprocess.call(("xdg-open", path))  # Linux
        else:
            messagebox.showerror("Error", "File not found!")

    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    def open_note_popup(self, file_item):
        note_window = tk.Toplevel(self.root)
        note_window.title(f"📝 {file_item['desc']}")
        note_window.geometry("400x580")

        ttk.Label(note_window, text="Title:").pack(anchor="w", padx=10, pady=5)
        desc_entry = ttk.Entry(note_window, font=("Segoe UI", 12), width=40)
        desc_entry.insert(0, file_item["desc"])
        desc_entry.pack(fill="x", padx=10, pady=5)

        ttk.Label(note_window, text="Note:").pack(anchor="w", padx=10, pady=5)
        text_area = tk.Text(note_window, wrap="word")
        text_area.insert("1.0", file_item["note"])
        text_area.pack(fill="both", expand=True, padx=10, pady=10)

        def save_changes():
            file_item["desc"] = desc_entry.get().strip() or "Untitled Note"
            file_item["note"] = text_area.get("1.0", "end-1c")
            self.save_data()
            self.refresh_ui()
            note_window.destroy()

        ttk.Button(note_window, text="Save", command=save_changes).pack(pady=5)

    def rename_item(self, date, file_item):
        rename_window = tk.Toplevel(self.root)
        rename_window.title("Rename Item")
        rename_window.geometry("400x150")

        ttk.Label(rename_window, text="Enter new title:").pack(anchor="w", padx=10, pady=10)

        entry = ttk.Entry(rename_window, font=("Segoe UI", 12), width=40)
        entry.insert(0, file_item["desc"])
        entry.pack(fill="x", padx=10, pady=5)
        entry.focus()

        def save_rename():
            new_title = entry.get().strip()
            if new_title:
                file_item["desc"] = new_title
                self.save_data()
                self.refresh_ui()
                rename_window.destroy()

        ttk.Button(rename_window, text="Save", command=save_rename).pack(pady=10)

    def delete_item(self, date, file_item):
        confirm = messagebox.askyesno("Delete", f"Delete {file_item['desc']}?")
        if confirm:
            self.data[date].remove(file_item)
            if not self.data[date]:
                del self.data[date]
            self.save_data()
            self.refresh_ui()


class CollapsibleSection(ttk.Frame):
    def __init__(self, parent, date, items, app):
        super().__init__(parent)
        self.app = app
        self.items = items
        self.date = date
        self.collapsed = True

        # Date header
        self.header = ttk.Button(self, text=f"{date} ▸", style="Header.TButton", command=self.toggle)
        self.header.pack(fill="x")

        # Container for items
        self.container = ttk.Frame(self)

    def toggle(self):
        if self.collapsed:
            self.expand()
        else:
            self.collapse()

    def expand(self):
        if self.collapsed:
            self.header.config(text=self.header.cget("text").replace("▸", "▾"))
            self.show_items()
            self.container.pack(fill="x", padx=10, pady=3)
            self.collapsed = False

    def collapse(self):
        if not self.collapsed:
            self.header.config(text=self.header.cget("text").replace("▾", "▸"))
            self.container.forget()
            self.collapsed = True

    def show_items(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=0)
        self.container.grid_columnconfigure(2, weight=0)
        self.container.grid_columnconfigure(3, weight=0)

        for r, file_item in enumerate(self.items):
            ttk.Label(self.container, text=file_item["desc"], anchor="w").grid(
                row=r, column=0, sticky="w", padx=5, pady=2
            )

            if "path" in file_item:
                ttk.Button(
                    self.container, text="Open",
                    command=lambda p=file_item["path"]: self.app.open_file(p)
                ).grid(row=r, column=1, padx=2, pady=2, sticky="ew")

                ttk.Button(
                    self.container, text="Rename",
                    command=lambda f=file_item: self.app.rename_item(self.date, f)
                ).grid(row=r, column=2, padx=2, pady=2, sticky="ew")

                ttk.Button(
                    self.container, text="Delete",
                    command=lambda f=file_item: self.app.delete_item(self.date, f)
                ).grid(row=r, column=3, padx=2, pady=2, sticky="ew")

            elif "note" in file_item:
                ttk.Button(
                    self.container, text="View Note",
                    command=lambda f=file_item: self.app.open_note_popup(f)
                ).grid(row=r, column=1, columnspan=2, padx=2, pady=2, sticky="ew")

                ttk.Button(
                    self.container, text="Delete",
                    command=lambda f=file_item: self.app.delete_item(self.date, f)
                ).grid(row=r, column=3, padx=2, pady=2, sticky="ew")

            elif "url" in file_item:
                ttk.Button(
                    self.container, text="Open Link",
                    command=lambda u=file_item["url"]: self.app.open_link(u)
                ).grid(row=r, column=1, padx=2, pady=2, sticky="ew")

                ttk.Button(
                    self.container, text="Rename",
                    command=lambda f=file_item: self.app.rename_item(self.date, f)
                ).grid(row=r, column=2, padx=2, pady=2, sticky="ew")

                ttk.Button(
                    self.container, text="Delete",
                    command=lambda f=file_item: self.app.delete_item(self.date, f)
                ).grid(row=r, column=3, padx=2, pady=2, sticky="ew")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagerApp(root)
    root.mainloop()
