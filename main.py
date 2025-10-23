import os
import sys
from contextlib import contextmanager
from io import StringIO

from PySide6 import QtCore, QtGui, QtWidgets

from utils.formatting import format_size
from unused_files.modelformats import unused_model_formats
from unused_files.content import unused_content
from unused_files.remove_game_files import remove_game_files
from material_compression.resize_and_compress import resize_and_compress
from material_compression.resize_png import clamp_pngs
from material_compression.remove_mipmaps import remove_mipmaps
from sound_compression.wav_to_mp3 import wav_to_mp3
from sound_compression.wav_to_ogg import wav_to_ogg
from sound_compression.mp3_to_ogg import mp3_to_ogg
from sound_compression.trim_empty import trim_empty_audio
from mapping.find_map_content import find_map_content


class SignalStream(QtCore.QObject):
    text_emitted = QtCore.Signal(str)

    def write(self, text: str):
        if text:
            self.text_emitted.emit(str(text))

    def flush(self):
        pass


@contextmanager
def redirect_stdout_stderr(callback):
    """Temporarily redirect stdout/stderr to a Qt signal callback."""
    old_out, old_err = sys.stdout, sys.stderr
    stream = SignalStream()
    stream.text_emitted.connect(callback)
    sys.stdout = stream
    sys.stderr = stream
    try:
        yield
    finally:
        sys.stdout = old_out
        sys.stderr = old_err


class TaskWorker(QtCore.QObject):
    started = QtCore.Signal(str)
    log = QtCore.Signal(str)
    finished = QtCore.Signal(str)
    failed = QtCore.Signal(str)

    def __init__(self, fn, *args, description: str = "Working...", **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.description = description

    @QtCore.Slot()
    def run(self):
        self.started.emit(self.description)
        try:
            with redirect_stdout_stderr(self.log.emit):
                result = self.fn(*self.args, **self.kwargs)
            msg = "Done."
            # If the function returned something meaningful, include it.
            if isinstance(result, tuple):
                try:
                    # Common pattern in this repo is (size, count)
                    size, count = result
                    msg = f"Done. Files: {count}, Size: {format_size(size)}"
                except Exception:
                    pass
            self.finished.emit(msg)
        except Exception as e:
            self.failed.emit(f"Error: {e}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GM Addon Optimization Tools")
        self.resize(980, 720)

        self.thread: QtCore.QThread | None = None
        self.worker: TaskWorker | None = None

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main_layout = QtWidgets.QVBoxLayout(central)

        # Folder picker
        folder_row = QtWidgets.QHBoxLayout()
        self.folder_edit = QtWidgets.QLineEdit()
        self.folder_edit.setPlaceholderText("Absolute path to folder…")
        browse_btn = QtWidgets.QPushButton("Browse…")
        browse_btn.clicked.connect(self.choose_folder)
        folder_row.addWidget(QtWidgets.QLabel("Content folder:"))
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(browse_btn)
        main_layout.addLayout(folder_row)

        # Actions grid
        actions_widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(actions_widget)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        row = 0
        def add_button(text, handler):
            nonlocal row
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(handler)
            grid.addWidget(btn, row // 2, row % 2)
            row += 1
            return btn

        # Texture / materials
        add_button("Clamp VTF file sizes", self.on_clamp_vtf)
        add_button("Use DXT for VTFs", self.on_use_dxt)
        add_button("Remove mipmaps (viewmodel-friendly)", self.on_remove_mipmaps)
        add_button("Clamp PNG file sizes", self.on_clamp_png)
        add_button("Resave VTF files (autorefresh)", self.on_resave_vtf)

        # Audio
        add_button(".wav to .ogg (skips looped/cued)", self.on_wav_to_ogg)
        add_button(".wav to .mp3 (skips looped/cued)", self.on_wav_to_mp3)
        add_button(".mp3 to .ogg", self.on_mp3_to_ogg)
        add_button("Trim empty audio tail", self.on_trim_empty_audio)

        # Cleanup / mapping
        add_button("Unused model formats (scan/remove)", self.on_unused_model_formats)
        add_button("Find unused content (WIP)", self.on_unused_content)
        add_button("Remove files already in game (HL2/CSS)", self.on_remove_game_files)
        add_button("Find and copy content used by .vmf", self.on_find_map_content)

        main_layout.addWidget(actions_widget)

        # Progress + Log
        progress_row = QtWidgets.QHBoxLayout()
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setVisible(False)
        progress_row.addWidget(self.progress)
        main_layout.addLayout(progress_row)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Status and output will appear here…")
        main_layout.addWidget(self.log, 1)

        # A little nicer default look
        QtWidgets.QApplication.setStyle("Fusion")
        self.apply_dark_palette()

    # ------------- Theming -------------
    def apply_dark_palette(self):
        palette = QtGui.QPalette()
        base = QtGui.QColor(45, 45, 45)
        alt = QtGui.QColor(53, 53, 53)
        text = QtGui.QColor(220, 220, 220)
        highlight = QtGui.QColor(42, 130, 218)

        palette.setColor(QtGui.QPalette.Window, alt)
        palette.setColor(QtGui.QPalette.WindowText, text)
        palette.setColor(QtGui.QPalette.Base, base)
        palette.setColor(QtGui.QPalette.AlternateBase, alt)
        palette.setColor(QtGui.QPalette.ToolTipBase, text)
        palette.setColor(QtGui.QPalette.ToolTipText, text)
        palette.setColor(QtGui.QPalette.Text, text)
        palette.setColor(QtGui.QPalette.Button, alt)
        palette.setColor(QtGui.QPalette.ButtonText, text)
        palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        palette.setColor(QtGui.QPalette.Highlight, highlight)
        palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        self.setPalette(palette)

    # ------------- Helpers -------------
    def current_folder(self) -> str:
        return (self.folder_edit.text() or "").strip().strip('"')

    def ensure_folder(self) -> str | None:
        folder = self.current_folder()
        if not folder or not os.path.exists(folder):
            QtWidgets.QMessageBox.warning(self, "Folder missing", "Please choose a valid content folder first.")
            return None
        return folder

    def choose_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select content folder")
        if folder:
            self.folder_edit.setText(folder)

    def ask_int(self, title: str, label: str, default: int = 1024) -> int | None:
        value, ok = QtWidgets.QInputDialog.getInt(self, title, label, value=default, minValue=1, maxValue=10_000_000, step=1)
        return value if ok else None

    def ask_yes_no(self, title: str, text: str) -> bool:
        res = QtWidgets.QMessageBox.question(self, title, text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        return res == QtWidgets.QMessageBox.Yes

    def ask_file(self, title: str, filter_str: str) -> str | None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, filter=filter_str)
        return path or None

    def ask_directory(self, title: str) -> str | None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, title)
        return path or None

    def start_task(self, description: str, fn, *args, **kwargs):
        if self.thread is not None:
            QtWidgets.QMessageBox.information(self, "Busy", "A task is already running. Please wait for it to finish.")
            return
        self.progress.setVisible(True)
        self.log_append(f"Starting: {description}\n")

        self.thread = QtCore.QThread()
        self.worker = TaskWorker(fn, *args, description=description, **kwargs)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.started.connect(lambda msg: None)
        self.worker.log.connect(self.log_append)
        self.worker.finished.connect(self.on_task_finished)
        self.worker.failed.connect(self.on_task_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup_thread)

        self.thread.start()

    def cleanup_thread(self):
        self.thread = None
        self.worker = None
        self.progress.setVisible(False)

    def on_task_finished(self, msg: str):
        self.log_append(msg + "\n")

    def on_task_failed(self, msg: str):
        self.log_append(msg + "\n")
        QtWidgets.QMessageBox.critical(self, "Task failed", msg)

    def log_append(self, text: str):
        self.log.moveCursor(QtGui.QTextCursor.End)
        self.log.insertPlainText(text)
        self.log.moveCursor(QtGui.QTextCursor.End)

    # ------------- Action handlers -------------
    def on_unused_model_formats(self):
        folder = self.ensure_folder()
        if not folder:
            return
        remove = self.ask_yes_no("Remove models?", "Do you want to remove the unused model formats?")

        def task():
            size, count = unused_model_formats(folder, remove)
            print((f"Removed {count} unused model formats, saving {format_size(size)}") if remove else (f"Found {count} unused model formats, taking up {format_size(size)}"))
            return size, count

        self.start_task("Unused model formats", task)

    def on_unused_content(self):
        folder = self.ensure_folder()
        if not folder:
            return
        remove = self.ask_yes_no("Remove files?", "Do you want to remove the found unused files? This isn't 100% and can remove used files!")

        def task():
            size, count = unused_content(folder, remove)
            print((f"Removed {count} unused files, saving {format_size(size)}") if remove else (f"Found {count} unused files, taking up {format_size(size)}"))
            return size, count

        self.start_task("Find unused content", task)

    def on_remove_game_files(self):
        folder = self.ensure_folder()
        if not folder:
            return
        remove = self.ask_yes_no("Remove files?", "Do you want to remove the found files? This will remove files that are already provided by the game.")
        gamefolder = self.ask_directory("Absolute path to game folder (eg C:/Program Files (x86)/Steam/steamapps/common/GarrysMod)")
        if not gamefolder or not os.path.exists(os.path.join(gamefolder, "gmod.exe")):
            QtWidgets.QMessageBox.warning(self, "Invalid game folder", "The selected folder doesn't contain gmod.exe")
            return

        self.start_task("Remove files already in game", remove_game_files, folder, gamefolder, remove)

    def on_clamp_vtf(self):
        folder = self.ensure_folder()
        if not folder:
            return
        size = self.ask_int("Clamp VTF size", "Clamp size (pixels)", default=1024)
        if size is None:
            return
        self.start_task("Clamp VTF file sizes", resize_and_compress, folder, int(size))

    def on_use_dxt(self):
        folder = self.ensure_folder()
        if not folder:
            return
        # Use a very large clamp to force DXT path
        self.start_task("Use DXT for VTFs", resize_and_compress, folder, 1_000_000)

    def on_remove_mipmaps(self):
        folder = self.ensure_folder()
        if not folder:
            return
        self.start_task("Remove mipmaps", remove_mipmaps, folder)

    def on_clamp_png(self):
        folder = self.ensure_folder()
        if not folder:
            return
        size = self.ask_int("Clamp PNG size", "Clamp size (pixels)", default=512)
        if size is None:
            return
        self.start_task("Clamp PNG file sizes", clamp_pngs, folder, int(size))

    def on_wav_to_mp3(self):
        folder = self.ensure_folder()
        if not folder:
            return
        self.start_task(".wav to .mp3", wav_to_mp3, folder)

    def on_wav_to_ogg(self):
        folder = self.ensure_folder()
        if not folder:
            return
        self.start_task(".wav to .ogg", wav_to_ogg, folder)

    def on_mp3_to_ogg(self):
        folder = self.ensure_folder()
        if not folder:
            return
        self.start_task(".mp3 to .ogg", mp3_to_ogg, folder)

    def on_trim_empty_audio(self):
        folder = self.ensure_folder()
        if not folder:
            return
        self.start_task("Trim empty audio", trim_empty_audio, folder)

    def on_find_map_content(self):
        folder = self.ensure_folder()
        if not folder:
            return
        map_file = self.ask_file("Select .vmf map file", "VMF files (*.vmf)")
        if not map_file or not map_file.endswith(".vmf"):
            QtWidgets.QMessageBox.warning(self, "Invalid map file", "Please select a valid .vmf file.")
            return
        dest_folder = self.ask_directory("Folder to copy found content to (will be created if it doesn't exist)")
        if not dest_folder:
            QtWidgets.QMessageBox.warning(self, "Invalid destination", "Please select a destination folder.")
            return
        os.makedirs(dest_folder, exist_ok=True)
        self.start_task("Find/copy content used by map", find_map_content, folder, dest_folder, map_file)

    def on_resave_vtf(self):
        folder = self.ensure_folder()
        if not folder:
            return

        def task():
            count = 0
            for root, _, files in os.walk(folder):
                for filename in files:
                    if filename.lower().endswith(".vtf"):
                        file_path = os.path.join(root, filename)
                        try:
                            with open(file_path, "r+b") as f:
                                data = f.read()
                                f.seek(0)
                                f.write(data)
                                f.truncate()
                            count += 1
                        except Exception as e:
                            print(f"Failed to resave {file_path}: {e}")
            print(f"Resaved {count} VTF files.")
            return 0, count

        self.start_task("Resave VTF files", task)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
