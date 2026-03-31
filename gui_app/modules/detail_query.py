from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHeaderView, QDateEdit, QTimeEdit
)
from PyQt6.QtCore import Qt, QDate, QTime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vue-element-plus-admin-master" / "backend"))

from utils.api_client import api_client


class DetailQueryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        filter_group = QGroupBox("查询条件")
        filter_layout = QFormLayout()
        
        row1 = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        row1.addWidget(QLabel("开始日期:"))
        row1.addWidget(self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        row1.addWidget(QLabel("结束日期:"))
        row1.addWidget(self.end_date)
        row1.addStretch()
        filter_layout.addRow(row1)
        
        row2 = QHBoxLayout()
        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText("输入车牌号")
        row2.addWidget(QLabel("车牌号:"))
        row2.addWidget(self.plate_input)
        
        self.station_input = QLineEdit()
        self.station_input.setPlaceholderText("输入收费站名称或编码")
        row2.addWidget(QLabel("收费站:"))
        row2.addWidget(self.station_input)
        row2.addStretch()
        filter_layout.addRow(row2)
        
        row3 = QHBoxLayout()
        self.lane_input = QLineEdit()
        self.lane_input.setPlaceholderText("输入车道号")
        row3.addWidget(QLabel("车道号:"))
        row3.addWidget(self.lane_input)
        
        self.media_type = QComboBox()
        self.media_type.addItem("全部", "")
        self.media_type.addItem("CPC卡", "CPC")
        self.media_type.addItem("ETC", "ETC")
        self.media_type.addItem("无卡", "NONE")
        row3.addWidget(QLabel("介质类型:"))
        row3.addWidget(self.media_type)
        row3.addStretch()
        filter_layout.addRow(row3)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        btn_layout = QHBoxLayout()
        
        search_btn = QPushButton("查询")
        search_btn.clicked.connect(self.search)
        btn_layout.addWidget(search_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "序号", "车牌号", "车型", "入口站", "出口站",
            "入口时间", "出口时间", "金额", "车道号", "介质类型",
            "交易类型", "状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def search(self):
        params = {
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date.date().toString("yyyy-MM-dd"),
            "plate": self.plate_input.text(),
            "station": self.station_input.text(),
            "lane": self.lane_input.text(),
            "media_type": self.media_type.currentData()
        }
        
        result = api_client.post("/api/detail-query/", params)
        
        if result.get("code") == 200:
            data = result.get("data", {}).get("list", [])
            self.table.setRowCount(len(data))
            
            for row, item in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.table.setItem(row, 1, QTableWidgetItem(item.get("plate", "")))
                self.table.setItem(row, 2, QTableWidgetItem(item.get("vehicle_type", "")))
                self.table.setItem(row, 3, QTableWidgetItem(item.get("entry_station", "")))
                self.table.setItem(row, 4, QTableWidgetItem(item.get("exit_station", "")))
                self.table.setItem(row, 5, QTableWidgetItem(item.get("entry_time", "")))
                self.table.setItem(row, 6, QTableWidgetItem(item.get("exit_time", "")))
                self.table.setItem(row, 7, QTableWidgetItem(str(item.get("amount", ""))))
                self.table.setItem(row, 8, QTableWidgetItem(item.get("lane", "")))
                self.table.setItem(row, 9, QTableWidgetItem(item.get("media_type", "")))
                self.table.setItem(row, 10, QTableWidgetItem(item.get("trans_type", "")))
                self.table.setItem(row, 11, QTableWidgetItem(item.get("status", "")))
        else:
            QMessageBox.warning(self, "错误", f"查询失败: {result.get('message', '未知错误')}")
    
    def reset(self):
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.end_date.setDate(QDate.currentDate())
        self.plate_input.clear()
        self.station_input.clear()
        self.lane_input.clear()
        self.media_type.setCurrentIndex(0)
        self.table.setRowCount(0)
    
    def refresh(self):
        pass
