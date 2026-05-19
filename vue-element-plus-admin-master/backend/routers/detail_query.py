"""
详单查询路由
包含通行记录的查询接口，支持多种条件筛选和分页
"""

import logging
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.dependencies import get_current_user
from core.models import DetailQueryRequest
from core.config import get_config as get_app_config
from core.utils import format_time_value

logger = logging.getLogger(__name__)

router = APIRouter()

QUERY_TIMEOUT = 90


def _get_detail_query_table_name(config) -> str:
    """从配置文件获取详单查询的固定表名"""
    table_name = config.get('DETAIL_QUERY', 'table_name', fallback='')

    if not table_name:
        logger.error("[DETAIL_QUERY] 配置节缺少 table_name 设置")
        return ''

    return table_name.strip()


def _execute_detail_query(request: DetailQueryRequest, config):
    """执行详单查询的核心逻辑（在线程池中运行）"""
    from database import get_db_connection

    table_name = _get_detail_query_table_name(config)
    if not table_name:
        return {"code": 404, "message": "未配置详单查询数据表，请检查 config.ini 的 [DETAIL_QUERY] 配置节"}

    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            if not cursor.fetchone():
                return {"code": 404, "message": f"数据表 {table_name} 不存在"}

            cursor.execute(f"DESCRIBE `{table_name}`")
            actual_columns = {row[0] for row in cursor.fetchall()}

            column_map = {
                'pass_id': '通行标识ID',
                'entry_name': '收费入口名称',
                'exit_name': '收费出口名称',
                'plate_number': '实际车辆车牌号码+颜色',
                'vehicle_type': '收费车型',
                'billing_method': '计费方式',
                'medium': '通行介质',
                'settlement_date': '清分日',
                'data_type': '拆分类型/数据类型',
                'time': '计费交易起点时间',
            }

            conditions = []
            params = []

            if request.pass_id and column_map['pass_id'] in actual_columns:
                conditions.append(f"`{column_map['pass_id']}` LIKE %s")
                params.append(f"{request.pass_id}%")
            if request.entry_name and column_map['entry_name'] in actual_columns:
                conditions.append(f"`{column_map['entry_name']}` LIKE %s")
                params.append(f"{request.entry_name}%")
            if request.exit_name and column_map['exit_name'] in actual_columns:
                conditions.append(f"`{column_map['exit_name']}` LIKE %s")
                params.append(f"{request.exit_name}%")
            if request.plate_number and column_map['plate_number'] in actual_columns:
                conditions.append(f"`{column_map['plate_number']}` LIKE %s")
                params.append(f"{request.plate_number}%")
            if request.vehicle_type and column_map['vehicle_type'] in actual_columns:
                conditions.append(f"`{column_map['vehicle_type']}` = %s")
                params.append(request.vehicle_type)
            if request.billing_method and column_map['billing_method'] in actual_columns:
                conditions.append(f"`{column_map['billing_method']}` = %s")
                params.append(request.billing_method)
            if request.medium and column_map['medium'] in actual_columns:
                conditions.append(f"`{column_map['medium']}` = %s")
                params.append(request.medium)
            if request.settlement_date and column_map['settlement_date'] in actual_columns:
                conditions.append(f"`{column_map['settlement_date']}` = %s")
                params.append(request.settlement_date)
            if request.data_type and column_map['data_type'] in actual_columns:
                conditions.append(f"`{column_map['data_type']}` = %s")
                params.append(request.data_type)
            if request.start_time and request.end_time and column_map['time'] in actual_columns:
                conditions.append(f"`{column_map['time']}` BETWEEN %s AND %s")
                params.extend([request.start_time, request.end_time])
            elif request.start_time and column_map['time'] in actual_columns:
                conditions.append(f"`{column_map['time']}` >= %s")
                params.append(request.start_time)
            elif request.end_time and column_map['time'] in actual_columns:
                conditions.append(f"`{column_map['time']}` <= %s")
                params.append(request.end_time)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            count_sql = f"SELECT COUNT(*) FROM `{table_name}` WHERE {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]

            order_col = column_map['time'] if column_map['time'] in actual_columns else 'id'
            offset = (request.page - 1) * request.page_size
            data_sql = f"""
                SELECT * FROM `{table_name}` 
                WHERE {where_clause} 
                ORDER BY `{order_col}` DESC 
                LIMIT {offset}, {request.page_size}
            """
            cursor.execute(data_sql, params)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            time_columns = {'入口时间', '出口时间', '交易时间', '门架通行时间'}
            data_list = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if col in time_columns:
                        value = format_time_value(value)
                    row_dict[col] = value
                data_list.append(row_dict)

            return {
                "code": 200,
                "message": "success",
                "data": {
                    "list": data_list,
                    "total": total,
                    "page": request.page,
                    "pageSize": request.page_size,
                    "tableName": table_name
                }
            }


@router.post("/api/detail-query/")
async def detail_query(request: DetailQueryRequest, user: dict = Depends(get_current_user)):
    """详单查询接口（带90秒超时控制）"""
    start_time = time.time()
    
    try:
        config = get_app_config()
        
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, _execute_detail_query, request, config),
                timeout=QUERY_TIMEOUT
            )
            
            elapsed = time.time() - start_time
            logger.info(f"详单查询完成，耗时: {elapsed:.2f}秒")
            
            return result
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.warning(f"详单查询超时（{QUERY_TIMEOUT}秒），已耗时: {elapsed:.2f}秒")
            return {
                "code": 504,
                "message": f"查询超时（限制{QUERY_TIMEOUT}秒），请缩小查询范围后重试"
            }
        finally:
            executor.shutdown(wait=False)
            
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"详单查询失败，耗时: {elapsed:.2f}秒，错误: {e}", exc_info=True)
        return {"code": 500, "message": f"详单查询失败: {str(e)}"}
