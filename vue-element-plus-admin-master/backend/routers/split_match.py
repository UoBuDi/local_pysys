"""
拆分匹配路由
包含数据库列表、表列表、数据查询、图片获取、导出、执行匹配等接口
"""

import logging
import re
import base64
import io
import json

import pymysql
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta

from core.dependencies import get_current_user
from core.models import ExecuteMatchRequest, UpdateMatchRequest, SplitStatisticsRequest
from core.config import get_config as get_app_config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/split-match/databases/")
async def get_split_match_databases(user: dict = Depends(get_current_user)):
    """获取可用的数据库列表"""
    try:
        config = get_app_config()

        databases = []

        for db_key in ['REMOTE_DB', 'LOCAL_DB', 'USER_DB']:
            if config.has_section(db_key):
                host = config.get(db_key, 'host', fallback='未知')
                database = config.get(db_key, 'database', fallback='未知')
                databases.append({
                    "key": db_key,
                    "name": f"{host}/{database}",
                    "type": "remote" if db_key == 'REMOTE_DB' else "local"
                })

        return {
            "code": 200,
            "message": "success",
            "data": databases
        }
    except Exception as e:
        logger.error(f"获取数据库列表失败: {e}")
        return {"code": 500, "message": "获取数据库列表失败"}


@router.get("/api/split-match/tables/")
async def get_split_match_tables(
    database: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """获取指定数据库的表列表（用于拆分匹配）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        db_type = database or 'CHECK_DATA_DB'

        with get_db_connection(db_type, config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]

                yc_pattern = re.compile(r'^\d{4}-\d{2}_yc$')
                monthly_tables = [t for t in tables if yc_pattern.match(t)]

                return {
                    "code": 200,
                    "message": "success",
                    "data": sorted(monthly_tables)
                }

    except Exception as e:
        logger.error(f"获取表列表失败: {e}")
        return {"code": 500, "message": "获取表列表失败"}


def validate_column_name(column_name: str) -> bool:
    """验证列名是否只包含合法字符（防止SQL注入）"""
    if not column_name:
        return False
    pattern = r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$'
    return bool(re.match(pattern, column_name))


@router.get("/api/split-match/data/")
async def get_split_match_data(
    table_name: str = Query(..., alias="table_name"),
    page: int = Query(1, alias="page"),
    page_size: int = Query(20, alias="page_size"),
    filters: Optional[str] = Query(None, alias="filters")
):
    """获取指定表的数据（分页+筛选）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        filter_dict = {}
        if filters:
            try:
                filter_dict = json.loads(filters)
                if not isinstance(filter_dict, dict):
                    filter_dict = {}
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"筛选参数格式错误: {filters}")
                filter_dict = {}

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                where_clauses = []
                params = []

                for key, value in filter_dict.items():
                    if value is not None and str(value).strip():
                        if not validate_column_name(key):
                            logger.warning(f"跳过非法列名: {key}")
                            continue
                        # 复核情况支持多选筛选，值为数组时使用 IN 查询
                        if key == '复核情况' and isinstance(value, list) and len(value) > 0:
                            placeholders = ', '.join(['%s'] * len(value))
                            where_clauses.append(f"`{key}` IN ({placeholders})")
                            params.extend([str(v).strip() for v in value])
                        else:
                            where_clauses.append(f"`{key}` = %s")
                            params.append(str(value).strip())

                where_sql = ""
                if where_clauses:
                    where_sql = " WHERE " + " AND ".join(where_clauses)

                if params:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`{where_sql}", params)
                else:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`{where_sql}")
                total = cursor.fetchone()[0]

                cursor.execute(f"DESCRIBE `{table_name}`")
                actual_columns = {row[0] for row in cursor.fetchall()}

                BLOB_COLUMNS = {'查核资料1', '查核资料2'}
                text_columns = [c for c in actual_columns if c not in BLOB_COLUMNS]
                col_list = ', '.join(f'`{c}`' for c in text_columns)

                offset = (page - 1) * page_size
                if params:
                    cursor.execute(f"SELECT {col_list} FROM `{table_name}`{where_sql} ORDER BY `门架通行时间` ASC LIMIT {offset}, {page_size}", params)
                else:
                    cursor.execute(f"SELECT {col_list} FROM `{table_name}`{where_sql} ORDER BY `门架通行时间` ASC LIMIT {offset}, {page_size}")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                data_list = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    data_list.append(row_dict)

                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "data": data_list,
                        "total": total,
                        "page": page,
                        "pageSize": page_size
                    }
                }

    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return {"code": 500, "message": "获取数据失败"}


@router.get("/api/split-match/original-image/")
async def get_original_image(
    table_name: str = Query(..., alias="table_name"),
    pass_id: str = Query(..., alias="pass_id"),
    field: str = Query(..., alias="field"),
    user: dict = Depends(get_current_user)
):
    """获取原始图片数据"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT `查核资料1`, `查核资料2` FROM `{table_name}` WHERE `通行标识ID` = %s",
                    (pass_id,)
                )
                result = cursor.fetchone()

                if not result:
                    return {"code": 404, "message": "记录不存在"}

                field_map = {'查核资料1': 0, '查核资料2': 1}
                col_index = field_map.get(field, 0)
                image_data = result[col_index]

                if image_data:
                    if isinstance(image_data, bytes):
                        image_data = image_data.decode('utf-8')

                    if isinstance(image_data, str):
                        if image_data.startswith('data:'):
                            if not image_data.startswith('data:image/'):
                                return {
                                    "code": 200,
                                    "message": "success",
                                    "data": None
                                }
                        else:
                            image_data = f"data:image/jpeg;base64,{image_data}"

                return {
                    "code": 200,
                    "message": "success",
                    "data": image_data
                }

    except Exception as e:
        logger.error(f"获取原图失败: {e}")
        return {"code": 500, "message": "获取原图失败"}


@router.get("/api/split-match/images/")
async def get_split_match_images(
    table_name: str = Query(..., alias="table_name"),
    pass_ids: str = Query(..., alias="pass_ids"),
    fields: str = Query(None, alias="fields"),
    user: dict = Depends(get_current_user)
):
    """获取拆分匹配的图片数据（批量缩略图，按通行标识ID分组返回）"""
    try:
        config = get_app_config()
        from database import get_db_connection
        from PIL import Image

        id_list = [pid.strip() for pid in pass_ids.split(',') if pid.strip()]
        if not id_list:
            return {"code": 400, "message": "pass_ids 不能为空"}

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                placeholders = ','.join(['%s'] * len(id_list))
                cursor.execute(
                    f"""SELECT `通行标识ID`, `查核资料1`, `查核资料2`
                        FROM `{table_name}` WHERE `通行标识ID` IN ({placeholders})""",
                    id_list
                )
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                result_map = {}
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    pass_id = row_dict.pop('通行标识ID')

                    for field in ['查核资料1', '查核资料2']:
                        raw = row_dict.get(field)
                        if not raw:
                            row_dict[field] = None
                            continue

                        try:
                            if isinstance(raw, bytes):
                                raw_str = raw.decode('utf-8')
                            else:
                                raw_str = str(raw)

                            if raw_str.startswith('data:'):
                                if not raw_str.startswith('data:image/'):
                                    row_dict[field] = None
                                    continue
                                comma_idx = raw_str.find(',')
                                if comma_idx != -1:
                                    raw_str = raw_str[comma_idx + 1:]

                            if len(raw_str) < 100:
                                row_dict[field] = None
                                continue

                            img_bytes = base64.b64decode(raw_str)
                            img = Image.open(io.BytesIO(img_bytes))
                            img.thumbnail((100, 100))
                            buf = io.BytesIO()
                            img.save(buf, format='JPEG', quality=60)
                            thumb_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                            row_dict[field] = f"data:image/jpeg;base64,{thumb_b64}"
                        except Exception:
                            row_dict[field] = None

                    result_map[pass_id] = row_dict

                return {
                    "code": 200,
                    "message": "success",
                    "data": result_map
                }

    except Exception as e:
        logger.error(f"获取图片失败: {e}")
        return {"code": 500, "message": "获取图片失败"}


@router.get("/api/split-match/export/")
async def export_split_match_data(
    table_name: str = Query(..., alias="table_name"),
    format: str = Query('csv', alias="format"),
    user: dict = Depends(get_current_user)
):
    """导出拆分匹配数据"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `{table_name}`")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                if format == 'csv':
                    import csv
                    import io

                    output = io.StringIO()
                    writer = csv.writer(output)

                    writer.writerow(columns)
                    writer.writerows(rows)

                    csv_content = output.getvalue()
                    output.close()

                    from fastapi.responses import Response
                    return Response(
                        content=csv_content,
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={table_name}.csv"}
                    )
                else:
                    data_list = []
                    for row in rows:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            row_dict[col] = row[i]
                        data_list.append(row_dict)

                    return {
                        "code": 200,
                        "message": "success",
                        "data": {
                            "tableName": table_name,
                            "columns": columns,
                            "column_types": {},
                            "data": data_list,
                            "rows": data_list,
                            "count": len(data_list)
                        }
                    }

    except Exception as e:
        logger.error(f"导出数据失败: {e}")
        return {"code": 500, "message": "导出数据失败"}


@router.post("/api/split-match/execute/")
async def execute_split_match(request: ExecuteMatchRequest, user: dict = Depends(get_current_user)):
    """执行拆分匹配操作

    支持两种模式：
    1. 传入records：对指定记录执行匹配
    2. 仅传入table_name：对全表执行匹配
    """
    try:
        config = get_app_config()
        from split_match_service import SplitMatchService
        service = SplitMatchService(config=config)

        if request.table_name and request.records:
            result = service.execute_match(
                request.table_name,
                request.records
            )
        elif request.table_name:
            result = service.execute_match(request.table_name)
        else:
            return {"code": 400, "message": "请提供表名或记录数据"}

        return {
            "code": 200,
            "message": f"匹配完成：已匹配 {result.get('matched_count', 0)} 条，未匹配 {result.get('unmatched_count', 0)} 条",
            "data": result
        }

    except Exception as e:
        logger.error(f"执行拆分匹配失败: {e}", exc_info=True)
        return {"code": 500, "message": f"执行拆分匹配失败: {str(e)}"}


@router.post("/api/split-match/preview/")
async def preview_split_match(request: ExecuteMatchRequest, user: dict = Depends(get_current_user)):
    """预览拆分匹配结果（不实际保存，仅返回将要执行的SQL语句）"""
    try:
        config = get_app_config()
        from split_match_service import SplitMatchService
        service = SplitMatchService(config=config)

        if not request.records or len(request.records) == 0:
            return {"code": 400, "message": "请提供要预览的记录"}

        preview_data = service.preview_match(
            request.table_name,
            request.records[:10]
        )

        if preview_data.get("error"):
            return {"code": 500, "message": preview_data["error"]}

        return {
            "code": 200,
            "message": "success",
            "data": preview_data
        }

    except Exception as e:
        logger.error(f"预览拆分匹配失败: {e}", exc_info=True)
        return {"code": 500, "message": f"预览拆分匹配失败: {str(e)}"}


@router.post("/api/split-match/update/")
async def update_split_match_data(request: UpdateMatchRequest, user: dict = Depends(get_current_user)):
    """更新拆分匹配的数据（支持乐观锁校验）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        # 乐观锁校验：若请求携带 version 字段，校验版本号
        if request.version is not None and not request.force_overwrite:
            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT version, updated_by FROM row_versions WHERE table_name = %s AND row_id = %s",
                        (request.table_name, request.row_id)
                    )
                    version_row = cursor.fetchone()

                    if version_row and version_row["version"] != request.version:
                        return {
                            "code": 409,
                            "message": "数据已被其他用户修改，请刷新后重试",
                            "data": {
                                "current_version": version_row["version"],
                                "updated_by": version_row["updated_by"]
                            }
                        }

        # 字段映射：数据库字段名 → 前端请求字段名
        field_mapping = {
            '查核资料1': 'image1_base64',
            '查核资料2': 'image2_base64',
            '复核情况': 'review_status',
            '核查通行标识': 'check_pass_id',
            '特情': 'special_situation',
            '核查拆分': 'check_split',
            '备注': 'remark'
        }

        # F-05: 在 UPDATE 之前查询旧值快照，确保记录的是真正的更新前数据
        old_values = {}
        with get_db_connection("CHECK_DATA_DB", config) as check_conn:
            with check_conn.cursor(pymysql.cursors.DictCursor) as check_cursor:
                check_cursor.execute(
                    f"SELECT * FROM `{request.table_name}` WHERE `通行标识ID` = %s",
                    (request.row_id,)
                )
                old_row = check_cursor.fetchone()
                if old_row:
                    for db_field, req_field in field_mapping.items():
                        if req_field in request.data and request.data[req_field] is not None:
                            old_values[db_field] = old_row.get(db_field)

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                update_fields = []
                params = []

                for db_field, req_field in field_mapping.items():
                    if req_field in request.data and request.data[req_field] is not None:
                        update_fields.append(f"`{db_field}` = %s")
                        params.append(request.data[req_field])

                if not update_fields:
                    return {"code": 400, "message": "没有需要更新的字段"}

                params.append(request.row_id)

                sql = f"UPDATE `{request.table_name}` SET {', '.join(update_fields)} WHERE `通行标识ID` = %s"
                cursor.execute(sql, params)
                conn.commit()

                affected_rows = cursor.rowcount

        # 更新成功后递增版本号，并获取新版本号
        username = user.get("username", "")
        user_id = user.get("id")
        new_version = None
        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "UPDATE row_versions SET version = version + 1, updated_by = %s WHERE table_name = %s AND row_id = %s",
                    (username, request.table_name, request.row_id)
                )
                conn.commit()
                if cursor.rowcount == 0:
                    cursor.execute(
                        "INSERT INTO row_versions (table_name, row_id, version, updated_by) VALUES (%s, %s, 2, %s)",
                        (request.table_name, request.row_id, username)
                    )
                    conn.commit()
                    new_version = 2
                else:
                    cursor.execute(
                        "SELECT version FROM row_versions WHERE table_name = %s AND row_id = %s",
                        (request.table_name, request.row_id)
                    )
                    vr = cursor.fetchone()
                    new_version = vr["version"] if vr else None

        # 构建变更字段映射（英文字段名→新值），用于协作广播
        changed_fields = {}
        for db_field, req_field in field_mapping.items():
            if req_field in request.data and request.data[req_field] is not None:
                changed_fields[req_field] = request.data[req_field]

        # 广播 row_updated 协作事件，通知同表房间其他用户局部更新
        try:
            from core.ws_manager_instance import status_manager
            await status_manager.broadcast_collaboration_event(
                table_name=request.table_name,
                event_type="row_updated",
                data={
                    "table_name": request.table_name,
                    "row_id": request.row_id,
                    "username": username,
                    "changed_fields": changed_fields
                },
                from_user_id=user_id
            )
        except Exception as broadcast_err:
            logger.warning(f"广播row_updated事件失败（不影响业务）: {broadcast_err}")

        # F-05: 记录编辑历史（使用 UPDATE 之前保存的 old_values 快照）
        try:
            with get_db_connection("USER_DB", config) as conn:
                with conn.cursor() as cursor:
                    # 构建 changed_fields JSON（旧值→新值），old_values 已在 UPDATE 前获取
                    history_changed = {}
                    for db_field, req_field in field_mapping.items():
                        if req_field in request.data and request.data[req_field] is not None:
                            history_changed[db_field] = {
                                "old": str(old_values.get(db_field, "")),
                                "new": str(request.data[req_field])
                            }

                    action = "force_overwrite" if request.force_overwrite else "update"
                    cursor.execute(
                        "INSERT INTO edit_history "
                        "(table_name, row_id, user_id, username, action, version_before, version_after, changed_fields, force_overwrite) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (request.table_name, request.row_id, user_id, username,
                         action, request.version, new_version,
                         json.dumps(history_changed, ensure_ascii=False) if history_changed else None,
                         1 if request.force_overwrite else 0)
                    )
                    conn.commit()
        except Exception as hist_err:
            logger.warning(f"记录编辑历史失败（不影响业务）: {hist_err}")

        return {
            "code": 200,
            "message": f"成功更新 {affected_rows} 条记录",
            "data": {
                "affectedRows": affected_rows,
                "version": new_version
            }
        }

    except Exception as e:
        logger.error(f"更新拆分匹配数据失败: {e}")
        return {"code": 500, "message": "更新拆分匹配数据失败"}


@router.get("/api/split-match/cf-tables/")
async def get_cf_tables(user: dict = Depends(get_current_user)):
    """获取查核数据相关的表列表"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                all_tables = [table[0] for table in cursor.fetchall()]

                cf_tables = [
                    table for table in all_tables
                    if any(keyword in table.lower() for keyword in ['cf', 'check', '查核'])
                ]

                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "tables": cf_tables,
                        "count": len(cf_tables)
                    }
                }

    except Exception as e:
        logger.error(f"获取查核表列表失败: {e}")
        return {"code": 500, "message": "获取查核表列表失败"}


@router.get("/api/split-match/verify-pass-id/")
async def verify_pass_id(
    pass_id: str = Query(..., alias="pass_id"),
    pass_id_secondary: Optional[str] = Query(None, alias="pass_id_secondary"),
    verify_type: str = Query(..., alias="verify_type"),
    user_id: Optional[int] = Query(None, alias="user_id"),
    username: Optional[str] = Query(None, alias="username"),
    user: dict = Depends(get_current_user)
):
    """核查通行标识ID或核查通行标识是否在详单查询表中存在匹配记录
    
    查询逻辑：
    - 接收 pass_id 和可选的 pass_id_secondary 两个值
    - 两个值都针对数据库表的 '通行标识ID' 字段进行 OR 条件查询
    - 示例SQL: SELECT * FROM table WHERE `通行标识ID`='值1' OR `通行标识ID`='值2'
    """
    import time as _time
    start = _time.time()
    try:
        config = get_app_config()
        from database import get_db_connection

        table_name = config.get('DETAIL_QUERY', 'table_name', fallback='')

        if not table_name:
            return {
                "code": 400,
                "message": "未配置详单查询表名，请检查config.ini的[DETAIL_QUERY]节"
            }

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                all_records = []

                try:
                    query_values = [pass_id]
                    
                    if pass_id_secondary and pass_id_secondary.strip():
                        secondary = pass_id_secondary.strip()
                        if secondary != pass_id:
                            query_values.append(secondary)

                    if len(query_values) == 1:
                        sql = f"SELECT * FROM `{table_name}` WHERE `通行标识ID` = %s LIMIT 50"
                        params = (query_values[0],)
                    else:
                        placeholders = " OR ".join(["`通行标识ID` = %s"] * len(query_values))
                        sql = f"SELECT * FROM `{table_name}` WHERE {placeholders} LIMIT 50"
                        params = tuple(query_values)

                    logger.info(f"[verify-pass-id] 执行查询: 表={table_name}, 值数量={len(query_values)}")
                    cursor.execute(sql, params)

                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    for row in rows:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            val = row[i]
                            if isinstance(val, bytes):
                                try:
                                    val = val.decode('utf-8')
                                except UnicodeDecodeError:
                                    val = val.hex()
                            row_dict[col] = val
                        all_records.append(row_dict)
                except Exception as e:
                    logger.error(f"查询详单表 {table_name} 失败: {e}")
                    return {
                        "code": 500,
                        "message": f"查询详单表失败: {str(e)}"
                    }

                elapsed = round((_time.time() - start) * 1000)

                return {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "exists": len(all_records) > 0,
                        "match_count": len(all_records),
                        "records": all_records,
                        "columns": columns if all_records else [],
                        "query_table": table_name,
                        "query_field": "通行标识ID",
                        "query_values": query_values,
                        "query_time": elapsed
                    }
                }

    except Exception as e:
        logger.error(f"核查通行标识失败: {e}")
        return {"code": 500, "message": f"核查通行标识失败: {str(e)}"}


@router.post("/api/split-match/split-statistics")
async def get_split_statistics(request: SplitStatisticsRequest):
    """获取拆分统计信息
    
    逻辑：
    1. 从当前选择的数据表中筛选'核查拆分'='已拆'的行
    2. 提取这些行的'通行标识ID'和'核查通行标识'字段值
    3. 用这些值与config.ini配置的详单查询表的'通行标识ID'字段匹配
    4. 统计匹配成功的记录条数(通行量)和'拆分路段拆分金额'求和(拆回金额)
    """
    try:
        config = get_app_config()
        from database import get_db_connection

        detail_table_name = config.get('DETAIL_QUERY', 'table_name', fallback='')

        if not detail_table_name:
            return {
                "code": 400,
                "message": "未配置详单查询表名，请检查config.ini的[DETAIL_QUERY]节"
            }

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                pass_ids = []

                try:
                    cursor.execute(
                        f"SELECT `通行标识ID`, `核查通行标识` FROM `{request.table_name}` WHERE `核查拆分` = %s",
                        ('已拆',)
                    )
                    rows = cursor.fetchall()
                    for row in rows:
                        id1 = row[0]
                        id2 = row[1]
                        if id1:
                            pass_ids.append(str(id1).strip())
                        if id2 and str(id2).strip() != (id1 or ''):
                            pass_ids.append(str(id2).strip())
                except Exception as e:
                    logger.error(f"查询拆分表 {request.table_name} 失败: {e}")
                    return {
                        "code": 500,
                        "message": f"查询拆分表失败: {str(e)}"
                    }

                if not pass_ids:
                    return {
                        "code": 200,
                        "message": "success",
                        "data": {
                            "split_count": 0,
                            "total_split_amount": 0
                        }
                    }

                unique_ids = list(set(pass_ids))
                placeholders = ','.join(['%s'] * len(unique_ids))

                try:
                    sql = f"""
                        SELECT 
                            COUNT(*) as count,
                            COALESCE(SUM(CAST(`拆分路段拆分金额` AS DECIMAL(18,2))), 0) as total_amount
                        FROM `{detail_table_name}`
                        WHERE `通行标识ID` IN ({placeholders})
                    """
                    cursor.execute(sql, tuple(unique_ids))
                    row = cursor.fetchone()

                    split_count = row[0] or 0
                    total_amount_fen = float(row[1] or 0)
                    total_amount_yuan = round(total_amount_fen / 100, 2)

                    return {
                        "code": 200,
                        "message": "success",
                        "data": {
                            "split_count": split_count,
                            "total_split_amount": total_amount_yuan
                        }
                    }
                except Exception as e:
                    logger.error(f"查询详单表 {detail_table_name} 统计失败: {e}")
                    return {
                        "code": 500,
                        "message": f"查询详单表统计失败: {str(e)}"
                    }

    except Exception as e:
        logger.error(f"获取拆分统计失败: {e}")
        return {"code": 500, "message": f"获取拆分统计失败: {str(e)}"}




@router.post("/api/split-match/lock/")
async def lock_row(request: dict, user: dict = Depends(get_current_user)):
    """获取行锁（内存存储，零SQL开销）"""
    table_name = request.get("table_name", "")
    row_id = request.get("row_id", "")
    if not table_name or not row_id:
        return {"code": 400, "message": "table_name 和 row_id 不能为空"}

    user_id = user.get("id", 0)
    username = user.get("username", "")

    try:
        from core.ws_manager_instance import status_manager
        result = status_manager.acquire_row_lock(table_name, row_id, user_id, username)

        # 加锁成功时广播row_locked事件，通知同表房间其他用户
        if result.get("locked") and result.get("own_lock"):
            try:
                await status_manager.broadcast_collaboration_event(
                    table_name=table_name,
                    event_type="row_locked",
                    data={
                        "table_name": table_name,
                        "row_id": row_id,
                        "user_id": user_id,
                        "username": username
                    },
                    from_user_id=user_id
                )
            except Exception as broadcast_err:
                logger.warning(f"广播row_locked事件失败（不影响业务）: {broadcast_err}")

        return {"code": 200, "data": result}
    except Exception as e:
        logger.error(f"获取行锁失败: {e}")
        return {"code": 500, "message": f"获取行锁失败: {str(e)}"}


@router.post("/api/split-match/unlock/")
async def unlock_row(request: dict, user: dict = Depends(get_current_user)):
    """释放行锁（内存存储，零SQL开销）"""
    table_name = request.get("table_name", "")
    row_id = request.get("row_id", "")
    user_id = user.get("id", 0)

    try:
        from core.ws_manager_instance import status_manager
        released = status_manager.release_row_lock(table_name, row_id, user_id)

        # 释放锁成功时广播row_unlocked事件，通知同表房间其他用户
        if released:
            try:
                await status_manager.broadcast_collaboration_event(
                    table_name=table_name,
                    event_type="row_unlocked",
                    data={
                        "table_name": table_name,
                        "row_id": row_id,
                        "user_id": user_id
                    },
                    from_user_id=user_id
                )
            except Exception as broadcast_err:
                logger.warning(f"广播row_unlocked事件失败（不影响业务）: {broadcast_err}")

        return {"code": 200, "message": "success", "data": {"released": released}}
    except Exception as e:
        logger.error(f"释放行锁失败: {e}")
        return {"code": 500, "message": f"释放行锁失败: {str(e)}"}


@router.get("/api/split-match/active-locks/")
async def get_active_locks(
    table_name: str = Query(..., description="表名"),
    user: dict = Depends(get_current_user)
):
    """获取指定表的活跃行锁列表（内存存储，零SQL开销）"""
    try:
        from core.ws_manager_instance import status_manager
        locks = status_manager.get_active_locks(table_name)
        return {"code": 200, "message": "success", "data": locks}
    except Exception as e:
        logger.error(f"获取活跃锁列表失败: {e}")
        return {"code": 500, "message": f"获取活跃锁列表失败: {str(e)}"}


@router.get("/api/split-match/row-version/")
async def get_row_version(
    table_name: str = Query(..., description="表名"),
    row_id: str = Query(..., description="行标识ID"),
    user: dict = Depends(get_current_user)
):
    """获取行版本号（使用数据库 row_versions 表，懒初始化）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT version, updated_by, updated_at FROM row_versions WHERE table_name = %s AND row_id = %s",
                    (table_name, row_id)
                )
                row = cursor.fetchone()

                if row:
                    updated_at = row["updated_at"]
                    return {
                        "code": 200,
                        "data": {
                            "version": row["version"],
                            "updated_by": row["updated_by"],
                            "updated_at": updated_at.isoformat() if isinstance(updated_at, datetime) else str(updated_at)
                        }
                    }

                # 懒初始化：记录不存在时创建
                cursor.execute(
                    "INSERT INTO row_versions (table_name, row_id, version) VALUES (%s, %s, 1)",
                    (table_name, row_id)
                )
                conn.commit()
                return {
                    "code": 200,
                    "data": {
                        "version": 1,
                        "updated_by": None,
                        "updated_at": None
                    }
                }

    except Exception as e:
        logger.error(f"获取行版本号失败: {e}")
        return {"code": 500, "message": f"获取行版本号失败: {str(e)}"}


@router.get("/api/split-match/single-row/")
async def get_single_row(
    table_name: str = Query(..., description="表名"),
    row_id: str = Query(..., description="行标识ID"),
    user: dict = Depends(get_current_user)
):
    """获取单行数据（排除BLOB列，用于协作局部更新）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("CHECK_DATA_DB", config) as conn:
            with conn.cursor() as cursor:
                # 获取表结构，排除BLOB列
                cursor.execute(f"DESCRIBE `{table_name}`")
                actual_columns = {row[0] for row in cursor.fetchall()}
                BLOB_COLUMNS = {'查核资料1', '查核资料2'}
                text_columns = [c for c in actual_columns if c not in BLOB_COLUMNS]
                col_list = ', '.join(f'`{c}`' for c in text_columns)

                cursor.execute(
                    f"SELECT {col_list} FROM `{table_name}` WHERE `通行标识ID` = %s LIMIT 1",
                    (row_id,)
                )
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()

                if not row:
                    return {"code": 404, "message": "未找到该行数据"}

                row_dict = {}
                for i, col in enumerate(columns):
                    val = row[i]
                    if isinstance(val, datetime):
                        val = val.isoformat()
                    elif isinstance(val, bytes):
                        val = val.decode('utf-8', errors='replace')
                    row_dict[col] = val

                return {"code": 200, "data": row_dict}

    except Exception as e:
        logger.error(f"获取单行数据失败: {e}")
        return {"code": 500, "message": f"获取单行数据失败: {str(e)}"}


# ==================== 字段级编辑标识 ====================

@router.post("/api/split-match/field-editing/mark/")
async def mark_field_editing(request: dict, user: dict = Depends(get_current_user)):
    """标记字段正在被编辑（字段级编辑标识）"""
    table_name = request.get("table_name", "")
    row_id = request.get("row_id", "")
    field_name = request.get("field_name", "")
    if not all([table_name, row_id, field_name]):
        return {"code": 400, "message": "table_name、row_id、field_name 不能为空"}

    user_id = user.get("id", 0)
    username = user.get("username", "")

    try:
        from core.ws_manager_instance import status_manager
        result = status_manager.mark_field_editing(table_name, row_id, field_name, user_id, username)

        # 广播字段编辑事件给同房间其他用户
        await status_manager.broadcast_collaboration_event(
            table_name=table_name,
            event_type="field_editing",
            data={
                "table_name": table_name,
                "row_id": row_id,
                "field_name": field_name,
                "user_id": user_id,
                "username": username,
                "action": "focus",
                "active_fields": result["active_fields"]
            },
            from_user_id=user_id
        )
        return {"code": 200, "data": result}
    except Exception as e:
        logger.error(f"标记字段编辑失败: {e}")
        return {"code": 500, "message": f"标记字段编辑失败: {str(e)}"}


@router.post("/api/split-match/field-editing/unmark/")
async def unmark_field_editing(request: dict, user: dict = Depends(get_current_user)):
    """取消字段编辑标记"""
    table_name = request.get("table_name", "")
    row_id = request.get("row_id", "")
    field_name = request.get("field_name", "")
    if not all([table_name, row_id, field_name]):
        return {"code": 400, "message": "table_name、row_id、field_name 不能为空"}

    user_id = user.get("id", 0)

    try:
        from core.ws_manager_instance import status_manager
        released = status_manager.unmark_field_editing(table_name, row_id, field_name, user_id)

        # 获取取消后的活跃字段列表
        active_fields = status_manager.get_row_field_editors(table_name, row_id)

        # 广播字段编辑取消事件
        await status_manager.broadcast_collaboration_event(
            table_name=table_name,
            event_type="field_editing",
            data={
                "table_name": table_name,
                "row_id": row_id,
                "field_name": field_name,
                "user_id": user_id,
                "action": "blur",
                "active_fields": active_fields
            },
            from_user_id=user_id
        )
        return {"code": 200, "data": {"released": released, "active_fields": active_fields}}
    except Exception as e:
        logger.error(f"取消字段编辑标记失败: {e}")
        return {"code": 500, "message": f"取消字段编辑标记失败: {str(e)}"}


@router.get("/api/split-match/field-editing/active/")
async def get_active_field_editors(
    table_name: str = Query(..., description="表名"),
    row_id: str = Query(..., description="行标识ID"),
    user: dict = Depends(get_current_user)
):
    """获取某行正在编辑的字段列表"""
    try:
        from core.ws_manager_instance import status_manager
        active_fields = status_manager.get_row_field_editors(table_name, row_id)
        return {"code": 200, "data": active_fields}
    except Exception as e:
        logger.error(f"获取字段编辑状态失败: {e}")
        return {"code": 500, "message": f"获取字段编辑状态失败: {str(e)}"}


# ==================== 光标位置同步 ====================

@router.post("/api/split-match/cursor-position/")
async def update_cursor_position(request: dict, user: dict = Depends(get_current_user)):
    """更新用户光标位置（光标位置同步）"""
    table_name = request.get("table_name", "")
    row_id = request.get("row_id", "")
    field_name = request.get("field_name", "")
    if not all([table_name, row_id, field_name]):
        return {"code": 400, "message": "table_name、row_id、field_name 不能为空"}

    user_id = user.get("id", 0)
    username = user.get("username", "")

    try:
        from core.ws_manager_instance import status_manager
        result = status_manager.update_cursor_position(table_name, user_id, username, row_id, field_name)

        # 广播光标位置给同房间其他用户
        await status_manager.broadcast_collaboration_event(
            table_name=table_name,
            event_type="cursor_position",
            data={
                "table_name": table_name,
                "user_id": user_id,
                "username": username,
                "row_id": row_id,
                "field_name": field_name
            },
            from_user_id=user_id
        )
        return {"code": 200, "data": result}
    except Exception as e:
        logger.error(f"更新光标位置失败: {e}")
        return {"code": 500, "message": f"更新光标位置失败: {str(e)}"}


@router.get("/api/split-match/cursor-positions/")
async def get_cursor_positions(
    table_name: str = Query(..., description="表名"),
    user: dict = Depends(get_current_user)
):
    """获取某表所有用户的光标位置"""
    try:
        from core.ws_manager_instance import status_manager
        user_id = user.get("id", 0)
        positions = status_manager.get_cursor_positions(table_name, exclude_user_id=user_id)
        return {"code": 200, "data": positions}
    except Exception as e:
        logger.error(f"获取光标位置失败: {e}")
        return {"code": 500, "message": f"获取光标位置失败: {str(e)}"}


@router.post("/api/split-match/cursor-clear/")
async def clear_cursor_position(request: dict, user: dict = Depends(get_current_user)):
    """清除用户光标位置（关闭编辑对话框时调用）"""
    table_name = request.get("table_name", "")
    if not table_name:
        return {"code": 400, "message": "table_name 不能为空"}

    user_id = user.get("id", 0)

    try:
        from core.ws_manager_instance import status_manager
        # 清除光标位置
        status_manager.clear_cursor_position(table_name, user_id)
        # 清除该用户在该表所有行的字段编辑标记
        # 遍历 field_editing 查找该用户的标记
        keys_to_delete = [
            k for k, v in status_manager.field_editing.items()
            if k.startswith(f"{table_name}:") and v["user_id"] == user_id
        ]
        for k in keys_to_delete:
            del status_manager.field_editing[k]

        # 广播清除事件
        await status_manager.broadcast_collaboration_event(
            table_name=table_name,
            event_type="cursor_cleared",
            data={
                "table_name": table_name,
                "user_id": user_id
            },
            from_user_id=user_id
        )
        return {"code": 200, "data": {"cleared": True}}
    except Exception as e:
        logger.error(f"清除光标位置失败: {e}")
        return {"code": 500, "message": f"清除光标位置失败: {str(e)}"}


# ==================== F-05: 编辑历史 ====================

@router.get("/api/split-match/edit-history/")
async def get_edit_history(
    table_name: str = Query(..., description="表名"),
    row_id: Optional[str] = Query(None, description="行标识ID（可选，不传则查全表）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    user: dict = Depends(get_current_user)
):
    """查询编辑历史记录（F-05）"""
    try:
        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                where = "WHERE table_name = %s"
                params: list = [table_name]

                if row_id:
                    where += " AND row_id = %s"
                    params.append(row_id)

                # 查询总数
                cursor.execute(f"SELECT COUNT(*) AS total FROM edit_history {where}", tuple(params))
                total = cursor.fetchone()["total"]

                # 分页查询
                offset = (page - 1) * page_size
                cursor.execute(
                    f"SELECT id, table_name, row_id, user_id, username, action, "
                    f"version_before, version_after, changed_fields, force_overwrite, created_at "
                    f"FROM edit_history {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    tuple(params) + (page_size, offset)
                )
                rows = cursor.fetchall()

                # 解析 changed_fields JSON
                for row in rows:
                    if row.get("changed_fields") and isinstance(row["changed_fields"], str):
                        try:
                            row["changed_fields"] = json.loads(row["changed_fields"])
                        except Exception:
                            pass
                    if row.get("created_at"):
                        row["created_at"] = row["created_at"].isoformat()

                return {
                    "code": 200,
                    "data": {
                        "total": total,
                        "page": page,
                        "page_size": page_size,
                        "records": rows
                    }
                }
    except Exception as e:
        logger.error(f"查询编辑历史失败: {e}")
        return {"code": 500, "message": f"查询编辑历史失败: {str(e)}"}


@router.post("/api/system/cleanup/")
async def manual_cleanup(
    days: int = Query(90, ge=1, description="清理多少天前的数据"),
    user: dict = Depends(get_current_user)
):
    """手动触发数据清理（管理员，F-05/F-11）"""
    try:
        # 仅管理员可操作
        if user.get("role", "") != "admin":
            return {"code": 403, "message": "仅管理员可执行数据清理"}

        config = get_app_config()
        from database import get_db_connection

        with get_db_connection("USER_DB", config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM edit_history WHERE created_at < NOW() - INTERVAL %s DAY", (days,))
                edit_deleted = cursor.rowcount
                cursor.execute("DELETE FROM notifications WHERE created_at < NOW() - INTERVAL %s DAY", (days,))
                notif_deleted = cursor.rowcount
                conn.commit()

        return {
            "code": 200,
            "data": {
                "edit_history_deleted": edit_deleted,
                "notifications_deleted": notif_deleted,
                "days": days
            }
        }
    except Exception as e:
        logger.error(f"数据清理失败: {e}")
        return {"code": 500, "message": f"数据清理失败: {str(e)}"}
