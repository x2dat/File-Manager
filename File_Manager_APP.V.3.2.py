from __future__ import annotations
import sys, os, json, datetime, subprocess, webbrowser, time

from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLineEdit, QLabel, QPushButton, QFileDialog, QMessageBox,
    QFrame, QDialog, QDialogButtonBox, QFormLayout, QPlainTextEdit, QSpacerItem,
    QSizePolicy, QProgressBar
)

# ---- data location next to .py / .exe ----
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "file_data.json")

# ---------------- Auto-Add Logic & Worker ---------------- #

class FileScannerWorker(QObject):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int, str)

    def run(self):
        """Scans the Downloads folder and updates data based on file creation time."""
        data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = {}

        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_path):
            self.finished.emit(data)
            return

        files = [f for f in os.listdir(downloads_path) if os.path.isfile(os.path.join(downloads_path, f))]
        total_files = len(files)
        
        existing_paths = set()
        for date_group in data.values():
            for item in date_group:
                if "path" in item:
                    existing_paths.add(item["path"])

        for i, filename in enumerate(files):
            full_path = os.path.join(downloads_path, filename)
            
            if full_path not in existing_paths:
                # Get Windows Creation Time
                timestamp = os.path.getctime(full_path)
                dt_object = datetime.date.fromtimestamp(timestamp)
                date_str = str(dt_object)

                # Format name: Filename (.EXT)
                name_part, ext_part = os.path.splitext(filename)
                formatted_name = f"{name_part} ({ext_part.replace('.', '').upper()})"

                if date_str not in data:
                    data[date_str] = []
                
                data[date_str].append({"desc": formatted_name, "path": full_path})
                existing_paths.add(full_path)

            percent = int(((i + 1) / total_files) * 100) if total_files > 0 else 100
            self.progress.emit(percent, f"Checking: {filename[:30]}...")
            
        self.finished.emit(data)

class LoadingScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Syncing Files...")
        self.setFixedSize(400, 120)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        self.label = QLabel("Initializing scanner...")
        self.label.setFont(QFont("Segoe UI", 10))
        
        self.pbar = QProgressBar()
        self.pbar.setStyleSheet("""
            QProgressBar { border: 1px solid #c9c9c9; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #0B5ED7; }
        """)
        
        layout.addWidget(self.label)
        layout.addWidget(self.pbar)

    def update_progress(self, val, text):
        self.pbar.setValue(val)
        self.label.setText(text)

# ---------------- Dialogs ---------------- #

class TitleInputDialog(QDialog):
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

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        self.header_btn = QPushButton(f"{date} ▸")
        self.header_btn.setObjectName("headerButton")
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.clicked.connect(self.toggle)
        v.addWidget(self.header_btn)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(10, 0, 10, 0)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(4)
        self.grid.setColumnStretch(0, 1) # Label takes available space
        
        v.addWidget(self.container)
        self.container.setVisible(False)
        self.refresh_rows()

    def toggle(self):
        self.collapsed = not self.collapsed
        self.header_btn.setText(self.header_btn.text().replace("▾", "▸") if self.collapsed else self.header_btn.text().replace("▸", "▾"))
        self.container.setVisible(not self.collapsed)

    def expand(self):
        if self.collapsed: self.toggle()

    def truncate_text(self, text: str, length: int = 50) -> str:
        return text[:length] + "..." if len(text) > length else text

    def refresh_rows(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for r, f in enumerate(self.items):
            display_text = f.get("title") if "note" in f else f.get("desc", "")
            lbl = QLabel(self.truncate_text(display_text))
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.grid.addWidget(lbl, r, 0)

            def add_btn(text, handler, width=100):
                btn = QPushButton(text)
                btn.setObjectName("rowButton")
                btn.clicked.connect(handler)
                btn.setFixedWidth(width)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                return btn

            if "path" in f:
                self.grid.addWidget(add_btn("Open", lambda _, p=f["path"]: self.app.open_file(p)), r, 1)
                self.grid.addWidget(add_btn("Rename", lambda _, d=self.date, it=f: self.app.rename_item(d, it)), r, 2)
                self.grid.addWidget(add_btn("Delete", lambda _, d=self.date, it=f: self.app.delete_item(d, it)), r, 3)
            elif "note" in f:
                self.grid.addWidget(add_btn("View Note", lambda _, it=f: self.app.open_note_popup(it), width=210), r, 1, 1, 2)
                self.grid.addWidget(add_btn("Delete", lambda _, d=self.date, it=f: self.app.delete_item(d, it)), r, 3)
            elif "url" in f:
                self.grid.addWidget(add_btn("Open Link", lambda _, u=f["url"]: self.app.open_link(u)), r, 1)
                self.grid.addWidget(add_btn("Rename", lambda _, d=self.date, it=f: self.app.rename_item(d, it)), r, 2)
                self.grid.addWidget(add_btn("Delete", lambda _, d=self.date, it=f: self.app.delete_item(d, it)), r, 3)

# ---------------- Main Window ---------------- #

class MainWindow(QMainWindow):
    def __init__(self, initial_data: dict):
        super().__init__()
        self.setWindowTitle("📚 File Manager")
        self.resize(800, 500)
        self.data = initial_data

        central = QWidget()
        self.setCentralWidget(central)
        root_v = QVBoxLayout(central)
        root_v.setContentsMargins(10, 10, 10, 10)
        root_v.setSpacing(6)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search…")
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.refresh_ui)
        self.search_edit.textChanged.connect(self.debounce_search)
        root_v.addWidget(self.search_edit)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_container)
        root_v.addWidget(self.scroll_area, 1)

        btn_box = QVBoxLayout()
        for text, icon, func in [("➕ Add File", "", self.add_file), ("📝 Add Note", "", self.add_note), ("🔗 Add Link", "", self.add_link)]:
            btn = QPushButton(text)
            btn.setObjectName("actionButton")
            btn.setMinimumHeight(36)
            btn.clicked.connect(func)
            btn_box.addWidget(btn)

        btn_frame = QFrame()
        btn_frame.setLayout(btn_box)
        root_v.addWidget(btn_frame, 0)

        self.expanded_dates = set()  # Track which date groups are expanded
        self.apply_theme()
        self.refresh_ui()

    def debounce_search(self):
        """Debounce the search to avoid lag from rapid updates."""
        self.search_timer.stop()
        self.search_timer.start(300)  # Wait 300ms after user stops typing

    def get_expanded_dates(self) -> set:
        """Get all currently expanded date groups."""
        expanded = set()
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if isinstance(widget, CollapsibleSection) and not widget.collapsed:
                expanded.add(widget.date)
        return expanded

    def restore_expanded_state(self, expanded_dates: set):
        """Restore expanded state for specific dates."""
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if isinstance(widget, CollapsibleSection):
                if widget.date in expanded_dates and widget.collapsed:
                    widget.toggle()
                elif widget.date not in expanded_dates and not widget.collapsed:
                    widget.toggle()

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except:
            QMessageBox.critical(self, "Error", "Failed to save data.")

    def add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select files")
        if not paths: return
        today = str(datetime.date.today())
        expanded_dates = self.get_expanded_dates()
        for p in paths:
            dlg = TitleInputDialog(p, self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                if today not in self.data: self.data[today] = []
                self.data[today].append({"desc": dlg.value(), "path": p})
        self.save_data()
        self.refresh_ui()
        self.restore_expanded_state(expanded_dates)

    def add_note(self):
        today = str(datetime.date.today())
        expanded_dates = self.get_expanded_dates()
        dlg = NoteDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, note = dlg.get()
            if not note: return
            if today not in self.data: self.data[today] = []
            self.data[today].append({"title": title, "note": note})
            self.save_data()
            self.refresh_ui()
            self.restore_expanded_state(expanded_dates)

    def add_link(self):
        today = str(datetime.date.today())
        expanded_dates = self.get_expanded_dates()
        dlg = LinkDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, url = dlg.get()
            if not url: return
            if today not in self.data: self.data[today] = []
            self.data[today].append({"desc": title, "url": url})
            self.save_data()
            self.refresh_ui()
            self.restore_expanded_state(expanded_dates)

    def open_file(self, path: str):
        if not os.path.exists(path): return QMessageBox.critical(self, "Error", "File not found!")
        os.startfile(path) if os.name == "nt" else subprocess.call(("open", path))

    def open_link(self, url: str): webbrowser.open(url)

    def open_note_popup(self, item: dict):
        expanded_dates = self.get_expanded_dates()
        dlg = NoteDialog(item.get("title", "Untitled Note"), item.get("note", ""), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, note = dlg.get()
            item["title"], item["note"] = title or "Untitled Note", note
            self.save_data()
            self.refresh_ui()
            self.restore_expanded_state(expanded_dates)

    def rename_item(self, date: str, item: dict):
        expanded_dates = self.get_expanded_dates()
        dlg = RenameDialog(item.get("desc", ""), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.value():
                item["desc"] = dlg.value()
                self.save_data()
                self.refresh_ui()
                self.restore_expanded_state(expanded_dates)

    def delete_item(self, date: str, item: dict):
        if QMessageBox.question(self, "Delete", "Delete item?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            expanded_dates = self.get_expanded_dates()
            self.data[date].remove(item)
            if not self.data[date]: del self.data[date]
            self.save_data()
            self.refresh_ui()
            self.restore_expanded_state(expanded_dates)

    def refresh_ui(self):
        while self.scroll_layout.count():
            it = self.scroll_layout.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        query = self.search_edit.text().lower().strip()
        for date in sorted(self.data.keys(), reverse=True):
            items = self.data[date]
            if query:
                # If query matches the date, show all items for that date
                if query in date.lower():
                    filtered = items
                else:
                    # Otherwise, filter items that contain the query
                    filtered = [f for f in items if query in str(f).lower()]
            else:
                filtered = items
            if not filtered: continue
            section = CollapsibleSection(date, filtered, self)
            if query: section.expand()
            self.scroll_layout.addWidget(section)
        self.scroll_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f5f5; color: #111; font-family: "Segoe UI"; }
            QLineEdit, QPlainTextEdit { padding: 6px 8px; border-radius: 6px; border: 1px solid #c9c9c9; background: #fff; }
            QPushButton#actionButton { background: #000; color: #fff; font-weight: 600; border-radius: 8px; padding: 8px; }
            QPushButton#rowButton { background: #0B5ED7; color: #fff; font-weight: 600; border-radius: 6px; padding: 6px; }
            QPushButton#headerButton { background: #e9ecef; border: 1px solid #d0d4d9; border-radius: 8px; text-align: left; padding: 10px; font-weight: 600; }
            QScrollBar:vertical { background: #666; width: 18px; border-radius: 6px; margin-left: 5px; margin-right: 5px; }
            QScrollBar::handle:vertical { background: #333; border-radius: 3px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; border: none; }
        """)

def main():
    app = QApplication(sys.argv)
    loading = LoadingScreen()
    loading.show()
    
    thread = QThread()
    worker = FileScannerWorker()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.progress.connect(loading.update_progress)
    
    def on_finished(updated_data):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)
        loading.close()
        global main_win
        main_win = MainWindow(updated_data)
        main_win.show()
        thread.quit()

    worker.finished.connect(on_finished)
    thread.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
