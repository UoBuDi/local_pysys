from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QDateEdit, QDialog,
    QTabWidget, QSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class GroupEditDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data or {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑班组" if self.data.get("id") else "新增班组")
        self.setMinimumWidth(300)
        
        layout = QFormLayout(self)
        
        self.name = QLineEdit()
        self.name.setText(self.data.get("name", ""))
        layout.addRow("班组名称:", self.name)
        
        self.description = QLineEdit()
        self.description.setText(self.data.get("description", ""))
        layout.addRow("描述:", self.description)
        
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
            "name": self.name.text(),
            "description": self.description.text()
        }


class ShiftEditDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data or {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑班次" if self.data.get("id") else "新增班次")
        self.setMinimumWidth(300)
        
        layout = QFormLayout(self)
        
        self.name = QLineEdit()
        self.name.setText(self.data.get("name", ""))
        layout.addRow("班次名称:", self.name)
        
        self.start_time = QLineEdit()
        self.start_time.setText(self.data.get("start_time", "08:00"))
        self.start_time.setPlaceholderText("HH:MM")
        layout.addRow("开始时间:", self.start_time)
        
        self.end_time = QLineEdit()
        self.end_time.setText(self.data.get("end_time", "17:00"))
        self.end_time.setPlaceholderText("HH:MM")
        layout.addRow("结束时间:", self.end_time)
        
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
            "name": self.name.text(),
            "start_time": self.start_time.text(),
            "end_time": self.end_time.text()
        }


class StaffEditDialog(QDialog):
    def __init__(self, parent=None, data=None, groups=None):
        super().__init__(parent)
        self.data = data or {}
        self.groups = groups or []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑人员" if self.data.get("id") else "新增人员")
        self.setMinimumWidth(300)
        
        layout = QFormLayout(self)
        
        self.name = QLineEdit()
        self.name.setText(self.data.get("name", ""))
        layout.addRow("姓名:", self.name)
        
        self.group_id = QComboBox()
        for group in self.groups:
            self.group_id.addItem(group.get("name", ""), group.get("id"))
        if self.data.get("group_id"):
            idx = self.group_id.findData(self.data.get("group_id"))
            if idx >= 0:
                self.group_id.setCurrentIndex(idx)
        layout.addRow("所属班组:", self.group_id)
        
        self.phone = QLineEdit()
        self.phone.setText(self.data.get("phone", ""))
        layout.addRow("联系电话:", self.phone)
        
        self.status = QComboBox()
        self.status.addItems(["在职", "离职"])
        self.status.setCurrentIndex(0 if self.data.get("status", 1) == 1 else 1)
        layout.addRow("状态:", self.status)
        
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
            "name": self.name.text(),
            "group_id": self.group_id.currentData(),
            "phone": self.phone.text(),
            "status": 1 if self.status.currentIndex() == 0 else 0
        }


class SchedulingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        self.group_tab = self.create_group_tab()
        self.tabs.addTab(self.group_tab, "班组管理")
        
        self.shift_tab = self.create_shift_tab()
        self.tabs.addTab(self.shift_tab, "班次管理")
        
        self.staff_tab = self.create_staff_tab()
        self.tabs.addTab(self.staff_tab, "人员管理")
        
        self.record_tab = self.create_record_tab()
        self.tabs.addTab(self.record_tab, "排班记录")
        
        layout.addWidget(self.tabs)
        
        self.load_all_data()
    
    def create_group_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("新增班组")
        add_btn.clicked.connect(self.add_group)
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_group)
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_group)
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_groups)
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self.import_groups)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.group_table = QTableWidget()
        self.group_table.setColumnCount(3)
        self.group_table.setHorizontalHeaderLabels(["ID", "班组名称", "描述"])
        self.group_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.group_table)
        
        return widget
    
    def create_shift_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("新增班次")
        add_btn.clicked.connect(self.add_shift)
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_shift)
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_shift)
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_shifts)
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self.import_shifts)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.shift_table = QTableWidget()
        self.shift_table.setColumnCount(4)
        self.shift_table.setHorizontalHeaderLabels(["ID", "班次名称", "开始时间", "结束时间"])
        self.shift_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.shift_table)
        
        return widget
    
    def create_staff_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("新增人员")
        add_btn.clicked.connect(self.add_staff)
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_staff)
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_staff)
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_staff)
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self.import_staff)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(5)
        self.staff_table.setHorizontalHeaderLabels(["ID", "姓名", "所属班组", "联系电话", "状态"])
        self.staff_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.staff_table)
        
        return widget
    
    def create_record_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("班组:"))
        self.record_group = QComboBox()
        self.record_group.currentIndexChanged.connect(self.load_records)
        filter_layout.addWidget(self.record_group)
        filter_layout.addWidget(QLabel("日期:"))
        self.record_date = QDateEdit()
        self.record_date.setDate(QDate.currentDate())
        self.record_date.dateChanged.connect(self.load_records)
        filter_layout.addWidget(self.record_date)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加排班")
        add_btn.clicked.connect(self.add_record)
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_records)
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self.import_records)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.record_table = QTableWidget()
        self.record_table.setColumnCount(5)
        self.record_table.setHorizontalHeaderLabels(["ID", "日期", "人员", "班次", "备注"])
        self.record_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.record_table)
        
        return widget
    
    def load_all_data(self):
        self.load_groups()
        self.load_shifts()
        self.load_staff()
        self.load_records()
    
    def load_groups(self):
        result = api_client.get("/api/scheduling/groups/")
        if result.get("code") == 200:
            groups = result.get("data", [])
            self.group_table.setRowCount(len(groups))
            for row, group in enumerate(groups):
                self.group_table.setItem(row, 0, QTableWidgetItem(str(group.get("id", ""))))
                self.group_table.setItem(row, 1, QTableWidgetItem(group.get("name", "")))
                self.group_table.setItem(row, 2, QTableWidgetItem(group.get("description", "")))
    
    def load_shifts(self):
        result = api_client.get("/api/scheduling/shifts/")
        if result.get("code") == 200:
            shifts = result.get("data", [])
            self.shift_table.setRowCount(len(shifts))
            for row, shift in enumerate(shifts):
                self.shift_table.setItem(row, 0, QTableWidgetItem(str(shift.get("id", ""))))
                self.shift_table.setItem(row, 1, QTableWidgetItem(shift.get("name", "")))
                self.shift_table.setItem(row, 2, QTableWidgetItem(shift.get("start_time", "")))
                self.shift_table.setItem(row, 3, QTableWidgetItem(shift.get("end_time", "")))
    
    def load_staff(self):
        result = api_client.get("/api/scheduling/staff/")
        if result.get("code") == 200:
            staff_list = result.get("data", [])
            self.staff_table.setRowCount(len(staff_list))
            for row, staff in enumerate(staff_list):
                self.staff_table.setItem(row, 0, QTableWidgetItem(str(staff.get("id", ""))))
                self.staff_table.setItem(row, 1, QTableWidgetItem(staff.get("name", "")))
                self.staff_table.setItem(row, 2, QTableWidgetItem(staff.get("group_name", "")))
                self.staff_table.setItem(row, 3, QTableWidgetItem(staff.get("phone", "")))
                self.staff_table.setItem(row, 4, QTableWidgetItem("在职" if staff.get("status") == 1 else "离职"))
    
    def load_records(self):
        result = api_client.get("/api/scheduling/records/", {
            "group_id": self.record_group.currentData(),
            "date": self.record_date.date().toString("yyyy-MM-dd")
        })
        if result.get("code") == 200:
            records = result.get("data", [])
            self.record_table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.record_table.setItem(row, 0, QTableWidgetItem(str(record.get("id", ""))))
                self.record_table.setItem(row, 1, QTableWidgetItem(record.get("schedule_date", "")))
                self.record_table.setItem(row, 2, QTableWidgetItem(record.get("staff_name", "")))
                self.record_table.setItem(row, 3, QTableWidgetItem(record.get("shift_name", "")))
                self.record_table.setItem(row, 4, QTableWidgetItem(record.get("remark", "")))
    
    def add_group(self):
        dialog = GroupEditDialog(self)
        if dialog.exec():
            result = api_client.post("/api/scheduling/groups/", dialog.get_data())
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "班组创建成功")
                self.load_groups()
    
    def edit_group(self):
        selected = self.group_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的班组")
            return
        row = selected[0].row()
        data = {"id": int(self.group_table.item(row, 0).text()), "name": self.group_table.item(row, 1).text(), "description": self.group_table.item(row, 2).text()}
        dialog = GroupEditDialog(self, data)
        if dialog.exec():
            result = api_client.put(f"/api/scheduling/groups/{data['id']}", dialog.get_data())
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "班组更新成功")
                self.load_groups()
    
    def delete_group(self):
        selected = self.group_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的班组")
            return
        row = selected[0].row()
        group_id = self.group_table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", "确定要删除该班组吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.delete(f"/api/scheduling/groups/{group_id}")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "班组删除成功")
                self.load_groups()
    
    def export_groups(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "groups.xlsx", "Excel文件 (*.xlsx)")
        if file_path:
            if api_client.download("/api/scheduling/groups/export/", file_path):
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
    
    def import_groups(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Excel文件 (*.xlsx *.xls)")
        if file_path:
            result = api_client.upload("/api/scheduling/groups/import/", file_path)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "导入成功")
                self.load_groups()
    
    def add_shift(self):
        dialog = ShiftEditDialog(self)
        if dialog.exec():
            result = api_client.post("/api/scheduling/shifts/", dialog.get_data())
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "班次创建成功")
                self.load_shifts()
    
    def edit_shift(self):
        selected = self.shift_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的班次")
            return
        row = selected[0].row()
        data = {"id": int(self.shift_table.item(row, 0).text()), "name": self.shift_table.item(row, 1).text(), "start_time": self.shift_table.item(row, 2).text(), "end_time": self.shift_table.item(row, 3).text()}
        dialog = ShiftEditDialog(self, data)
        if dialog.exec():
            result = api_client.put(f"/api/scheduling/shifts/{data['id']}", dialog.get_data())
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "班次更新成功")
                self.load_shifts()
    
    def delete_shift(self):
        selected = self.shift_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的班次")
            return
        row = selected[0].row()
        shift_id = self.shift_table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", "确定要删除该班次吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.delete(f"/api/scheduling/shifts/{shift_id}")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "班次删除成功")
                self.load_shifts()
    
    def export_shifts(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "shifts.xlsx", "Excel文件 (*.xlsx)")
        if file_path:
            if api_client.download("/api/scheduling/shifts/export/", file_path):
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
    
    def import_shifts(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Excel文件 (*.xlsx *.xls)")
        if file_path:
            result = api_client.upload("/api/scheduling/shifts/import/", file_path)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "导入成功")
                self.load_shifts()
    
    def add_staff(self):
        result = api_client.get("/api/scheduling/groups/")
        groups = result.get("data", []) if result.get("code") == 200 else []
        dialog = StaffEditDialog(self, groups=groups)
        if dialog.exec():
            result = api_client.post("/api/scheduling/staff/", dialog.get_data())
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "人员创建成功")
                self.load_staff()
    
    def edit_staff(self):
        selected = self.staff_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的人员")
            return
        row = selected[0].row()
        result = api_client.get("/api/scheduling/groups/")
        groups = result.get("data", []) if result.get("code") == 200 else []
        data = {"id": int(self.staff_table.item(row, 0).text()), "name": self.staff_table.item(row, 1).text(), "phone": self.staff_table.item(row, 3).text(), "status": 1 if self.staff_table.item(row, 4).text() == "在职" else 0}
        dialog = StaffEditDialog(self, data, groups)
        if dialog.exec():
            result = api_client.put(f"/api/scheduling/staff/{data['id']}", dialog.get_data())
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "人员更新成功")
                self.load_staff()
    
    def delete_staff(self):
        selected = self.staff_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的人员")
            return
        row = selected[0].row()
        staff_id = self.staff_table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", "确定要删除该人员吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.delete(f"/api/scheduling/staff/{staff_id}")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "人员删除成功")
                self.load_staff()
    
    def export_staff(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "staff.xlsx", "Excel文件 (*.xlsx)")
        if file_path:
            if api_client.download("/api/scheduling/staff/export/", file_path):
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
    
    def import_staff(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Excel文件 (*.xlsx *.xls)")
        if file_path:
            result = api_client.upload("/api/scheduling/staff/import/", file_path)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "导入成功")
                self.load_staff()
    
    def add_record(self):
        QMessageBox.information(self, "提示", "请使用Web界面的排班日历进行排班操作")
    
    def export_records(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "scheduling.xlsx", "Excel文件 (*.xlsx)")
        if file_path:
            if api_client.download("/api/scheduling/export/", file_path):
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
    
    def import_records(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Excel文件 (*.xlsx *.xls)")
        if file_path:
            result = api_client.upload("/api/scheduling/import/", file_path)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "导入成功")
                self.load_records()
    
    def refresh(self):
        self.load_all_data()
