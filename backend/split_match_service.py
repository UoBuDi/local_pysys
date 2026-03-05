import pymysql
import logging

logger = logging.getLogger(__name__)


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
        try:
            conn = self._get_db_connection()
            if not conn:
                return {"list": [], "total": 0}
            
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
                cursor.execute(count_sql, params)
                total_result = cursor.fetchone()
                total = total_result['total'] if total_result else 0
                
                offset = (page - 1) * page_size
                select_sql = f"SELECT * FROM `{table_name}` WHERE {where_clause} LIMIT %s OFFSET %s"
                select_params = params + [page_size, offset]
                cursor.execute(select_sql, select_params)
                data = cursor.fetchall()
            
            return {"list": data, "total": total}
        except Exception as e:
            logger.error(f"获取表数据失败: {e}", exc_info=True)
            return {"list": [], "total": 0}
        finally:
            if conn:
                conn.close()
    
    def execute_match(self, table_name):
        """执行拆分匹配，根据通行标识ID进行匹配并更新备注字段"""
        conn = None
        try:
            conn = self._get_db_connection()
            if not conn:
                return {"matched": 0, "updated": 0}
            
            matched_count = 0
            updated_count = 0
            
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = f"SELECT `通行标识ID` FROM `{table_name}` WHERE `通行标识ID` IS NOT NULL"
                cursor.execute(query)
                all_pass_ids = [row['通行标识ID'] for row in cursor.fetchall()]
                
                pass_id_counts = {}
                for pass_id in all_pass_ids:
                    if pass_id:
                        pass_id_counts[pass_id] = pass_id_counts.get(pass_id, 0) + 1
                
                matched_pass_ids = [pid for pid, count in pass_id_counts.items() if count > 1]
                matched_count = len(matched_pass_ids)
                
                if matched_pass_ids:
                    update_query = f"UPDATE `{table_name}` SET `备注` = '重复' WHERE `通行标识ID` IN ({','.join(['%s'] * len(matched_pass_ids))})"
                    cursor.execute(update_query, matched_pass_ids)
                    updated_count = cursor.rowcount
                    conn.commit()
            
            return {"matched": matched_count, "updated": updated_count}
        except Exception as e:
            logger.error(f"执行匹配失败: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return {"matched": 0, "updated": 0}
        finally:
            if conn:
                conn.close()
    
    def update_table_data(self, table_name, row_id, data):
        """更新表数据"""
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
            
            update_sql = f"UPDATE `{table_name}` SET {','.join(set_clauses)} WHERE `id` = %s"
            
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
        return 