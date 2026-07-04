import sys
import os
import time
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QAbstractItemView,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
import cloudscraper

class DownloadTask:
    def __init__(self, link, save_dir):
        self.link = link.strip()
        self.save_dir = save_dir
        
        self.file_id = self.link.split('/')[-1].split('#')[0]
        self.filename = self.link.split('#')[-1] if '#' in self.link else self.file_id
        self.filepath = os.path.join(self.save_dir, self.filename)
        
        self.status = "Pending"  # Pending, Starting..., Downloading, Paused, Cancelled, Completed, Error
        self.progress = 0.0
        self.speed = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        
        self.pause_flag = False
        self.cancel_flag = False
        self.row_idx = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FuckingFast Downloader - UI (PyQt6)")
        self.resize(850, 600)
        
        self.tasks = []
        self.max_workers = 3
        self.scraper = cloudscraper.create_scraper(browser='chrome')
        
        self.setup_ui()
        
        # Start Background Download Manager
        self.manager_thread = threading.Thread(target=self.download_manager, daemon=True)
        self.manager_thread.start()
        
        # UI Updater Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(500) # update every 500ms

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 1. Directory Section
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Save Directory:"))
        self.dir_input = QLineEdit(os.path.abspath("."))
        dir_layout.addWidget(self.dir_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_dir)
        dir_layout.addWidget(browse_btn)
        main_layout.addLayout(dir_layout)
        
        # 2. Links Section
        main_layout.addWidget(QLabel("Paste Links Here (one per line):"))
        self.text_links = QTextEdit()
        self.text_links.setMaximumHeight(100)
        main_layout.addWidget(self.text_links)
        
        add_btn = QPushButton("Add Links to Queue")
        add_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 6px;")
        add_btn.clicked.connect(self.add_links)
        main_layout.addWidget(add_btn)
        
        # 3. Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Filename", "Status", "Progress", "Speed", "Size"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table)
        
        # 4. Controls Section
        control_layout = QHBoxLayout()
        resume_btn = QPushButton("Resume Selected")
        resume_btn.clicked.connect(self.resume_selected)
        control_layout.addWidget(resume_btn)
        
        pause_btn = QPushButton("Pause Selected")
        pause_btn.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
        pause_btn.clicked.connect(self.pause_selected)
        control_layout.addWidget(pause_btn)
        
        cancel_btn = QPushButton("Cancel Selected")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        cancel_btn.clicked.connect(self.cancel_selected)
        control_layout.addWidget(cancel_btn)
        
        control_layout.addStretch()
        
        clear_btn = QPushButton("Clear Completed/Cancelled")
        clear_btn.clicked.connect(self.clear_finished)
        control_layout.addWidget(clear_btn)
        
        main_layout.addLayout(control_layout)

    def browse_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Directory", self.dir_input.text())
        if folder:
            self.dir_input.setText(folder)

    def add_links(self):
        text = self.text_links.toPlainText().strip()
        if not text:
            return
            
        links = [line.strip() for line in text.split('\n') if line.strip() and line.startswith('http')]
        save_dir = self.dir_input.text()
        
        for link in links:
            task = DownloadTask(link, save_dir)
            row = self.table.rowCount()
            self.table.insertRow(row)
            task.row_idx = row
            
            self.table.setItem(row, 0, QTableWidgetItem(task.filename))
            self.table.setItem(row, 1, QTableWidgetItem(task.status))
            self.table.setItem(row, 2, QTableWidgetItem("0%"))
            self.table.setItem(row, 3, QTableWidgetItem("-"))
            self.table.setItem(row, 4, QTableWidgetItem("-"))
            
            self.tasks.append(task)
            
        self.text_links.clear()

    def get_selected_tasks(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        return [t for t in self.tasks if t.row_idx in selected_rows]

    def pause_selected(self):
        for task in self.get_selected_tasks():
            if task.status == "Downloading":
                task.pause_flag = True
                task.status = "Pausing..."

    def resume_selected(self):
        for task in self.get_selected_tasks():
            if task.status in ("Paused", "Error", "Cancelled"):
                task.pause_flag = False
                task.cancel_flag = False
                task.status = "Pending"

    def cancel_selected(self):
        for task in self.get_selected_tasks():
            if task.status in ("Downloading", "Pending", "Paused", "Starting..."):
                task.cancel_flag = True
                task.pause_flag = False
                task.status = "Cancelled"

    def clear_finished(self):
        to_remove = [t for t in self.tasks if t.status in ("Completed", "Cancelled", "Error")]
        # Remove from bottom to top to preserve indices
        to_remove.sort(key=lambda t: t.row_idx, reverse=True)
        for t in to_remove:
            self.table.removeRow(t.row_idx)
            self.tasks.remove(t)
            
        # Update row indices
        for idx, t in enumerate(self.tasks):
            t.row_idx = idx

    def update_ui(self):
        for task in self.tasks:
            if task.row_idx is None:
                continue
            prog_str = f"{task.progress:.1f}%"
            speed_str = f"{task.speed:.2f} MB/s" if task.status == "Downloading" else "-"
            size_mb = task.total_bytes / (1024*1024)
            dl_mb = task.downloaded_bytes / (1024*1024)
            size_str = f"{dl_mb:.1f} / {size_mb:.1f} MB" if task.total_bytes > 0 else "-"
            
            self.table.item(task.row_idx, 1).setText(task.status)
            self.table.item(task.row_idx, 2).setText(prog_str)
            self.table.item(task.row_idx, 3).setText(speed_str)
            self.table.item(task.row_idx, 4).setText(size_str)

    def download_manager(self):
        while True:
            active = sum(1 for t in self.tasks if t.status in ("Downloading", "Starting..."))
            if active < self.max_workers:
                for task in self.tasks:
                    if task.status == "Pending":
                        task.status = "Starting..."
                        threading.Thread(target=self.download_worker, args=(task,), daemon=True).start()
                        active += 1
                        if active >= self.max_workers:
                            break
            time.sleep(1)

    def get_direct_link(self, task):
        try:
            res = self.scraper.get(task.link)
            if res.status_code != 200:
                return None
            
            post_url = f"https://fuckingfast.co/f/{task.file_id}/go"
            headers = {
                'HX-Request': 'true',
                'HX-Target': '',
                'HX-Current-URL': task.link,
                'Referer': task.link
            }
            res2 = self.scraper.post(post_url, headers=headers)
            if res2.status_code == 200:
                return res2.headers.get('Hx-Redirect')
        except Exception:
            return None
        return None

    def download_worker(self, task):
        dl_url = self.get_direct_link(task)
        if not dl_url:
            if not task.cancel_flag:
                task.status = "Error"
            return
            
        if task.cancel_flag:
            task.status = "Cancelled"
            return

        task.status = "Downloading"
        
        try:
            initial_size = 0
            if os.path.exists(task.filepath):
                initial_size = os.path.getsize(task.filepath)
                
            head_req = self.scraper.head(dl_url)
            total_size = int(head_req.headers.get('content-length', 0))
            task.total_bytes = total_size
            
            if initial_size > 0 and initial_size == total_size:
                task.downloaded_bytes = total_size
                task.progress = 100
                task.status = "Completed"
                return
                
            resume_header = {}
            mode = 'wb'
            if initial_size > 0:
                resume_header = {'Range': f'bytes={initial_size}-'}
                mode = 'ab'
                
            with self.scraper.get(dl_url, stream=True, headers=resume_header) as r:
                if r.status_code not in (200, 206):
                    task.status = "Error"
                    return
                    
                if r.status_code == 200 and initial_size > 0:
                    mode = 'wb'
                    initial_size = 0
                    
                task.downloaded_bytes = initial_size
                if total_size == 0 and 'content-length' in r.headers:
                    task.total_bytes = int(r.headers['content-length']) + initial_size
                elif total_size == 0:
                    task.total_bytes = 0
                    
                start_time = time.time()
                last_time = start_time
                bytes_since_last = 0
                
                with open(task.filepath, mode) as f:
                    for chunk in r.iter_content(chunk_size=8192*8):
                        if task.pause_flag:
                            task.status = "Paused"
                            task.speed = 0
                            return
                        if task.cancel_flag:
                            task.status = "Cancelled"
                            task.speed = 0
                            return
                            
                        if chunk:
                            f.write(chunk)
                            size = len(chunk)
                            task.downloaded_bytes += size
                            bytes_since_last += size
                            
                            now = time.time()
                            if now - last_time > 0.5:
                                task.speed = (bytes_since_last / (now - last_time)) / (1024*1024)
                                if task.total_bytes > 0:
                                    task.progress = (task.downloaded_bytes / task.total_bytes) * 100
                                last_time = now
                                bytes_since_last = 0
                
                task.progress = 100
                task.speed = 0
                task.status = "Completed"
                
        except Exception as e:
            if not task.cancel_flag and not task.pause_flag:
                task.status = "Error"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
