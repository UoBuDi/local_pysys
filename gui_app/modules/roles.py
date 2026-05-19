from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QComboBox, QHeaderView, QAbstractItemView,
    QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class RoleEditDialog(QDialog):
    def __init__(self, parent=None, role_data=None):
        super().__init__(parent)
        self.role_data = role_data or {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑角色" if self.role_data.get("id") else "新增角色")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.name = QLineEdit()
        self.name.setText(self.role_data.get("name", ""))
        layout.addRow("角色名称:", self.name)
        
        self.code = QLineEdit()
        self.code.setText(self.role_data.get("code", ""))
        layout.addRow("角色编码:", self.code)
        
        self.status = QComboBox()
        self.status.addItems(["启用", "禁用"])
        self.status.setCurrentIndex(0 if self.role_data.get("status", 1) == 1 else 1)
        layout.addRow("状态:", self.status)
        
        self.remark = QTextEdit()
        self.remark.setMaximumHeight(80)
        self.remark.setText(self.role_data.get("remark", ""))
        layout.addRow("备注:", self.remark)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
    
    def get_data(self):
        return {
            "name": self.name.text(),
            "code": self.code.text(),
            "status": 1 if self.status.currentIndex() == 0 else 0,
            "remark": self.remark.toPlainText()
        }
    
    def save(self):
        if not self.name.text():
            QMessageBox.warning(self, "错误", "角色名称不能为空")
            return
        self.accept()


class RoleListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("新增角色")
        add_btn.clicked.connect(self.add_role)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_role)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_role)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "角色名称", "角色编码", "状态", "创建时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
    
    def load_data(self):
        result = api_client.get("/api/roles/")
        
        if result.get("code") == 200:
            roles = result.get("data", [])
            self.table.setRowCount(len(roles))
            
            for row, role in enumerate(roles):
                self.table.setItem(row, 0, QTableWidgetItem(str(role.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(role.get("name", "")))
                self.table.setItem(row, 2, QTableWidgetItem(role.get("code", "")))
                self.table.setItem(row, 3, QTableWidgetItem("启用" if role.get("status") == 1 else "禁用"))
                self.table.setItem(row, 4, QTableWidgetItem(role.get("create_time", "")))
        else:
            QMessageBox.warning(self, "错误", f"获取角色列表失败: {result.get('message', '未知错误')}")
    
    def add_role(self):
        dialog = RoleEditDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            result = api_client.post("/api/roles/", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "角色创建成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"创建失败: {result.get('message', '未知错误')}")
    
    def edit_role(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的角色")
            return
        
        row = selected[0].row()
        role_id = self.table.item(row, 0).text()
        
        role_data = {
            "id": int(role_id),
            "name": self.table.item(row, 1).text(),
            "code": self.table.item(row, 2).text(),
            "status": 1 if self.table.item(row, 3).text() == "启用" else 0
        }
        
        dialog = RoleEditDialog(self, role_data)
        if dialog.exec():
            data = dialog.get_data()
            result = api_client.put(f"/api/roles/{role_id}", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "角色更新成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"更新失败: {result.get('message', '未知错误')}")
    
    def delete_role(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的角色")
            return
        
        row = selected[0].row()
        role_id = self.table.item(row, 0).text()
        role_name = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除角色 '{role_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.delete(f"/api/roles/{role_id}")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "角色删除成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"删除失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_data()
