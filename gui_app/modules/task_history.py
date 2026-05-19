from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class TaskHistoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        filter_group = QGroupBox("筛选条件")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("任务名称:"))
        self.filter_task = QLineEdit()
        self.filter_task.setPlaceholderText("输入任务名称")
        filter_layout.addWidget(self.filter_task)
        
        filter_layout.addWidget(QLabel("状态:"))
        self.filter_status = QComboBox()
        self.filter_status.addItem("全部", "")
        self.filter_status.addItem("成功", "success")
        self.filter_status.addItem("失败", "failed")
        filter_layout.addWidget(self.filter_status)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(search_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_filter)
        filter_layout.addWidget(reset_btn)
        
        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "任务名称", "开始时间", "结束时间", "状态", "执行结果"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_data(self):
        result = api_client.get("/api/task-execution-history/", {
            "task_name": self.filter_task.text(),
            "status": self.filter_status.currentData()
        })
        
        if result.get("code") == 200:
            history = result.get("data", [])
            self.table.setRowCount(len(history))
            
            for row, item in enumerate(history):
                self.table.setItem(row, 0, QTableWidgetItem(str(item.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(item.get("task_name", "")))
                self.table.setItem(row, 2, QTableWidgetItem(item.get("start_time", "-")))
                self.table.setItem(row, 3, QTableWidgetItem(item.get("end_time", "-")))
                self.table.setItem(row, 4, QTableWidgetItem(item.get("status", "")))
                self.table.setItem(row, 5, QTableWidgetItem(item.get("result", "-")))
        else:
            QMessageBox.warning(self, "错误", f"获取执行历史失败: {result.get('message', '未知错误')}")
    
    def reset_filter(self):
        self.filter_task.clear()
        self.filter_status.setCurrentIndex(0)
        self.load_data()
    
    def refresh(self):
        self.load_data()
