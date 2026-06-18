"""
路径匹配路由
提供收费路径匹配与金额计算功能，支持多条件搜索、省份编码查询、详情查看
"""

import logging
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends
from pymysql.cursors import DictCursor

from core.dependencies import get_current_user
from core.models import PathMatchRequest, PathDetailRequest
from core.config import get_config as get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()

QUERY_TIMEOUT = 120

# 省份编码前14位映射表（全国高速公路联网收费省级行政区划编码）
PROVINCE_CODE_MAP = {
    "11000000000000": "北京", "12000000000000": "天津", "13000000000000": "河北",
    "14000000000000": "山西", "15000000000000": "内蒙古", "21000000000000": "辽宁",
    "22000000000000": "吉林", "23000000000000": "黑龙江", "31000000000000": "上海",
    "32000000000000": "江苏", "33000000000000": "浙江", "34000000000000": "安徽",
    "35000000000000": "福建", "36000000000000": "江西", "37000000000000": "山东",
    "41000000000000": "河南", "42000000000000": "湖北", "43000000000000": "湖南",
    "44000000000000": "广东", "45000000000000": "广西", "46000000000000": "海南",
    "50000000000000": "重庆", "51000000000000": "四川", "52000000000000": "贵州",
    "53000000000000": "云南", "54000000000000": "西藏", "61000000000000": "陕西",
    "62000000000000": "甘肃", "63000000000000": "青海", "64000000000000": "宁夏",
    "65000000000000": "新疆",
}


def _get_path_match_table_name(config) -> str:
    """从配置文件获取路径匹配的固定表名"""
    table_name = config.get('PATH_MATCH', 'table_name', fallback='')
    if not table_name:
        logger.error("[PATH_MATCH] 配置节缺少 table_name 设置")
        return ''
    return table_name.strip()


def _build_search_conditions(request: PathMatchRequest, actual_columns: set):
    """根据请求参数构建 SQL WHERE 条件和参数列表

    Args:
        request: 前端搜索请求
        actual_columns: 数据表实际存在的列名集合

    Returns:
        tuple: (conditions列表, params列表)
    """
    conditions = []
    params = []

    # 清分日范围过滤（优先使用 transactionTimeRange）
    if request.transactionTimeRange and len(request.transactionTimeRange) == 2:
        if '清分日' in actual_columns:
            conditions.append("`清分日` >= %s")
            params.append(request.transactionTimeRange[0])
            conditions.append("`清分日` <= %s")
            params.append(request.transactionTimeRange[1] + ' 23:59:59')
    elif request.timeRange and len(request.timeRange) == 2:
        # 回退：按门架经过时间范围过滤
        if '计费交易起点时间' in actual_columns:
            conditions.append("`计费交易起点时间` >= %s")
            params.append(request.timeRange[0])
        if '计费交易终点时间' in actual_columns:
            conditions.append("`计费交易终点时间` <= %s")
            params.append(request.timeRange[1])

    # 排除绿通（拆分类型/数据类型 = 36）
    if request.excludeGreenChannel and '拆分类型/数据类型' in actual_columns:
        conditions.append("`拆分类型/数据类型` != 36")

    # 收费车型过滤
    if request.vehicleTypes and '收费车型' in actual_columns:
        types_list = [t.strip() for t in request.vehicleTypes.split(',') if t.strip()]
        if types_list:
            placeholders = ', '.join(['%s'] * len(types_list))
            conditions.append(f"`收费车型` IN ({placeholders})")
            params.extend(types_list)

    # 包含的拆分收费单元名称（起点）
    if request.includeUnits and '拆分收费单元名称组合' in actual_columns:
        include = request.includeUnits.strip()
        if request.endUnit and request.endUnit.strip():
            # 起点和终点同时存在：匹配包含起点和终点的路径
            end = request.endUnit.strip()
            conditions.append("`拆分收费单元名称组合` LIKE %s")
            params.append(f'%{include}%{end}%')
        else:
            conditions.append("`拆分收费单元名称组合` LIKE %s")
            params.append(f'%{include}%')

    # 终点位置包含的拆分收费单元名称（仅终点，无起点时）
    if request.endUnit and request.endUnit.strip() and not request.includeUnits:
        if '拆分收费单元名称组合' in actual_columns:
            end = request.endUnit.strip()
            conditions.append("`拆分收费单元名称组合` LIKE %s")
            params.append(f'%{end}%')

    # 排除的拆分收费单元名称
    if request.excludeUnits and '拆分收费单元名称组合' in actual_columns:
        exclude_list = [u.strip() for u in request.excludeUnits.split(',') if u.strip()]
        for unit in exclude_list:
            conditions.append("`拆分收费单元名称组合` NOT LIKE %s")
            params.append(f'%{unit}%')

    # 排除的收费出口名称
    if request.excludeExits and '收费出口名称' in actual_columns:
        exit_list = [e.strip() for e in request.excludeExits.split(',') if e.strip()]
        for exit_name in exit_list:
            conditions.append("`收费出口名称` NOT LIKE %s")
            params.append(f'{exit_name}%')

    return conditions, params


def _execute_search(request: PathMatchRequest, config):
    """执行路径匹配搜索的核心逻辑（在线程池中运行）"""
    from database import get_db_connection

    table_name = _get_path_match_table_name(config)
    if not table_name:
        return {"code": 404, "message": "未配置路径匹配数据表，请检查 config.ini 的 [PATH_MATCH] 配置节"}

    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor() as cursor:
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            if not cursor.fetchone():
                return {"code": 404, "message": f"数据表 {table_name} 不存在"}

            # 获取表的实际列名
            cursor.execute(f"DESCRIBE `{table_name}`")
            actual_columns = {row[0] for row in cursor.fetchall()}

            # 构建查询条件
            conditions, params = _build_search_conditions(request, actual_columns)
            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # 查询总记录数
            count_start = time.time()
            count_sql = f"SELECT COUNT(*) FROM `{table_name}` WHERE {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]
            count_duration = time.time() - count_start

            if total == 0:
                return {
                    "code": 200,
                    "message": "success",
                    "data": [],
                    "count": 0,
                    "debug": {
                        "total_time": 0,
                        "count_duration": round(count_duration, 3),
                        "select_sql": count_sql
                    }
                }

            # 查询数据
            select_start = time.time()
            select_fields = [
                '`通行标识ID`', '`收费入口编码`', '`收费出口编码`',
                '`收费入口名称`', '`收费出口名称`',
                '`计费交易起点时间`', '`计费交易终点时间`',
                '`实际车辆车牌号码+颜色`', '`收费车型`', '`清分日`',
                '`拆分路段拆分金额`', '`拆分收费单元名称组合`'
            ]
            # 仅选择表中实际存在的列
            available_fields = [f for f in select_fields if f.strip('`') in actual_columns]
            if not available_fields:
                available_fields = ['*']

            fields_str = ', '.join(available_fields)
            data_sql = f"SELECT {fields_str} FROM `{table_name}` WHERE {where_clause} ORDER BY `清分日` DESC, `计费交易起点时间` DESC"
            cursor.execute(data_sql, params)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            select_duration = time.time() - select_start

            # 转换为字典列表
            data_list = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                data_list.append(row_dict)

            total_time = time.time() - count_start

            return {
                "code": 200,
                "message": "success",
                "data": data_list,
                "count": total,
                "debug": {
                    "total_time": round(total_time, 3),
                    "count_duration": round(count_duration, 3),
                    "select_sql": data_sql
                }
            }


def _execute_get_tables(config):
    """获取 CHECK_DATA_DB 中可用的路径匹配表列表"""
    from database import get_db_connection

    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            # 过滤出可能相关的表（包含 cf 或 split 关键字的表）
            relevant_tables = [t for t in tables if 'cf' in t.lower() or 'split' in t.lower() or 'path' in t.lower()]
            if not relevant_tables:
                relevant_tables = tables
            return {"code": 200, "message": "success", "data": relevant_tables}


def _execute_get_provinces(codes: list, config):
    """根据站点编码查询省份名称

    使用内置的省份编码映射表，取编码前14位匹配省份
    """
    result = {}
    for code in codes:
        if code and len(code) >= 14:
            prefix = code[:14]
            result[prefix] = PROVINCE_CODE_MAP.get(prefix, "未知")
    return {"code": 200, "message": "success", "data": result}


def _execute_get_detail(passage_id: str, table_name: str, config):
    """根据通行标识ID查询详情"""
    from database import get_db_connection

    if not table_name:
        table_name = _get_path_match_table_name(config)
    if not table_name:
        return {"code": 404, "message": "未配置路径匹配数据表"}

    with get_db_connection("CHECK_DATA_DB", config) as conn:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            if not cursor.fetchone():
                return {"code": 404, "message": f"数据表 {table_name} 不存在"}

            cursor.execute(f"SELECT * FROM `{table_name}` WHERE `通行标识ID` = %s LIMIT 1", (passage_id,))
            row = cursor.fetchone()
            if not row:
                return {"code": 404, "message": f"未找到通行标识ID为 {passage_id} 的记录"}

            return {"code": 200, "message": "success", "data": dict(row)}


@router.get("/api/path-match/tables/")
async def get_path_match_tables(user: dict = Depends(get_current_user)):
    """获取可用的路径匹配数据表列表"""
    try:
        config = get_app_config()
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            result = await loop.run_in_executor(executor, _execute_get_tables, config)
            return result
        finally:
            executor.shutdown(wait=False)
    except Exception as e:
        logger.error(f"获取路径匹配表列表失败: {e}", exc_info=True)
        return {"code": 500, "message": f"获取表列表失败: {str(e)}"}


@router.post("/api/path-match/search")
async def search_path_match(request: PathMatchRequest, user: dict = Depends(get_current_user)):
    """路径匹配搜索接口（带超时控制）"""
    start_time = time.time()

    try:
        config = get_app_config()
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)

        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, _execute_search, request, config),
                timeout=QUERY_TIMEOUT
            )
            elapsed = time.time() - start_time
            logger.info(f"路径匹配搜索完成，耗时: {elapsed:.2f}秒")
            return result

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.warning(f"路径匹配搜索超时（{QUERY_TIMEOUT}秒），已耗时: {elapsed:.2f}秒")
            return {"code": 504, "message": f"查询超时（限制{QUERY_TIMEOUT}秒），请缩小查询范围后重试"}
        finally:
            executor.shutdown(wait=False)

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"路径匹配搜索失败，耗时: {elapsed:.2f}秒，错误: {e}", exc_info=True)
        return {"code": 500, "message": f"路径匹配搜索失败: {str(e)}"}


@router.post("/api/path-match/provinces")
async def get_provinces_by_codes(request: dict, user: dict = Depends(get_current_user)):
    """根据站点编码查询省份名称"""
    try:
        codes = request.get("codes", [])
        config = get_app_config()
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            result = await loop.run_in_executor(executor, _execute_get_provinces, codes, config)
            return result
        finally:
            executor.shutdown(wait=False)
    except Exception as e:
        logger.error(f"查询省份信息失败: {e}", exc_info=True)
        return {"code": 500, "message": f"查询省份信息失败: {str(e)}"}


@router.post("/api/path-match/detail")
async def get_path_match_detail(request: PathDetailRequest, user: dict = Depends(get_current_user)):
    """根据通行标识ID查询路径匹配详情"""
    try:
        config = get_app_config()
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            result = await loop.run_in_executor(
                executor, _execute_get_detail, request.passageId, request.tableName, config
            )
            return result
        finally:
            executor.shutdown(wait=False)
    except Exception as e:
        logger.error(f"获取路径匹配详情失败: {e}", exc_info=True)
        return {"code": 500, "message": f"获取详情失败: {str(e)}"}
