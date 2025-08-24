# File Manager App (PyQt6 port of your Tkinter layout)
# Copyright (C) 2025, x2dat/x2.exe on github.com
#
# GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. https://www.gnu.org/licenses/

from __future__ import annotations
import sys, os, json, datetime, subprocess, webbrowser

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLineEdit, QLabel, QPushButton, QFileDialog, QMessageBox,
    QFrame, QDialog, QDialogButtonBox, QFormLayout, QPlainTextEdit, QSpacerItem,
    QSizePolicy
)

# ---- data location next to .py / .exe ----
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "file_data.json")


# ---------------- Dialogs ---------------- #

class TitleInputDialog(QDialog):
    """Small dialog to enter a title (used when adding files)."""
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Title")
        self.setModal(True)
        layout = QVBoxLayout(self)
        lbl = QLabel(f"Enter title for:\n{os.path.basename(filename)}")
        self.edit = QLineEdit()
        self.edit.setFont(QFont("Segoe UI", 12))
        self.edit.setPlaceholderText(os.path.basename(filename))
        layout.addWidget(lbl)
        layout.addWidget(self.edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def value(self) -> str:
        text = self.edit.text().strip()
        return text if text else self.edit.placeholderText()


class NoteDialog(QDialog):
    """Dialog for creating/editing a note (title + note)."""
    def __init__(self, title_text: str = "", note_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Add / Edit Note")
        self.resize(400, 350)
        form = QFormLayout(self)

        self.title_edit = QLineEdit()
        self.title_edit.setFont(QFont("Segoe UI", 12))
        self.title_edit.setText(title_text)
        self.title_edit.setPlaceholderText("Untitled Note")
        form.addRow("Title:", self.title_edit)

        self.note_edit = QPlainTextEdit()
        self.note_edit.setPlainText(note_text)
        self.note_edit.setPlaceholderText("Write your note here...")
        form.addRow("Note:", self.note_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self.setLayout(form)

    def get(self):
        title = self.title_edit.text().strip() or "Untitled Note"
        note = self.note_edit.toPlainText().strip()
        return title, note


class LinkDialog(QDialog):
    def __init__(self, title_text: str = "", url_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔗 Add Link")
        self.resize(400, 200)
        form = QFormLayout(self)

        self.title_edit = QLineEdit()
        self.title_edit.setFont(QFont("Segoe UI", 12))
        self.title_edit.setText(title_text)
        self.title_edit.setPlaceholderText("Untitled Link")
        form.addRow("Title:", self.title_edit)

        self.url_edit = QLineEdit()
        self.url_edit.setFont(QFont("Segoe UI", 12))
        self.url_edit.setText(url_text)
        self.url_edit.setPlaceholderText("https://example.com")
        form.addRow("URL:", self.url_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get(self):
        title = self.title_edit.text().strip() or "Untitled Link"
        url = self.url_edit.text().strip()
        return title, url


class RenameDialog(QDialog):
    def __init__(self, current: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Item")
        self.resize(400, 150)
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Enter new title:"))
        self.edit = QLineEdit(current)
        self.edit.setFont(QFont("Segoe UI", 12))
        v.addWidget(self.edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        v.addWidget(buttons)

    def value(self):
        return self.edit.text().strip()


# ------------- Collapsible section ------------- #

class CollapsibleSection(QFrame):
    def __init__(self, date: str, items: list[dict], app: "MainWindow"):
        super().__init__()
        self.app = app
        self.date = date
        self.items = items
        self.collapsed = True

        self.setFrameShape(QFrame.Shape.NoFrame)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        # Header button
        self.header_btn = QPushButton(f"{date} ▸")
        self.header_btn.setObjectName("headerButton")
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.clicked.connect(self.toggle)
        v.addWidget(self.header_btn)

        # Container
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(10, 0, 10, 0)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(4)
        v.addWidget(self.container)
        self.container.setVisible(False)

        self.refresh_rows()

    def toggle(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.header_btn.setText(self.header_btn.text().replace("▾", "▸"))
            self.container.setVisible(False)
        else:
            self.header_btn.setText(self.header_btn.text().replace("▸", "▾"))
            self.container.setVisible(True)

    def expand(self):
        if self.collapsed:
            self.toggle()

    def refresh_rows(self):
        # clear layout
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for r, f in enumerate(self.items):
            if "note" in f:
                title = f.get("title", "Untitled Note")
                text = title  # No bold tags
                lbl = QLabel(text)
                lbl.setTextFormat(Qt.TextFormat.PlainText)
            else:
                lbl = QLabel(f.get("desc", ""))
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.grid.addWidget(lbl, r, 0)

            def add_btn(text, handler):
                btn = QPushButton(text)
                btn.setObjectName("rowButton")
                btn.clicked.connect(handler)
                btn.setMinimumWidth(84)
                return btn

            if "path" in f:
                self.grid.addWidget(add_btn("Open",
                    lambda _, p=f["path"]: self.app.open_file(p)), r, 1)
                self.grid.addWidget(add_btn("Rename",
                    lambda _, d=self.date, it=f: self.app.rename_item(d, it)), r, 2)
                self.grid.addWidget(add_btn("Delete",
                    lambda _, d=self.date, it=f: self.app.delete_item(d, it)), r, 3)

            elif "note" in f:
                self.grid.addWidget(add_btn("View Note",
                    lambda _, it=f: self.app.open_note_popup(it)), r, 1, 1, 2)
                self.grid.addWidget(add_btn("Delete",
                    lambda _, d=self.date, it=f: self.app.delete_item(d, it)), r, 3)

            elif "url" in f:
                self.grid.addWidget(add_btn("Open Link",
                    lambda _, u=f["url"]: self.app.open_link(u)), r, 1)
                self.grid.addWidget(add_btn("Rename",
                    lambda _, d=self.date, it=f: self.app.rename_item(d, it)), r, 2)
                self.grid.addWidget(add_btn("Delete",
                    lambda _, d=self.date, it=f: self.app.delete_item(d, it)), r, 3)


# ---------------- Main Window ---------------- #

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📚 File Manager")
        self.resize(800, 500)

        # Fonts / colors
        self.base_font = QFont("Segoe UI", 10)

        # ---- central widget with vertical layout ----
        central = QWidget()
        self.setCentralWidget(central)
        root_v = QVBoxLayout(central)
        root_v.setContentsMargins(10, 10, 10, 10)
        root_v.setSpacing(6)

        # ---- Search bar row (top) ----
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(6)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search…")
        self.search_edit.textChanged.connect(self.refresh_ui)

        self.search_edit.setFont(self.base_font)

        search_row.addWidget(self.search_edit, 1)  # expands
        root_v.addLayout(search_row)

        # ---- Scrollable area (middle) ----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_container)
        root_v.addWidget(self.scroll_area, 1)

        # ---- Buttons area (bottom, stacked vertically full width) ----
        btn_box = QVBoxLayout()
        btn_box.setContentsMargins(0, 0, 0, 0)
        btn_box.setSpacing(6)

        self.btn_add_file = QPushButton("➕ Add File")
        self.btn_add_note = QPushButton("📝 Add Note")
        self.btn_add_link = QPushButton("🔗 Add Link")
        for b in (self.btn_add_file, self.btn_add_note, self.btn_add_link):
            b.setObjectName("actionButton")
            b.setMinimumHeight(36)
            b.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))

        self.btn_add_file.clicked.connect(self.add_file)
        self.btn_add_note.clicked.connect(self.add_note)
        self.btn_add_link.clicked.connect(self.add_link)

        btn_box.addWidget(self.btn_add_file)
        btn_box.addWidget(self.btn_add_note)
        btn_box.addWidget(self.btn_add_link)

        # A wrapper frame to span full width
        btn_frame = QFrame()
        btn_frame.setLayout(btn_box)
        root_v.addWidget(btn_frame, 0)

        # ---- load data + style ----
        self.data = self.load_data()
        self.apply_theme()
        self.refresh_ui()

    # ---------- Data ---------- #
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except PermissionError:
            QMessageBox.critical(self, "Error",
                                 "Permission denied writing file_data.json.\n"
                                 "Place the app in a folder where you have write access.")

    # ---------- Actions ---------- #
    def add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select files")
        if not paths:
            return
        today = str(datetime.date.today())
        for p in paths:
            # Prevent duplicates for same date
            if today in self.data and any(("path" in it and it["path"] == p) for it in self.data[today]):
                QMessageBox.warning(self, "Duplicate",
                                    f"{os.path.basename(p)} is already added today.")
                continue
            dlg = TitleInputDialog(p, self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                desc = dlg.value()
                if today not in self.data:
                    self.data[today] = []
                self.data[today].append({"desc": desc, "path": p})
        self.save_data()
        self.refresh_ui()

    def add_note(self):
        today = str(datetime.date.today())
        dlg = NoteDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, note = dlg.get()
            if not note:
                QMessageBox.warning(self, "Empty Note", "Note text cannot be empty.")
                return
            if today not in self.data:
                self.data[today] = []
            self.data[today].append({"title": title, "note": note})
            self.save_data()
            self.refresh_ui()

    def add_link(self):
        today = str(datetime.date.today())
        dlg = LinkDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, url = dlg.get()
            if not url:
                QMessageBox.warning(self, "Empty URL", "URL cannot be empty.")
                return
            if today not in self.data:
                self.data[today] = []
            self.data[today].append({"desc": title, "url": url})
            self.save_data()
            self.refresh_ui()

    def open_file(self, path: str):
        if not os.path.exists(path):
            QMessageBox.critical(self, "Error", "File not found!")
            return
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif os.name == "posix":
            try:
                subprocess.call(("open", path))
            except Exception:
                subprocess.call(("xdg-open", path))

    def open_link(self, url: str):
        webbrowser.open(url)

    def open_note_popup(self, item: dict):
        dlg = NoteDialog(
            item.get("title", "Untitled Note"),
            item.get("note", ""),
            self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, note = dlg.get()
            item["title"] = title or "Untitled Note"
            item["note"] = note
            self.save_data()
            self.refresh_ui()

    def rename_item(self, date: str, item: dict):
        dlg = RenameDialog(item.get("desc", ""), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_title = dlg.value()
            if new_title:
                item["desc"] = new_title
                self.save_data()
                self.refresh_ui()

    def delete_item(self, date: str, item: dict):
        confirm = QMessageBox.question(self, "Delete", f"Delete {item.get('desc','item')}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.data[date].remove(item)
            if not self.data[date]:
                del self.data[date]
            self.save_data()
            self.refresh_ui()

    # ---------- UI refresh ---------- #
    def refresh_ui(self):
        # clear sections
        while self.scroll_layout.count():
            it = self.scroll_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        query = (self.search_edit.text() or "").lower().strip()
        search_mode = bool(query)

        # sort dates descending
        for date in sorted(self.data.keys(), reverse=True):
            items = self.data[date]
            if query:
                filtered = [
                    f for f in items
                    if (query in f.get("desc", "").lower())
                    or ("path" in f and query in os.path.basename(f["path"]).lower())
                    or ("note" in f and query in f.get("note", "").lower())
                    or ("url" in f and query in f.get("url", "").lower())
                ]
            else:
                filtered = items

            if not filtered:
                continue

            section = CollapsibleSection(date, filtered, self)
            if search_mode:
                section.expand()
            self.scroll_layout.addWidget(section)

        self.scroll_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Minimum,
                                               QSizePolicy.Policy.Expanding))

    # ---------- Styling ---------- #
    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f5f5; color: #111; }
            QLabel { font: 10pt "Segoe UI"; }
            QLineEdit {
                font: 10pt "Segoe UI";
                padding: 6px 8px;
                border-radius: 6px;
                border: 1px solid #c9c9c9;
                background: #ffffff;
            }
            QPlainTextEdit {
                font: 10pt "Segoe UI";
                padding: 6px 8px;
                border-radius: 6px;
                border: 1px solid #c9c9c9;
                background: #ffffff;
            }
            QScrollArea { border: none; }
            /* --- Custom Scrollbar --- */
            QScrollBar:vertical {
                background: #e9ecef;
                width: 12px;
                margin: 2px 0 2px 6px;
                border-radius: 12px;
            }
            QScrollBar::handle:vertical {
                background: #b0b8c1;
                min-height: 24px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8fa2b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background: #e9ecef;
                height: 12px;
                margin: 0 2px 0 2px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #b0b8c1;
                min-width: 24px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #8fa2b8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QPushButton#actionButton {
                background: #000000;
                color: #ffffff;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 12px;
                border: 1px solid #000000;
            }
            QPushButton#actionButton:hover {
                background: #111111;
            }
            QPushButton#actionButton:pressed {
                background: #222222;
            }
            QPushButton#rowButton {
                background: #0B5ED7; /* blue */
                color: #ffffff;
                font-weight: 600;
                border-radius: 6px;
                padding: 6px 10px;
                border: 1px solid #0A58CA;
            }
            QPushButton#rowButton:hover { background: #0A58CA; }
            QPushButton#rowButton:pressed { background: #094DB3; }
            QPushButton#headerButton {
                background: #e9ecef;
                color: #111;
                border: 1px solid #d0d4d9;
                border-radius: 8px;
                text-align: left;
                padding: 10px 12px;
                font: 11pt "Segoe UI";
                font-weight: 600;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("File Manager")
    # nice default icon/size DPI
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
