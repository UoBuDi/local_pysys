import pymysql
import logging
import time

logger = logging.getLogger(__name__)


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
                select_sql = f"SELECT * FROM `{table_name}` WHERE {where_clause} LIMIT %s OFFSET %s"
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
                    "select_duration": select_duration
                }
            
            return {"data": data, "columns": columns, "total": total, "debug": debug_info}
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"获取表数据失败: {e}", exc_info=True)
            return {"data": [], "columns": [], "total": 0, "debug": {"total_time": total_time}}
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
        except Exception as e:
            logger.error(f"更新表数据失败: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def split_data(self, data):
        return data
    
    def match_data(self, data1, data2):
        return []
