from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QDateEdit, QTimeEdit,
    QDialog, QTextEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QDate, QTime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class SpecialRecordEditDialog(QDialog):
    def __init__(self, parent=None, record_data=None):
        super().__init__(parent)
        self.record_data = record_data or {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("编辑记录" if self.record_data.get("id") else "新增记录")
        self.setMinimumWidth(500)
        
        layout = QFormLayout(self)
        
        self.record_type = QComboBox()
        self.record_type.addItems(["U型车", "未付车", "无卡车"])
        if self.record_data.get("record_type"):
            idx = self.record_type.findText(self.record_data.get("record_type"))
            if idx >= 0:
                self.record_type.setCurrentIndex(idx)
        layout.addRow("记录类型:", self.record_type)
        
        self.record_date = QDateEdit()
        self.record_date.setCalendarPopup(True)
        if self.record_data.get("record_date"):
            self.record_date.setDate(QDate.fromString(self.record_data.get("record_date"), "yyyy-MM-dd"))
        else:
            self.record_date.setDate(QDate.currentDate())
        layout.addRow("日期:", self.record_date)
        
        self.exit_station = QLineEdit()
        self.exit_station.setText(self.record_data.get("exit_station", ""))
        layout.addRow("收费出口:", self.exit_station)
        
        self.entry_station = QLineEdit()
        self.entry_station.setText(self.record_data.get("entry_station", ""))
        layout.addRow("收费入口:", self.entry_station)
        
        self.lane = QLineEdit()
        self.lane.setText(self.record_data.get("lane", ""))
        layout.addRow("车道号:", self.lane)
        
        self.plate = QLineEdit()
        self.plate.setText(self.record_data.get("plate", ""))
        layout.addRow("车牌:", self.plate)
        
        self.reason = QTextEdit()
        self.reason.setMaximumHeight(60)
        self.reason.setText(self.record_data.get("reason", ""))
        layout.addRow("原因:", self.reason)
        
        self.remark = QTextEdit()
        self.remark.setMaximumHeight(60)
        self.remark.setText(self.record_data.get("remark", ""))
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
            "record_type": self.record_type.currentText(),
            "record_date": self.record_date.date().toString("yyyy-MM-dd"),
            "exit_station": self.exit_station.text(),
            "entry_station": self.entry_station.text(),
            "lane": self.lane.text(),
            "plate": self.plate.text(),
            "reason": self.reason.toPlainText(),
            "remark": self.remark.toPlainText()
        }
    
    def save(self):
        if not self.plate.text():
            QMessageBox.warning(self, "错误", "车牌号不能为空")
            return
        self.accept()


class SpecialRecordsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        filter_group = QGroupBox("筛选条件")
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("记录类型:"))
        self.filter_type = QComboBox()
        self.filter_type.addItem("全部", "")
        self.filter_type.addItems(["U型车", "未付车", "无卡车"])
        filter_layout.addWidget(self.filter_type)
        
        filter_layout.addWidget(QLabel("车牌号:"))
        self.filter_plate = QLineEdit()
        filter_layout.addWidget(self.filter_plate)
        
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
        
        add_btn = QPushButton("新增记录")
        add_btn.clicked.connect(self.add_record)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self.edit_record)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self.delete_record)
        btn_layout.addWidget(delete_btn)
        
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_data)
        btn_layout.addWidget(export_btn)
        
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self.import_data)
        btn_layout.addWidget(import_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "类型", "日期", "收费出口", "收费入口",
            "车道号", "车牌", "原因", "备注"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_data(self):
        result = api_client.get("/api/special-records/", {
            "record_type": self.filter_type.currentData(),
            "plate": self.filter_plate.text()
        })
        
        if result.get("code") == 200:
            records = result.get("data", [])
            self.table.setRowCount(len(records))
            
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(str(record.get("id", ""))))
                self.table.setItem(row, 1, QTableWidgetItem(record.get("record_type", "")))
                self.table.setItem(row, 2, QTableWidgetItem(record.get("record_date", "")))
                self.table.setItem(row, 3, QTableWidgetItem(record.get("exit_station", "")))
                self.table.setItem(row, 4, QTableWidgetItem(record.get("entry_station", "")))
                self.table.setItem(row, 5, QTableWidgetItem(record.get("lane", "")))
                self.table.setItem(row, 6, QTableWidgetItem(record.get("plate", "")))
                self.table.setItem(row, 7, QTableWidgetItem(record.get("reason", "")))
                self.table.setItem(row, 8, QTableWidgetItem(record.get("remark", "")))
        else:
            QMessageBox.warning(self, "错误", f"获取记录失败: {result.get('message', '未知错误')}")
    
    def reset_filter(self):
        self.filter_type.setCurrentIndex(0)
        self.filter_plate.clear()
        self.load_data()
    
    def add_record(self):
        dialog = SpecialRecordEditDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            result = api_client.post("/api/special-records/", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "记录创建成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"创建失败: {result.get('message', '未知错误')}")
    
    def edit_record(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要编辑的记录")
            return
        
        row = selected[0].row()
        record_data = {
            "id": int(self.table.item(row, 0).text()),
            "record_type": self.table.item(row, 1).text(),
            "record_date": self.table.item(row, 2).text(),
            "exit_station": self.table.item(row, 3).text(),
            "entry_station": self.table.item(row, 4).text(),
            "lane": self.table.item(row, 5).text(),
            "plate": self.table.item(row, 6).text(),
            "reason": self.table.item(row, 7).text(),
            "remark": self.table.item(row, 8).text()
        }
        
        dialog = SpecialRecordEditDialog(self, record_data)
        if dialog.exec():
            data = dialog.get_data()
            record_id = record_data["id"]
            result = api_client.put(f"/api/special-records/{record_id}", data)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "记录更新成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"更新失败: {result.get('message', '未知错误')}")
    
    def delete_record(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的记录")
            return
        
        row = selected[0].row()
        record_id = self.table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除该记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = api_client.delete(f"/api/special-records/{record_id}")
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "记录删除成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"删除失败: {result.get('message', '未知错误')}")
    
    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "special_records.xlsx", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            result = api_client.download("/api/special-records/export/", file_path)
            if result:
                QMessageBox.information(self, "成功", f"数据已导出到: {file_path}")
            else:
                QMessageBox.warning(self, "错误", "导出失败")
    
    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_path:
            result = api_client.upload("/api/special-records/import/", file_path)
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", f"导入成功: {result.get('message', '')}")
                self.load_data()
            else:
                QMessageBox.warning(self, "错误", f"导入失败: {result.get('message', '未知错误')}")
    
    def refresh(self):
        self.load_data()
