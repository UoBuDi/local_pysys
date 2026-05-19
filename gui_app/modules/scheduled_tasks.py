from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QSpinBox, QDialog,
    QTimeEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QTime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class TaskEditDialog(QDialog):
    def __init__(self, parent=None, task_data=None):
        super().__init__(parent)
        self.task_data = task_data or {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑定时任务")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.name = QLineEdit()
        self.name.setText(self.task_data.get("name", ""))
        self.name.setReadOnly(True)
        layout.addRow("任务名称:", self.name)
        
        self.cron_expr = QLineEdit()
        self.cron_expr.setText(self.task_data.get("cron_expression", ""))
        layout.addRow("Cron表达式:", self.cron_expr)
        
        self.is_enabled = QCheckBox("启用")
        self.is_enabled.setChecked(self.task_data.get("is_enabled", False))
        layout.addRow(self.is_enabled)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
    
    def get_data(self):
        return {
            "cron_expression": self.cron_expr.text(),
            "is_enabled": self.is_enabled.isChecked()
        }


class ScheduledTasksWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(refresh_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_task)
        btn_layout.addWidget(edit_btn)
        
        run_btn = QPushButton("立即执行")
        run_btn.clicked.connect(self.run_task)
        btn_layout.addWidget(run_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "任务名称", "Cron表达式", "状态", "上次执行时间", "下次执行时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_data(self):
        result = api_client.get("/api/scheduled-tasks/")
        
        if result.get("code") == 200:
            tasks = result.get("data", [])
            self.table.setRowCount(len(tasks))
            
            for row, task in enumerate(tasks):
                self.table.setItem(row, 0, QTableWidgetItem(str(task.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(task.get("name", "")))
                self.table.setItem(row, 2, QTableWidgetItem(task.get("cron_expression", "")))
                self.table.setItem(row, 3, QTableWidgetItem("启用" if task.get("is_enabled") else "禁用"))
                self.table.setItem(row, 4, QTableWidgetItem(task.get("last_run_time", "-")))
                self.table.setItem(row, 5, QTableWidgetItem(task.get("next_run_time", "-")))
        else:
            QMessageBox.warning(self, "错误", f"获取任务列表失败: {result.get('message', '未知错误')}")
    
    def edit_task(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的任务")
            return
        
        row = selected[0].row()
        task_data = {
            "id": int(self.table.item(row, 0).text()),
            "name": self.table.item(row, 1).text(),
            "cron_expression": self.table.item(row, 2).text(),
            "is_enabled": self.table.item(row, 3).text() == "启用"
        }
        
        dialog = TaskEditDialog(self, task_data)
        if dialog.exec():
            data = dialog.get_data()
            task_id = task_data["id"]
            result = api_client.put(f"/api/scheduled-tasks/{task_id}", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "任务更新成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"更新失败: {result.get('message', '未知错误')}")
    
    def run_task(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要执行的任务")
            return
        
        row = selected[0].row()
        task_name = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认执行",
            f"确定要立即执行任务 '{task_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.post(f"/api/scheduled-tasks/{task_name}/run")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "任务已开始执行")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"执行失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_data()
