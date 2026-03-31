from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QComboBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class UserEditDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑用户" if self.user_data.get("id") else "新增用户")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.username = QLineEdit()
        self.username.setText(self.user_data.get("username", ""))
        layout.addRow("用户名:", self.username)
        
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("密码:", self.password)
        
        self.nickname = QLineEdit()
        self.nickname.setText(self.user_data.get("nickname", ""))
        layout.addRow("昵称:", self.nickname)
        
        self.email = QLineEdit()
        self.email.setText(self.user_data.get("email", ""))
        layout.addRow("邮箱:", self.email)
        
        self.phone = QLineEdit()
        self.phone.setText(self.user_data.get("phone", ""))
        layout.addRow("电话:", self.phone)
        
        self.status = QComboBox()
        self.status.addItems(["启用", "禁用"])
        self.status.setCurrentIndex(0 if self.user_data.get("status", 1) == 1 else 1)
        layout.addRow("状态:", self.status)
        
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
            "username": self.username.text(),
            "password": self.password.text() or None,
            "nickname": self.nickname.text(),
            "email": self.email.text(),
            "phone": self.phone.text(),
            "status": 1 if self.status.currentIndex() == 0 else 0
        }
    
    def save(self):
        if not self.username.text():
            QMessageBox.warning(self, "错误", "用户名不能为空")
            return
        
        self.accept()


class UserListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        filter_group = QGroupBox("筛选条件")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("用户名:"))
        self.filter_username = QLineEdit()
        self.filter_username.setPlaceholderText("输入用户名搜索")
        filter_layout.addWidget(self.filter_username)
        
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
        
        add_btn = QPushButton("新增用户")
        add_btn.clicked.connect(self.add_user)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_user)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_user)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "用户名", "昵称", "邮箱", "电话", "状态", "创建时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
    
    def load_data(self):
        result = api_client.get("/api/users/", {
            "username": self.filter_username.text()
        })
        
        if result.get("code") == 200:
            users = result.get("data", {}).get("list", [])
            self.table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.table.setItem(row, 0, QTableWidgetItem(str(user.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(user.get("username", "")))
                self.table.setItem(row, 2, QTableWidgetItem(user.get("nickname", "")))
                self.table.setItem(row, 3, QTableWidgetItem(user.get("email", "")))
                self.table.setItem(row, 4, QTableWidgetItem(user.get("phone", "")))
                self.table.setItem(row, 5, QTableWidgetItem("启用" if user.get("status") == 1 else "禁用"))
                self.table.setItem(row, 6, QTableWidgetItem(user.get("create_time", "")))
        else:
            QMessageBox.warning(self, "错误", f"获取用户列表失败: {result.get('message', '未知错误')}")
    
    def reset_filter(self):
        self.filter_username.clear()
        self.load_data()
    
    def add_user(self):
        dialog = UserEditDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            result = api_client.post("/api/users/", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "用户创建成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"创建失败: {result.get('message', '未知错误')}")
    
    def edit_user(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的用户")
            return
        
        row = selected[0].row()
        user_id = self.table.item(row, 0).text()
        
        user_data = {
            "id": int(user_id),
            "username": self.table.item(row, 1).text(),
            "nickname": self.table.item(row, 2).text(),
            "email": self.table.item(row, 3).text(),
            "phone": self.table.item(row, 4).text(),
            "status": 1 if self.table.item(row, 5).text() == "启用" else 0
        }
        
        dialog = UserEditDialog(self, user_data)
        if dialog.exec():
            data = dialog.get_data()
            result = api_client.put(f"/api/users/{user_id}", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "用户更新成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"更新失败: {result.get('message', '未知错误')}")
    
    def delete_user(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的用户")
            return
        
        row = selected[0].row()
        user_id = self.table.item(row, 0).text()
        username = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除用户 '{username}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.delete(f"/api/users/{user_id}")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "用户删除成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"删除失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_data()
