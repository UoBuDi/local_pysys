import asyncio
from typing import List, Dict

# 同步状态
sync_status = {
    "is_running": False,
    "progress": 0.0,
    "message": "",
    "current_month": None
}

def generate_month_options() -> List[str]:
    # 生成月份选项
    months = []
    for year in [2025, 2026]:
        for month in range(1, 13):
            months.append(f"{year}-{month:02d}")
    return months

async def run_sync(months: List[str], config):
    global sync_status
    sync_status["is_running"] = True
    sync_status["progress"] = 0.0
    sync_status["message"] = "开始同步"
    
    try:
        total = len(months)
        for i, month in enumerate(months):
            sync_status["current_month"] = month
            sync_status["message"] = f"正在同步 {month}"
            sync_status["progress"] = (i + 1) / total * 100
            await asyncio.sleep(1)
        
        sync_status["message"] = "同步完成"
    finally:
        sync_status["is_running"] = False

def stop_sync():
    global sync_status
    sync_status["is_running"] = False
    sync_status["message"] = "同步已停止"