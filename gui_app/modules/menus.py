from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QComboBox, QHeaderView, QAbstractItemView,
    QTextEdit, QSpinBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class MenuEditDialog(QDialog):
    def __init__(self, parent=None, menu_data=None, parent_options=None):
        super().__init__(parent)
        self.menu_data = menu_data or {}
        self.parent_options = parent_options or []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑菜单" if self.menu_data.get("id") else "新增菜单")
        self.setMinimumWidth(500)
        
        layout = QFormLayout(self)
        
        self.parent_id = QComboBox()
        self.parent_id.addItem("无（顶级菜单）", 0)
        for opt in self.parent_options:
            self.parent_id.addItem(opt.get("name", ""), opt.get("id"))
        if self.menu_data.get("parent_id"):
            idx = self.parent_id.findData(self.menu_data.get("parent_id"))
            if idx >= 0:
                self.parent_id.setCurrentIndex(idx)
        layout.addRow("父级菜单:", self.parent_id)
        
        self.name = QLineEdit()
        self.name.setText(self.menu_data.get("name", ""))
        layout.addRow("菜单名称:", self.name)
        
        self.path = QLineEdit()
        self.path.setText(self.menu_data.get("path", ""))
        layout.addRow("路由路径:", self.path)
        
        self.component = QLineEdit()
        self.component.setText(self.menu_data.get("component", ""))
        layout.addRow("组件路径:", self.component)
        
        self.icon = QLineEdit()
        self.icon.setText(self.menu_data.get("icon", ""))
        layout.addRow("图标:", self.icon)
        
        self.sort_order = QSpinBox()
        self.sort_order.setRange(0, 9999)
        self.sort_order.setValue(self.menu_data.get("sort_order", 0))
        layout.addRow("排序:", self.sort_order)
        
        self.status = QComboBox()
        self.status.addItems(["启用", "禁用"])
        self.status.setCurrentIndex(0 if self.menu_data.get("status", 1) == 1 else 1)
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
            "parent_id": self.parent_id.currentData(),
            "name": self.name.text(),
            "path": self.path.text(),
            "component": self.component.text(),
            "icon": self.icon.text(),
            "sort_order": self.sort_order.value(),
            "status": 1 if self.status.currentIndex() == 0 else 0
        }
    
    def save(self):
        if not self.name.text():
            QMessageBox.warning(self, "错误", "菜单名称不能为空")
            return
        self.accept()


class MenuListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("新增菜单")
        add_btn.clicked.connect(self.add_menu)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_menu)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_menu)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "菜单名称", "路径", "图标", "排序", "状态"])
        self.tree.setColumnWidth(0, 50)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 200)
        layout.addWidget(self.tree)
    
    def load_data(self):
        result = api_client.get("/api/menus/")
        
        if result.get("code") == 200:
            menus = result.get("data", [])
            self.tree.clear()
            
            menu_map = {}
            for menu in menus:
                item = QTreeWidgetItem([
                    str(menu.get("id", "")),
                    menu.get("name", ""),
                    menu.get("path", ""),
                    menu.get("icon", ""),
                    str(menu.get("sort_order", 0)),
                    "启用" if menu.get("status") == 1 else "禁用"
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, menu)
                menu_map[menu.get("id")] = item
            
            for menu in menus:
                item = menu_map.get(menu.get("id"))
                parent_id = menu.get("parent_id")
                if parent_id and parent_id in menu_map:
                    parent_item = menu_map.get(parent_id)
                    parent_item.addChild(item)
                else:
                    self.tree.addTopLevelItem(item)
            
            self.tree.expandAll()
        else:
            QMessageBox.warning(self, "错误", f"获取菜单列表失败: {result.get('message', '未知错误')}")
    
    def get_parent_options(self):
        result = api_client.get("/api/menus/")
        if result.get("code") == 200:
            return result.get("data", [])
        return []
    
    def add_menu(self):
        parent_options = self.get_parent_options()
        dialog = MenuEditDialog(self, parent_options=parent_options)
        if dialog.exec():
            data = dialog.get_data()
            result = api_client.post("/api/menus/", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "菜单创建成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"创建失败: {result.get('message', '未知错误')}")
    
    def edit_menu(self):
        selected = self.tree.currentItem()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的菜单")
            return
        
        menu_data = selected.data(0, Qt.ItemDataRole.UserRole)
        parent_options = self.get_parent_options()
        
        dialog = MenuEditDialog(self, menu_data=menu_data, parent_options=parent_options)
        if dialog.exec():
            data = dialog.get_data()
            menu_id = menu_data.get("id")
            result = api_client.put(f"/api/menus/{menu_id}", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "菜单更新成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"更新失败: {result.get('message', '未知错误')}")
    
    def delete_menu(self):
        selected = self.tree.currentItem()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的菜单")
            return
        
        menu_data = selected.data(0, Qt.ItemDataRole.UserRole)
        menu_name = menu_data.get("name", "")
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除菜单 '{menu_name}' 吗？\n注意：子菜单也会被删除！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            menu_id = menu_data.get("id")
            result = api_client.delete(f"/api/menus/{menu_id}")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "菜单删除成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"删除失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_data()
