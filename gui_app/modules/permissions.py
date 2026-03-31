from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QComboBox, QHeaderView, QAbstractItemView,
    QTextEdit
)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class PermissionEditDialog(QDialog):
    def __init__(self, parent=None, perm_data=None):
        super().__init__(parent)
        self.perm_data = perm_data or {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑权限" if self.perm_data.get("id") else "新增权限")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.name = QLineEdit()
        self.name.setText(self.perm_data.get("name", ""))
        layout.addRow("权限名称:", self.name)
        
        self.code = QLineEdit()
        self.code.setText(self.perm_data.get("code", ""))
        layout.addRow("权限编码:", self.code)
        
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        self.description.setText(self.perm_data.get("description", ""))
        layout.addRow("描述:", self.description)
        
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
            "description": self.description.toPlainText()
        }
    
    def save(self):
        if not self.name.text() or not self.code.text():
            QMessageBox.warning(self, "错误", "权限名称和编码不能为空")
            return
        self.accept()


class PermissionListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("新增权限")
        add_btn.clicked.connect(self.add_permission)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_permission)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_permission)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ID", "权限名称", "权限编码", "描述"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
    
    def load_data(self):
        result = api_client.get("/api/permissions/")
        
        if result.get("code") == 200:
            perms = result.get("data", [])
            self.table.setRowCount(len(perms))
            
            for row, perm in enumerate(perms):
                self.table.setItem(row, 0, QTableWidgetItem(str(perm.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(perm.get("name", "")))
                self.table.setItem(row, 2, QTableWidgetItem(perm.get("code", "")))
                self.table.setItem(row, 3, QTableWidgetItem(perm.get("description", "")))
        else:
            QMessageBox.warning(self, "错误", f"获取权限列表失败: {result.get('message', '未知错误')}")
    
    def add_permission(self):
        dialog = PermissionEditDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            result = api_client.post("/api/permissions/", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "权限创建成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"创建失败: {result.get('message', '未知错误')}")
    
    def edit_permission(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的权限")
            return
        
        row = selected[0].row()
        perm_id = self.table.item(row, 0).text()
        
        perm_data = {
            "id": int(perm_id),
            "name": self.table.item(row, 1).text(),
            "code": self.table.item(row, 2).text(),
            "description": self.table.item(row, 3).text()
        }
        
        dialog = PermissionEditDialog(self, perm_data)
        if dialog.exec():
            data = dialog.get_data()
            result = api_client.put(f"/api/permissions/{perm_id}", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "权限更新成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"更新失败: {result.get('message', '未知错误')}")
    
    def delete_permission(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的权限")
            return
        
        row = selected[0].row()
        perm_id = self.table.item(row, 0).text()
        perm_name = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除权限 '{perm_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.delete(f"/api/permissions/{perm_id}")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "权限删除成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"删除失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_data()
