import os
import sqlite3
import hashlib
import threading
from pathlib import Path
from tkinter import *
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Project Zero - Indexer v0.1"


class IndexerApp:

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("900x650")

        self.folder = StringVar()

        self.create_widgets()

    def create_widgets(self):

        top = Frame(self.root)
        top.pack(fill=X, padx=10, pady=10)

        Label(top, text="Markdown Library").pack(anchor="w")

        Entry(
            top,
            textvariable=self.folder,
            width=80
        ).pack(side=LEFT, fill=X, expand=True)

        Button(
            top,
            text="Browse...",
            command=self.choose_folder
        ).pack(side=LEFT, padx=5)

        Button(
            top,
            text="Start Index",
            command=self.start_index
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

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder.set(folder)

    def start_index(self):

        if not self.folder.get():
            messagebox.showerror(
                "Error",
                "Please select a Markdown folder."
            )
            return

        thread = threading.Thread(
            target=self.index_library,
            daemon=True
        )

        thread.start()

    def log_message(self, text):

        self.log.insert(END, text + "\n")
        self.log.see(END)

    def create_database(self):

        conn = sqlite3.connect("project_zero.db")

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

            hash TEXT

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

    def index_library(self):

        folder = Path(self.folder.get())

        files = list(folder.rglob("*.md"))

        total = len(files)

        conn = self.create_database()

        cursor = conn.cursor()

        self.progress["maximum"] = total

        for i, file in enumerate(files, start=1):

            self.progress["value"] = i

            self.status.config(
                text=f"Indexing {i} of {total}"
            )

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
                hash
            )

            VALUES
            (?, ?, ?, ?, ?, ?, ?)

            """,

            (
                title,
                file.name,
                str(file),
                words,
                chars,
                size,
                digest
            )

            )

            self.log_message(
                f"[{i}/{total}] {title}"
            )

            self.root.update_idletasks()

        conn.commit()

        conn.close()

        self.status.config(
            text="Finished."
        )

        self.log_message("")
        self.log_message("Index Complete.")

        messagebox.showinfo(
            "Complete",
            "Library successfully indexed."
        )


if __name__ == "__main__":

    root = Tk()

    app = IndexerApp(root)

    root.mainloop()