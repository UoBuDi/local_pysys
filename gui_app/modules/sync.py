from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QProgressBar, QTextEdit,
    QDateEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtCore import QDate
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class SyncWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_status()
        self.load_months()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_status)
        self.timer.start(3000)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        status_group = QGroupBox("同步状态")
        status_layout = QFormLayout()
        
        self.status_label = QLabel("未知")
        status_layout.addRow("当前状态:", self.status_label)
        
        self.progress_label = QLabel("0%")
        status_layout.addRow("进度:", self.progress_label)
        
        self.current_month_label = QLabel("-")
        status_layout.addRow("当前月份:", self.current_month_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        control_group = QGroupBox("同步控制")
        control_layout = QHBoxLayout()
        
        start_btn = QPushButton("启动同步")
        start_btn.clicked.connect(self.start_sync)
        control_layout.addWidget(start_btn)
        
        pause_btn = QPushButton("暂停同步")
        pause_btn.clicked.connect(self.pause_sync)
        control_layout.addWidget(pause_btn)
        
        stop_btn = QPushButton("停止同步")
        stop_btn.clicked.connect(self.stop_sync)
        control_layout.addWidget(stop_btn)
        
        force_stop_btn = QPushButton("强制停止")
        force_stop_btn.clicked.connect(self.force_stop_sync)
        control_layout.addWidget(force_stop_btn)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        months_group = QGroupBox("可同步月份")
        months_layout = QVBoxLayout()
        
        self.months_table = QTableWidget()
        self.months_table.setColumnCount(1)
        self.months_table.setHorizontalHeaderLabels(["月份"])
        self.months_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.months_table.setMaximumHeight(200)
        months_layout.addWidget(self.months_table)
        
        months_group.setLayout(months_layout)
        layout.addWidget(months_group)
        
        layout.addStretch()
    
    def load_status(self):
        result = api_client.get("/api/sync/status/")
        
        if result.get("code") == 200:
            data = result.get("data", {})
            
            status = data.get("status", "idle")
            status_map = {
                "idle": "空闲",
                "running": "运行中",
                "paused": "已暂停",
                "stopped": "已停止"
            }
            self.status_label.setText(status_map.get(status, status))
            
            progress = data.get("progress", 0)
            self.progress_label.setText(f"{progress}%")
            
            current_month = data.get("current_month", "-")
            self.current_month_label.setText(current_month or "-")
    
    def load_months(self):
        result = api_client.get("/api/sync/months/")
        
        if result.get("code") == 200:
            months = result.get("data", [])
            self.months_table.setRowCount(len(months))
            
            for row, month in enumerate(months):
                self.months_table.setItem(row, 0, QTableWidgetItem(str(month)))
    
    def start_sync(self):
        result = api_client.post("/api/start-sync/")
        if result.get("code") == 200:
            QMessageBox.information(self, "成功", "同步任务已启动")
            self.load_status()
        else:
            QMessageBox.warning(self, "错误", f"启动失败: {result.get('message', '未知错误')}")
    
    def pause_sync(self):
        result = api_client.post("/api/pause-sync/")
        if result.get("code") == 200:
            QMessageBox.information(self, "成功", "同步任务已暂停")
            self.load_status()
        else:
            QMessageBox.warning(self, "错误", f"暂停失败: {result.get('message', '未知错误')}")
    
    def stop_sync(self):
        result = api_client.post("/api/stop-sync/")
        if result.get("code") == 200:
            QMessageBox.information(self, "成功", "同步任务已停止")
            self.load_status()
        else:
            QMessageBox.warning(self, "错误", f"停止失败: {result.get('message', '未知错误')}")
    
    def force_stop_sync(self):
        reply = QMessageBox.question(
            self, "确认强制停止",
            "强制停止可能会丢失数据，确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.post("/api/force-stop-sync/")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "同步任务已强制停止")
                self.load_status()
            else:
                QMessageBox.warning(self, "错误", f"强制停止失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_status()
        self.load_months()
    
    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)
