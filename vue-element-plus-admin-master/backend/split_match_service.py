import pymysql
import logging
import time
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)


def compress_base64_image(base64_data, max_size: int = 200, quality: int = 60) -> str:
    """
    将 base64 图片压缩为缩略图
    
    Args:
        base64_data: base64 编码的图片数据（str 或 bytes）
            - str: 可能包含 data:image/xxx;base64, 前缀，或纯 base64 字符串
            - bytes: 可能是原始图片二进制数据，或 base64 编码字符串的 bytes 形式
        max_size: 缩略图最大边长
        quality: JPEG 压缩质量 (1-100)
    
    Returns:
        压缩后的 base64 图片数据（带 data:image/jpeg;base64, 前缀）
    """
    if not base64_data:
        return base64_data
    
    def get_data_preview(data, max_len=50):
        """获取数据预览"""
        if isinstance(data, bytes):
            preview = data[:max_len]
            try:
                return f"bytes({len(data)}): {preview.decode('utf-8', errors='replace')}..."
            except:
                return f"bytes({len(data)}): {preview.hex()}..."
        elif isinstance(data, str):
            return f"str({len(data)}): {data[:max_len]}..."
        return f"{type(data).__name__}: {str(data)[:max_len]}..."
    
    def try_decode_as_image(data_bytes, debug_context=""):
        """尝试将 bytes 作为原始图片数据解析"""
        try:
            image = Image.open(io.BytesIO(data_bytes))
            logger.debug(f"[图片压缩] {debug_context} 成功解析为图片: {image.size}x{image.mode}")
            return image
        except Exception as e:
            logger.debug(f"[图片压缩] {debug_context} 不是原始图片数据: {e}")
            return None
    
    def try_decode_as_base64_string(data_bytes, debug_context=""):
        """尝试将 bytes 解码为 base64 字符串"""
        try:
            decoded_str = data_bytes.decode('utf-8')
            if decoded_str.startswith('data:image'):
                header_end = decoded_str.find(',')
                if header_end != -1:
                    result = decoded_str[header_end + 1:]
                    logger.debug(f"[图片压缩] {debug_context} 解码为 data URL base64: {len(result)} 字符")
                    return result
                logger.debug(f"[图片压缩] {debug_context} 解码为 data URL (无逗号)")
                return decoded_str
            logger.debug(f"[图片压缩] {debug_context} 解码为纯 base64 字符串: {len(decoded_str)} 字符")
            return decoded_str
        except Exception as e:
            logger.debug(f"[图片压缩] {debug_context} 无法解码为 UTF-8 字符串: {e}")
            return None
    
    def is_valid_base64(s):
        """检查字符串是否看起来像有效的 base64"""
        if not s or not isinstance(s, str):
            return False
        s = s.strip()
        if len(s) < 10:
            return False
        import re
        base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
        return bool(base64_pattern.match(s))
    
    logger.debug(f"[图片压缩] 输入数据类型: {type(base64_data).__name__}, 预览: {get_data_preview(base64_data)}")
    
    try:
        image = None
        image_data = None
        
        if isinstance(base64_data, bytes):
            logger.debug(f"[图片压缩] 处理 bytes 类型数据, 长度: {len(base64_data)}")
            
            image = try_decode_as_image(base64_data, "尝试1: 直接解析 bytes")
            if image:
                image_data = base64_data
            else:
                decoded_str = try_decode_as_base64_string(base64_data, "尝试2")
                if decoded_str:
                    if is_valid_base64(decoded_str):
                        logger.debug(f"[图片压缩] 尝试2: 解码 base64 字符串")
                        try:
                            image_data = base64.b64decode(decoded_str)
                            image = try_decode_as_image(image_data, "尝试2: 解码后解析")
                        except Exception as e:
                            logger.warning(f"[图片压缩] 尝试2: base64 解码失败: {e}")
                    else:
                        logger.debug(f"[图片压缩] 尝试2: 字符串不是有效的 base64 格式")
        
        elif isinstance(base64_data, str):
            logger.debug(f"[图片压缩] 处理 str 类型数据, 长度: {len(base64_data)}")
            
            if base64_data.startswith('data:image'):
                header_end = base64_data.find(',')
                if header_end != -1:
                    pure_base64 = base64_data[header_end + 1:]
                else:
                    pure_base64 = base64_data
                logger.debug(f"[图片压缩] 提取 data URL 中的 base64: {len(pure_base64)} 字符")
                image_data = base64.b64decode(pure_base64)
            else:
                logger.debug(f"[图片压缩] 直接解码 base64 字符串")
                image_data = base64.b64decode(base64_data)
            image = try_decode_as_image(image_data, "解码后解析")
        
        else:
            logger.warning(f"[图片压缩] 不支持的输入类型: {type(base64_data)}")
            return base64_data
        
        if image is None:
            logger.warning(f"[图片压缩] 无法解析图片数据，返回 None")
            return None
        
        if image.mode in ('RGBA', 'P'):
            logger.debug(f"[图片压缩] 转换图片模式: {image.mode} -> RGB")
            image = image.convert('RGB')
        
        original_width, original_height = image.size
        if max(original_width, original_height) > max_size:
            ratio = max_size / max(original_width, original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            logger.debug(f"[图片压缩] 缩放图片: {original_width}x{original_height} -> {new_width}x{new_height}")
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        compressed_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        logger.debug(f"[图片压缩] 压缩成功: 原始 {len(base64_data) if isinstance(base64_data, (str, bytes)) else 'N/A'} -> 压缩后 {len(compressed_base64)} 字符")
        return f"data:image/jpeg;base64,{compressed_base64}"
    
    except Exception as e:
        logger.warning(f"[图片压缩] 压缩过程异常: {e}")
        try:
            if isinstance(base64_data, bytes):
                decoded_str = try_decode_as_base64_string(base64_data, "降级处理")
                if decoded_str:
                    if decoded_str.startswith('data:image'):
                        logger.debug(f"[图片压缩] 降级: 返回原始 data URL")
                        return decoded_str
                    if is_valid_base64(decoded_str):
                        logger.debug(f"[图片压缩] 降级: 返回带前缀的 base64")
                        return f"data:image/jpeg;base64,{decoded_str}"
                    try:
                        image_data = base64.b64decode(decoded_str)
                        encoded = base64.b64encode(image_data).decode('utf-8')
                        logger.debug(f"[图片压缩] 降级: 重新编码后返回")
                        return f"data:image/jpeg;base64,{encoded}"
                    except Exception:
                        pass
                encoded = base64.b64encode(base64_data).decode('utf-8')
                logger.debug(f"[图片压缩] 降级: 直接编码 bytes 返回")
                return f"data:image/jpeg;base64,{encoded}"
            elif isinstance(base64_data, str):
                if base64_data.startswith('data:image'):
                    logger.debug(f"[图片压缩] 降级: 返回原始 data URL 字符串")
                    return base64_data
                logger.debug(f"[图片压缩] 降级: 返回带前缀的原始字符串")
                return f"data:image/jpeg;base64,{base64_data}"
            logger.warning(f"[图片压缩] 降级处理失败: 未知类型")
            return None
        except Exception as e2:
            logger.error(f"[图片压缩] 降级处理异常: {e2}")
            return None


def format_sql(sql_query: str, sql_params: list) -> str:
    """格式化 SQL 语句，替换参数为实际值"""
    temp_sql = sql_query.replace('%%', '__PERCENT_SIGN__')
    
    for param in sql_params:
        if isinstance(param, str):
            temp_sql = temp_sql.replace('%s', f"'{param}'", 1)
        else:
            temp_sql = temp_sql.replace('%s', str(param), 1)
    
    debug_sql = temp_sql.replace('__PERCENT_SIGN__', '%')
    return debug_sql


class SplitMatchService:
    def __init__(self, config=None):
        self.config = config
    
    def _get_db_connection(self):
        """获取CHECK_DATA_DB数据库连接"""
        try:
            db_config = {
                'host': self.config.get('CHECK_DATA_DB', 'host', fallback='localhost'),
                'port': self.config.getint('CHECK_DATA_DB', 'port', fallback=3306),
                'user': self.config.get('CHECK_DATA_DB', 'user', fallback='root'),
                'password': self.config.get('CHECK_DATA_DB', 'password', fallback='password'),
                'database': self.config.get('CHECK_DATA_DB', 'database', fallback='check_data'),
                'charset': self.config.get('CHECK_DATA_DB', 'charset', fallback='utf8mb4')
            }
            conn = pymysql.connect(**db_config)
            return conn
        except Exception as e:
            logger.error(f"获取数据库连接失败: {e}")
            return None
    
    def get_yc_tables(self):
        """获取check_data数据库中所有以_yc结尾的表"""
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return []
            
            check_data_config = {
                'host': self.config.get('CHECK_DATA_DB', 'host', fallback='localhost'),
                'port': self.config.getint('CHECK_DATA_DB', 'port', fallback=3306),
                'user': self.config.get('CHECK_DATA_DB', 'user', fallback='root'),
                'password': self.config.get('CHECK_DATA_DB', 'password', fallback='password'),
                'database': self.config.get('CHECK_DATA_DB', 'database', fallback='check_data'),
                'charset': self.config.get('CHECK_DATA_DB', 'charset', fallback='utf8mb4')
            }
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME LIKE %s
                    ORDER BY TABLE_NAME
                """
                cursor.execute(query, (check_data_config['database'], '%_yc'))
                tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
            
            return tables
        except Exception as e:
            logger.error(f"获取_yc表列表失败: {e}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
    
    def search_cf_tables(self):
        """获取拆分数据表列表（CF表）"""
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return []
            
            check_data_config = {
                'host': self.config.get('CHECK_DATA_DB', 'host', fallback='localhost'),
                'port': self.config.getint('CHECK_DATA_DB', 'port', fallback=3306),
                'user': self.config.get('CHECK_DATA_DB', 'user', fallback='root'),
                'password': self.config.get('CHECK_DATA_DB', 'password', fallback='password'),
                'database': self.config.get('CHECK_DATA_DB', 'database', fallback='check_data'),
                'charset': self.config.get('CHECK_DATA_DB', 'charset', fallback='utf8mb4')
            }
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = %s 
                    ORDER BY TABLE_NAME
                """
                cursor.execute(query, (check_data_config['database'],))
                tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
            
            return tables
        except Exception as e:
            logger.error(f"获取CF表列表失败: {e}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
    
    def get_table_data(self, table_name, filters=None, page=1, page_size=20):
        """获取指定表的数据，支持分页和字段筛选"""
        conn = None
        start_time = time.time()
        debug_info = {}
        try:
            conn = self._get_db_connection()
            if not conn:
                return {"data": [], "columns": [], "total": 0, "debug": debug_info}
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                where_conditions = []
                params = []
                
                if filters:
                    for key, value in filters.items():
                        if value:
                            where_conditions.append(f"`{key}` LIKE %s")
                            params.append(f"%{value}%")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                count_sql = f"SELECT COUNT(*) as total FROM `{table_name}` WHERE {where_clause}"
                formatted_count_sql = format_sql(count_sql, params)
                
                count_start = time.time()
                cursor.execute(count_sql, params)
                total_result = cursor.fetchone()
                total = total_result['total'] if total_result else 0
                count_duration = time.time() - count_start
                
                offset = (page - 1) * page_size
                image_fields = ['查核资料1', '查核资料2']
                non_image_cols = []
                cols_start = time.time()
                cursor.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
                    (self.config.get('CHECK_DATA_DB', 'database', fallback='check_data'), table_name)
                )
                all_cols = [r['COLUMN_NAME'] for r in cursor.fetchall()]
                non_image_cols = [c for c in all_cols if c not in image_fields]
                cols_duration = time.time() - cols_start
                
                select_cols = ', '.join(f'`{c}`' for c in non_image_cols)
                select_sql = f"SELECT {select_cols} FROM `{table_name}` WHERE {where_clause} LIMIT %s OFFSET %s"
                select_params = params + [page_size, offset]
                formatted_select_sql = format_sql(select_sql, select_params)
                
                select_start = time.time()
                cursor.execute(select_sql, select_params)
                data = cursor.fetchall()
                select_duration = time.time() - select_start
                
                columns = []
                if data and len(data) > 0:
                    columns = list(data[0].keys())
                
                total_time = time.time() - start_time
                debug_info = {
                    "select_sql": formatted_select_sql,
                    "count_sql": formatted_count_sql,
                    "total_time": total_time,
                    "count_duration": count_duration,
                    "select_duration": select_duration,
                    "cols_duration": cols_duration
                }
            
            return {"data": data, "columns": columns, "total": total, "debug": debug_info}
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"获取表数据失败: {e}", exc_info=True)
            return {"data": [], "columns": [], "total": 0, "debug": {"total_time": total_time}}
        finally:
            if conn:
                conn.close()
    
    def get_original_image(self, table_name, pass_id, field):
        """获取原图数据"""
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return None
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = f"SELECT `{field}` FROM `{table_name}` WHERE `通行标识ID` = %s"
                cursor.execute(sql, (pass_id,))
                result = cursor.fetchone()
                
                if result and field in result and result[field]:
                    return result[field]
                return None
        except Exception as e:
            logger.error(f"获取原图失败: {e}", exc_info=True)
            return None
        finally:
            if conn:
                conn.close()
    
    def get_table_images(self, table_name, pass_ids, fields=None):
        """批量获取指定记录的图片缩略图"""
        if fields is None:
            fields = ['查核资料1', '查核资料2']
        
        if not pass_ids:
            return {}
        
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return {}
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                field_list = ', '.join(f'`{f}`' for f in fields)
                placeholders = ', '.join(['%s'] * len(pass_ids))
                sql = f"SELECT `通行标识ID`, {field_list} FROM `{table_name}` WHERE `通行标识ID` IN ({placeholders})"
                cursor.execute(sql, tuple(pass_ids))
                rows = cursor.fetchall()
                
                result = {}
                for row in rows:
                    pass_id = row['通行标识ID']
                    images = {}
                    for field in fields:
                        if field in row and row[field]:
                            images[field] = compress_base64_image(row[field], max_size=200, quality=60)
                        else:
                            images[field] = None
                    result[pass_id] = images
                
                return result
        except Exception as e:
            logger.error(f"批量获取图片失败: {e}", exc_info=True)
            return {}
        finally:
            if conn:
                conn.close()
    
    def get_table_columns_info(self, table_name):
        """获取指定表的列信息，包括字段名和数据类型"""
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return {}
            
            check_data_config = {
                'host': self.config.get('CHECK_DATA_DB', 'host', fallback='localhost'),
                'port': self.config.getint('CHECK_DATA_DB', 'port', fallback=3306),
                'user': self.config.get('CHECK_DATA_DB', 'user', fallback='root'),
                'password': self.config.get('CHECK_DATA_DB', 'password', fallback='password'),
                'database': self.config.get('CHECK_DATA_DB', 'database', fallback='check_data'),
                'charset': self.config.get('CHECK_DATA_DB', 'charset', fallback='utf8mb4')
            }
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """
                cursor.execute(query, (check_data_config['database'], table_name))
                columns_info = cursor.fetchall()
                
                # 转换为字典格式，方便访问
                column_type_map = {}
                for col in columns_info:
                    column_type_map[col['column_name']] = col['data_type']
            
            return column_type_map
        except Exception as e:
            logger.error(f"获取表列信息失败: {e}", exc_info=True)
            return {}
        finally:
            if conn:
                conn.close()
    
    def get_all_table_data(self, table_name, filters=None):
        """获取指定表的完整数据，支持字段筛选但不进行分页"""
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return {"data": [], "columns": [], "column_types": {}}
            
            # 获取列类型信息
            column_types = self.get_table_columns_info(table_name)
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                where_conditions = []
                params = []
                
                if filters:
                    for key, value in filters.items():
                        if value:
                            where_conditions.append(f"`{key}` LIKE %s")
                            params.append(f"%{value}%")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                select_sql = f"SELECT * FROM `{table_name}` WHERE {where_clause}"
                cursor.execute(select_sql, params)
                data = cursor.fetchall()
                
                columns = []
                if data and len(data) > 0:
                    columns = list(data[0].keys())
            
            return {"data": data, "columns": columns, "column_types": column_types}
        except Exception as e:
            logger.error(f"获取完整表数据失败: {e}", exc_info=True)
            return {"data": [], "columns": [], "column_types": {}}
        finally:
            if conn:
                conn.close()
    
    def execute_match(self, table_name, records=None):
        """执行拆分匹配，使用LEFT JOIN方式一次性更新所有记录
        
        匹配逻辑：
        1. 使用LEFT JOIN将YC表与CF表连接
        2. 通过通行标识ID和核查通行标识进行匹配
        3. 一次性更新所有记录的核查拆分字段
        4. 支持传入records参数或处理所有记录
        """
        conn = None
        start_time = time.time()
        debug_info = {}
        
        try:
            conn = self._get_db_connection()
            if not conn:
                logger.error("无法获取数据库连接")
                return {
                    "matched_count": 0, 
                    "unmatched_count": 0, 
                    "total": 0,
                    "pass_id_matched": 0,
                    "check_id_matched": 0,
                    "debug": debug_info
                }
            
            cf_table = "202005-202311_cf_1215"
            debug_info['cf_table'] = cf_table
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 情况1：有传入records参数，需要先创建临时表
                if records is not None:
                    debug_info['records_source'] = '前端传入'
                    debug_info['records_count'] = len(records)
                    
                    # 过滤掉无效记录（至少有一个ID不为空）
                    valid_records = []
                    for record in records:
                        pass_id = record.get('通行标识ID')
                        check_id = record.get('核查通行标识')
                        pass_id_valid = pass_id is not None and str(pass_id).strip() != ''
                        check_id_valid = check_id is not None and str(check_id).strip() != ''
                        if pass_id_valid or check_id_valid:
                            valid_records.append(record)
                    
                    if len(valid_records) == 0:
                        logger.warning("没有找到待匹配的记录")
                        total_time = time.time() - start_time
                        debug_info['total_time'] = total_time
                        return {
                            "matched_count": 0, 
                            "unmatched_count": 0, 
                            "total": 0,
                            "pass_id_matched": 0,
                            "check_id_matched": 0,
                            "debug": debug_info
                        }
                    
                    # 创建临时表存储待匹配记录
                    temp_table_name = f"temp_match_{int(time.time())}"
                    create_temp_sql = f"""
                        CREATE TEMPORARY TABLE `{temp_table_name}` (
                            `通行标识ID` VARCHAR(255),
                            `核查通行标识` VARCHAR(255)
                        ) ENGINE=InnoDB
                    """
                    debug_info['create_temp_table_sql'] = create_temp_sql
                    cursor.execute(create_temp_sql)
                    
                    # 批量插入临时表
                    insert_sql = f"INSERT INTO `{temp_table_name}` (`通行标识ID`, `核查通行标识`) VALUES (%s, %s)"
                    insert_values = [(str(r.get('通行标识ID')), str(r.get('核查通行标识'))) for r in valid_records]
                    cursor.executemany(insert_sql, insert_values)
                    
                    # 更新主表：通行标识ID匹配的记录
                    update_pass_id_sql = f"""
                        UPDATE `{table_name}` AS t1
                        INNER JOIN `{temp_table_name}` AS t2 ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t2.`通行标识ID`
                        INNER JOIN `{cf_table}` AS t3 ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t3.`通行标识ID` COLLATE utf8mb4_general_ci
                        SET t1.`核查拆分` = '已拆'
                        WHERE t3.`通行标识ID` IS NOT NULL AND t3.`通行标识ID` != ''
                    """
                    debug_info['update_pass_id_sql'] = update_pass_id_sql
                    cursor.execute(update_pass_id_sql)
                    pass_id_matched = cursor.rowcount
                    
                    # 更新主表：核查通行标识匹配的记录（且通行标识ID未匹配的）
                    update_check_id_sql = f"""
                        UPDATE `{table_name}` AS t1
                        INNER JOIN `{temp_table_name}` AS t2 ON t1.`核查通行标识` COLLATE utf8mb4_general_ci = t2.`核查通行标识`
                        INNER JOIN `{cf_table}` AS t3 ON t1.`核查通行标识` COLLATE utf8mb4_general_ci = t3.`通行标识ID` COLLATE utf8mb4_general_ci
                        SET t1.`核查拆分` = '已拆'
                        WHERE t3.`通行标识ID` IS NOT NULL AND t3.`通行标识ID` != ''
                          AND (t1.`核查拆分` != '已拆' OR t1.`核查拆分` IS NULL)
                    """
                    debug_info['update_check_id_sql'] = update_check_id_sql
                    cursor.execute(update_check_id_sql)
                    check_id_matched = cursor.rowcount
                    
                    # 更新未匹配的记录为'未拆'
                    update_unmatched_sql = f"""
                        UPDATE `{table_name}` AS t1
                        INNER JOIN `{temp_table_name}` AS t2 ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t2.`通行标识ID` OR t1.`核查通行标识` COLLATE utf8mb4_general_ci = t2.`核查通行标识`
                        SET t1.`核查拆分` = '未拆'
                        WHERE t1.`核查拆分` != '已拆' OR t1.`核查拆分` IS NULL
                    """
                    debug_info['update_unmatched_sql'] = update_unmatched_sql
                    cursor.execute(update_unmatched_sql)
                    
                    # 删除临时表
                    cursor.execute(f"DROP TEMPORARY TABLE `{temp_table_name}`")
                    
                    matched_count = pass_id_matched + check_id_matched
                    total_count = len(valid_records)
                    
                else:
                    # 情况2：没有传入records参数，直接JOIN更新所有记录
                    debug_info['records_source'] = '数据库所有记录'
                    
                    # 第一步：更新通行标识ID匹配的记录
                    update_pass_id_sql = f"""
                        UPDATE `{table_name}` AS t1
                        LEFT JOIN `{cf_table}` AS t2 ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t2.`通行标识ID` COLLATE utf8mb4_general_ci
                        SET t1.`核查拆分` = '已拆'
                        WHERE t2.`通行标识ID` IS NOT NULL AND t2.`通行标识ID` != ''
                    """
                    debug_info['update_pass_id_sql'] = update_pass_id_sql
                    cursor.execute(update_pass_id_sql)
                    pass_id_matched = cursor.rowcount
                    
                    # 第二步：更新核查通行标识匹配的记录（且通行标识ID未匹配的）
                    update_check_id_sql = f"""
                        UPDATE `{table_name}` AS t1
                        LEFT JOIN `{cf_table}` AS t2 ON t1.`核查通行标识` COLLATE utf8mb4_general_ci = t2.`通行标识ID` COLLATE utf8mb4_general_ci
                        SET t1.`核查拆分` = '已拆'
                        WHERE t2.`通行标识ID` IS NOT NULL AND t2.`通行标识ID` != ''
                          AND (t1.`核查拆分` != '已拆' OR t1.`核查拆分` IS NULL)
                    """
                    debug_info['update_check_id_sql'] = update_check_id_sql
                    cursor.execute(update_check_id_sql)
                    check_id_matched = cursor.rowcount
                    
                    # 第三步：更新未匹配的记录为'未拆'
                    update_unmatched_sql = f"""
                        UPDATE `{table_name}` AS t1
                        LEFT JOIN `{cf_table}` AS t2_pass ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t2_pass.`通行标识ID` COLLATE utf8mb4_general_ci
                        LEFT JOIN `{cf_table}` AS t2_check ON t1.`核查通行标识` COLLATE utf8mb4_general_ci = t2_check.`通行标识ID` COLLATE utf8mb4_general_ci
                        SET t1.`核查拆分` = '未拆'
                        WHERE t2_pass.`通行标识ID` IS NULL 
                          AND t2_check.`通行标识ID` IS NULL
                          AND (t1.`通行标识ID` IS NOT NULL AND t1.`通行标识ID` != '' 
                               OR t1.`核查通行标识` IS NOT NULL AND t1.`核查通行标识` != '')
                    """
                    debug_info['update_unmatched_sql'] = update_unmatched_sql
                    cursor.execute(update_unmatched_sql)
                    
                    matched_count = pass_id_matched + check_id_matched
                    
                    # 查询总记录数
                    count_sql = f"""
                        SELECT COUNT(*) AS total FROM `{table_name}`
                        WHERE (`通行标识ID` IS NOT NULL AND `通行标识ID` != '') 
                           OR (`核查通行标识` IS NOT NULL AND `核查通行标识` != '')
                    """
                    debug_info['count_sql'] = count_sql
                    cursor.execute(count_sql)
                    total_count = cursor.fetchone()['total']
                
                conn.commit()
                
                total_time = time.time() - start_time
                debug_info['total_time'] = total_time
                debug_info['pass_id_matched'] = pass_id_matched
                debug_info['check_id_matched'] = check_id_matched
                debug_info['matched_count'] = matched_count
                debug_info['total_count'] = total_count
            
            return {
                "matched_count": matched_count, 
                "unmatched_count": total_count - matched_count, 
                "total": total_count,
                "pass_id_matched": pass_id_matched,
                "check_id_matched": check_id_matched,
                "debug": debug_info
            }
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"执行匹配失败: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return {
                "matched_count": 0, 
                "unmatched_count": 0, 
                "total": 0,
                "pass_id_matched": 0,
                "check_id_matched": 0,
                "debug": {"total_time": total_time, "error": str(e)}
            }
        finally:
            if conn:
                conn.close()
    
    def preview_match(self, table_name, records=None):
        """预览执行匹配将要执行的SQL语句（不实际执行）"""
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return {
                    "sqls": [],
                    "error": "无法获取数据库连接"
                }
            
            sqls = []
            cf_table = "202005-202311_cf_1215"
            
            # 1. 情况1：有传入records参数
            if records is not None:
                # 过滤掉无效记录（至少有一个ID不为空）
                valid_records = []
                for record in records:
                    pass_id = record.get('通行标识ID')
                    check_id = record.get('核查通行标识')
                    pass_id_valid = pass_id is not None and str(pass_id).strip() != ''
                    check_id_valid = check_id is not None and str(check_id).strip() != ''
                    if pass_id_valid or check_id_valid:
                        valid_records.append(record)
                
                if len(valid_records) > 0:
                    temp_table_name = f"temp_match_{int(time.time())}"
                    # 创建临时表SQL
                    create_temp_sql = f"""
                        CREATE TEMPORARY TABLE `{temp_table_name}` (
                            `通行标识ID` VARCHAR(255),
                            `核查通行标识` VARCHAR(255)
                        ) ENGINE=InnoDB
                    """
                    sqls.append({
                        "name": "创建临时表SQL",
                        "sql": create_temp_sql
                    })
                    
                    # 更新通行标识ID匹配的记录
                    update_pass_id_sql = f"""
                        UPDATE `{table_name}` AS t1
                        INNER JOIN `{temp_table_name}` AS t2 ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t2.`通行标识ID`
                        INNER JOIN `{cf_table}` AS t3 ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t3.`通行标识ID` COLLATE utf8mb4_general_ci
                        SET t1.`核查拆分` = '已拆'
                        WHERE t3.`通行标识ID` IS NOT NULL AND t3.`通行标识ID` != ''
                    """
                    sqls.append({
                        "name": "按通行标识ID更新SQL",
                        "sql": update_pass_id_sql
                    })
                    
                    # 更新核查通行标识匹配的记录
                    update_check_id_sql = f"""
                        UPDATE `{table_name}` AS t1
                        INNER JOIN `{temp_table_name}` AS t2 ON t1.`核查通行标识` COLLATE utf8mb4_general_ci = t2.`核查通行标识`
                        INNER JOIN `{cf_table}` AS t3 ON t1.`核查通行标识` COLLATE utf8mb4_general_ci = t3.`通行标识ID` COLLATE utf8mb4_general_ci
                        SET t1.`核查拆分` = '已拆'
                        WHERE t3.`通行标识ID` IS NOT NULL AND t3.`通行标识ID` != ''
                          AND (t1.`核查拆分` != '已拆' OR t1.`核查拆分` IS NULL)
                    """
                    sqls.append({
                        "name": "按核查通行标识更新SQL",
                        "sql": update_check_id_sql
                    })
                    
                    # 更新未匹配的记录
                    update_unmatched_sql = f"""
                        UPDATE `{table_name}` AS t1
                        INNER JOIN `{temp_table_name}` AS t2 ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t2.`通行标识ID` OR t1.`核查通行标识` COLLATE utf8mb4_general_ci = t2.`核查通行标识`
                        SET t1.`核查拆分` = '未拆'
                        WHERE t1.`核查拆分` != '已拆' OR t1.`核查拆分` IS NULL
                    """
                    sqls.append({
                        "name": "更新未匹配记录SQL",
                        "sql": update_unmatched_sql
                    })
                    
                    # 删除临时表
                    sqls.append({
                        "name": "删除临时表SQL",
                        "sql": f"DROP TEMPORARY TABLE `{temp_table_name}`"
                    })
            
            else:
                # 情况2：没有传入records参数，直接JOIN
                # 更新通行标识ID匹配的记录
                update_pass_id_sql = f"""
                    UPDATE `{table_name}` AS t1
                    LEFT JOIN `{cf_table}` AS t2 ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t2.`通行标识ID` COLLATE utf8mb4_general_ci
                    SET t1.`核查拆分` = '已拆'
                    WHERE t2.`通行标识ID` IS NOT NULL AND t2.`通行标识ID` != ''
                """
                sqls.append({
                    "name": "按通行标识ID更新SQL",
                    "sql": update_pass_id_sql
                })
                
                # 更新核查通行标识匹配的记录
                update_check_id_sql = f"""
                    UPDATE `{table_name}` AS t1
                    LEFT JOIN `{cf_table}` AS t2 ON t1.`核查通行标识` COLLATE utf8mb4_general_ci = t2.`通行标识ID` COLLATE utf8mb4_general_ci
                    SET t1.`核查拆分` = '已拆'
                    WHERE t2.`通行标识ID` IS NOT NULL AND t2.`通行标识ID` != ''
                      AND (t1.`核查拆分` != '已拆' OR t1.`核查拆分` IS NULL)
                """
                sqls.append({
                    "name": "按核查通行标识更新SQL",
                    "sql": update_check_id_sql
                })
                
                # 更新未匹配的记录
                update_unmatched_sql = f"""
                    UPDATE `{table_name}` AS t1
                    LEFT JOIN `{cf_table}` AS t2_pass ON t1.`通行标识ID` COLLATE utf8mb4_general_ci = t2_pass.`通行标识ID` COLLATE utf8mb4_general_ci
                    LEFT JOIN `{cf_table}` AS t2_check ON t1.`核查通行标识` COLLATE utf8mb4_general_ci = t2_check.`通行标识ID` COLLATE utf8mb4_general_ci
                    SET t1.`核查拆分` = '未拆'
                    WHERE t2_pass.`通行标识ID` IS NULL 
                      AND t2_check.`通行标识ID` IS NULL
                      AND (t1.`通行标识ID` IS NOT NULL AND t1.`通行标识ID` != '' 
                           OR t1.`核查通行标识` IS NOT NULL AND t1.`核查通行标识` != '')
                """
                sqls.append({
                    "name": "更新未匹配记录SQL",
                    "sql": update_unmatched_sql
                })
                
                # 查询总记录数
                count_sql = f"""
                    SELECT COUNT(*) AS total FROM `{table_name}`
                    WHERE (`通行标识ID` IS NOT NULL AND `通行标识ID` != '') 
                       OR (`核查通行标识` IS NOT NULL AND `核查通行标识` != '')
                """
                sqls.append({
                    "name": "查询总记录数SQL",
                    "sql": count_sql
                })
            
            return {
                "sqls": sqls
            }
        except Exception as e:
            logger.error(f"预览SQL失败: {e}", exc_info=True)
            return {
                "sqls": [],
                "error": str(e)
            }
        finally:
            if conn:
                conn.close()
    
    def update_table_data(self, table_name, row_id, data):
        """更新表数据
        
        Args:
            table_name: 表名
            row_id: 行标识（通行标识ID）
            data: 要更新的数据字典
        """
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return False
            
            set_clauses = []
            params = []
            
            for key, value in data.items():
                set_clauses.append(f"`{key}` = %s")
                params.append(value)
            
            params.append(row_id)
            
            update_sql = f"UPDATE `{table_name}` SET {','.join(set_clauses)} WHERE `通行标识ID` = %s"
            
            with conn.cursor() as cursor:
                cursor.execute(update_sql, params)
                conn.commit()
                return cursor.rowcount > 0
        except pymysql.err.OperationalError as e:
            error_code = e.args[0] if e.args else 0
            error_msg = str(e)
            
            if error_code == 1114:
                logger.error(f"[表空间不足] 无法更新 {table_name}: {error_msg}")
                raise Exception(f"数据库表 '{table_name}' 空间不足，请联系管理员清理磁盘空间")
            elif error_code in [1040, 1041]:
                logger.error(f"[连接问题] 无法更新 {table_name}: {error_msg}")
                raise Exception("数据库连接异常，请稍后重试")
            elif error_code == 1146:
                logger.error(f"[表不存在] 表 {table_name} 不存在: {error_msg}")
                raise Exception(f"数据表 '{table_name}' 不存在，请检查配置")
            else:
                logger.error(f"[SQL错误-{error_code}] 更新 {table_name} 失败: {error_msg}", exc_info=True)
                raise Exception(f"数据库操作失败 (错误码: {error_code}): {error_msg}")
                
        except Exception as e:
            logger.error(f"更新表数据失败: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def split_data(self, data):
        return data
    
    def match_data(self, data1, data2):
        return []
