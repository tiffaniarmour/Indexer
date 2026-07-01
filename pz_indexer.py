import sqlite3
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox

APP_TITLE = "Project Zero - Indexer v0.2 Workspace Edition"


class IndexerApp:

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("900x650")

        self.project_root = self.find_project_root()
        self.markdown_folder = self.project_root / "Markdown Library"
        self.database_folder = self.project_root / "Database"
        self.logs_folder = self.project_root / "Logs"
        self.database_path = self.database_folder / "project_zero.db"

        self.create_widgets()
        self.show_startup_info()

    def find_project_root(self):
        current_file = Path(__file__).resolve()
        current_folder = current_file.parent

        if current_folder.name.lower() == "pz indexer":
            return current_folder.parent

        return current_folder.parent

    def create_widgets(self):
        top = Frame(self.root)
        top.pack(fill=X, padx=10, pady=10)

        Label(
            top,
            text="Project Zero Workspace Indexer",
            font=("Arial", 14, "bold")
        ).pack(anchor="w")

        Label(
            top,
            text="This version automatically reads from the Project Zero Markdown Library and writes to the shared Database folder."
        ).pack(anchor="w", pady=(4, 8))

        path_frame = Frame(self.root)
        path_frame.pack(fill=X, padx=10)

        Label(path_frame, text="Project Root:").grid(row=0, column=0, sticky="w")
        Label(path_frame, text=str(self.project_root), anchor="w").grid(row=0, column=1, sticky="w")

        Label(path_frame, text="Markdown Library:").grid(row=1, column=0, sticky="w")
        Label(path_frame, text=str(self.markdown_folder), anchor="w").grid(row=1, column=1, sticky="w")

        Label(path_frame, text="Database Output:").grid(row=2, column=0, sticky="w")
        Label(path_frame, text=str(self.database_path), anchor="w").grid(row=2, column=1, sticky="w")

        button_frame = Frame(self.root)
        button_frame.pack(fill=X, padx=10, pady=10)

        Button(
            button_frame,
            text="Start Index",
            command=self.start_index,
            width=20
        ).pack(side=LEFT)

        self.progress = ttk.Progressbar(
            self.root,
            orient="horizontal",
            mode="determinate",
            length=700
        )
        self.progress.pack(fill=X, padx=10)

        self.status = Label(
            self.root,
            text="Ready."
        )
        self.status.pack(anchor="w", padx=10, pady=5)

        self.log = Text(
            self.root,
            height=28,
            wrap=WORD
        )
        self.log.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def show_startup_info(self):
        self.log_message("Project Zero Indexer v0.2 Workspace Edition")
        self.log_message("")
        self.log_message(f"Project Root: {self.project_root}")
        self.log_message(f"Markdown Library: {self.markdown_folder}")
        self.log_message(f"Database Output: {self.database_path}")
        self.log_message(f"Logs Folder: {self.logs_folder}")
        self.log_message("")
        self.log_message("Ready to index.")

    def start_index(self):
        thread = threading.Thread(
            target=self.index_library,
            daemon=True
        )
        thread.start()

    def log_message(self, text):
        self.log.insert(END, text + "\n")
        self.log.see(END)
        self.root.update_idletasks()

    def prepare_workspace_folders(self):
        self.database_folder.mkdir(parents=True, exist_ok=True)
        self.logs_folder.mkdir(parents=True, exist_ok=True)

    def create_database(self):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            filename TEXT,
            filepath TEXT,
            word_count INTEGER,
            character_count INTEGER,
            file_size INTEGER,
            hash TEXT,
            indexed_at TEXT
        )
        """)

        conn.commit()
        return conn

    def sha256(self, filename):
        h = hashlib.sha256()

        with open(filename, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)

        return h.hexdigest()

    def write_log_file(self, lines):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_path = self.logs_folder / f"pz_indexer_{timestamp}.log"

        with open(log_path, "w", encoding="utf-8") as log_file:
            for line in lines:
                log_file.write(line + "\n")

        return log_path

    def index_library(self):
        self.prepare_workspace_folders()

        log_lines = []

        def add_log(text):
            log_lines.append(text)
            self.log_message(text)

        if not self.markdown_folder.exists():
            messagebox.showerror(
                "Missing Markdown Library",
                "The Project Zero folder must contain a folder named 'Markdown Library'."
            )
            return

        files = list(self.markdown_folder.rglob("*.md"))
        total = len(files)

        if total == 0:
            messagebox.showerror(
                "No Markdown Files",
                "No .md files were found in the Markdown Library folder."
            )
            return

        self.progress["value"] = 0
        self.progress["maximum"] = total

        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        add_log("")
        add_log("Index started.")
        add_log(f"Started At: {started_at}")
        add_log(f"Project Root: {self.project_root}")
        add_log(f"Markdown Library: {self.markdown_folder}")
        add_log(f"Database: {self.database_path}")
        add_log(f"Found {total} Markdown files.")
        add_log("")

        conn = self.create_database()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM conversations")
        conn.commit()

        indexed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for i, file in enumerate(files, start=1):
            self.progress["value"] = i
            self.status.config(text=f"Indexing {i} of {total}")

            text = file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            words = len(text.split())
            chars = len(text)
            size = file.stat().st_size
            digest = self.sha256(file)
            title = file.stem

            cursor.execute("""
            INSERT INTO conversations
            (
                title,
                filename,
                filepath,
                word_count,
                character_count,
                file_size,
                hash,
                indexed_at
            )
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                file.name,
                str(file),
                words,
                chars,
                size,
                digest,
                indexed_at
            ))

            add_log(f"[{i}/{total}] {title}")

        conn.commit()
        conn.close()

        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.status.config(text="Finished.")

        add_log("")
        add_log("Index complete.")
        add_log(f"Finished At: {finished_at}")
        add_log(f"Database saved to: {self.database_path}")

        log_path = self.write_log_file(log_lines)
        self.log_message(f"Log saved to: {log_path}")

        messagebox.showinfo(
            "Complete",
            f"Library successfully indexed.\n\nDatabase saved to:\n{self.database_path}\n\nLog saved to:\n{log_path}"
        )


if __name__ == "__main__":
    root = Tk()
    app = IndexerApp(root)
    root.mainloop()

