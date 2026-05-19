import pymysql
import base64
import traceback

def test_connection():
    """Test database connection"""
    try:
        conn = pymysql.connect(
            host='172.32.48.238',
            port=3306,
            user='root',
            password='9a1d4e4ae72d2eaa',
            database='check_data',
            connect_timeout=5
        )
        print("[OK] Database connection successful")
        return conn
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        return None

def test_simple_update(conn, test_id):
    """Test 1: Simple text field update"""
    print("\n" + "="*60)
    print("TEST 1: Simple text field update (备注)")
    print("="*60)
    
    try:
        cursor = conn.cursor()
        
        # Update remark field
        sql = "UPDATE `2025-12_yc` SET `备注` = %s WHERE `通行标识ID` = %s"
        params = ('Diagnostic Test - ' + __import__('datetime').datetime.now().strftime('%H:%M:%S'), test_id)
        
        print(f"SQL: UPDATE ... SET `备注` = '{params[0]}' WHERE ...")
        cursor.execute(sql, params)
        affected = cursor.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"[OK] Success! affected_rows = {affected}")
            
            # Verify the update
            cursor.execute("SELECT `备注` FROM `2025-12_yc` WHERE `通行标识ID` = %s", (test_id,))
            result = cursor.fetchone()
            print(f"     Verified: 备注 = '{result[0]}'")
            return True
        else:
            print(f"[WARN] No rows updated (affected_rows = 0)")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def test_small_image_update(conn, test_id):
    """Test 2: Small image update (10KB)"""
    print("\n" + "="*60)
    print("TEST 2: Small image update (10KB binary data)")
    print("="*60)
    
    try:
        cursor = conn.cursor()
        
        # Create small test image (10KB of random-looking data)
        small_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==') * 100
        
        print(f"Data size: {len(small_data)} bytes ({len(small_data)/1024:.2f} KB)")
        
        sql = "UPDATE `2025-12_yc` SET `查核资料1` = %s WHERE `通行标识ID` = %s"
        params = (small_data, test_id)
        
        print("Executing UPDATE with binary data...")
        cursor.execute(sql, params)
        affected = cursor.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"[OK] Success! affected_rows = {affected}")
            
            # Verify
            cursor.execute("SELECT LENGTH(`查核资料1`) FROM `2025-12_yc` WHERE `通行标识ID` = %s", (test_id,))
            result = cursor.fetchone()
            print(f"     Verified: Image size = {result[0]} bytes")
            return True
        else:
            print(f"[WARN] No rows updated")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def test_large_image_update(conn, test_id):
    """Test 3: Large image update (~500KB)"""
    print("\n" + "="*60)
    print("TEST 3: Large image update (~500KB binary data)")
    print("="*60)
    
    try:
        cursor = conn.cursor()
        
        # Create larger test data (simulate real image)
        large_data = b'\x00' * (512 * 1024)  # 512KB
        
        print(f"Data size: {len(large_data)} bytes ({len(large_data)/1024:.2f} KB)")
        
        sql = "UPDATE `2025-12_yc` SET `查核资料1` = %s WHERE `通行标识ID` = %s"
        params = (large_data, test_id)
        
        print("Executing UPDATE with large binary data...")
        cursor.execute(sql, params)
        affected = cursor.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"[OK] Success! affected_rows = {affected}")
            
            # Verify
            cursor.execute("SELECT LENGTH(`查核资料1`) FROM `2025-12_yc` WHERE `通行标识ID` = %s", (test_id,))
            result = cursor.fetchone()
            print(f"     Verified: Image size = {result[0]} bytes")
            return True
        else:
            print(f"[WARN] No rows updated")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def test_multi_field_update(conn, test_id):
    """Test 4: Multi-field update (simulating actual request)"""
    print("\n" + "="*60)
    print("TEST 4: Multi-field update (simulating /api/split-match/update/)")
    print("="*60)
    
    try:
        cursor = conn.cursor()
        
        # Simulate the actual data from frontend request
        update_data = {
            '通行标识ID': test_id,
            '车牌号码': '京BCG030_1',
            '车牌': '京BCG030',
            '核查通行标识': None,
            '复核情况': '待删除',
            '备注': '摩托车',
            '特情': None,
            '核查拆分': '未拆',
            '门架通行时间': '2025-12-11 13:41:31',
            '入口时间': '2025-12-11 09:00:18',
            '收费车型': 1,
            '车种': 0,
            '通行介质': 2,
            '门架应收金额': 13870,
            '门架交易金额': 13870,
            '收费入口名称': '湖北隆中站',
            '通行日期': '2025-12'
        }
        
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            if key != '通行标识ID':
                set_clauses.append(f"`{key}` = %s")
                params.append(value)
                print(f"  - {key}: {value}")
        
        params.append(test_id)
        
        update_sql = f"UPDATE `2025-12_yc` SET {','.join(set_clauses)} WHERE `通行标识ID` = %s"
        
        print(f"\nSQL Preview:")
        print(f"UPDATE `2025-12_yc` SET {len(set_clauses)} fields WHERE `通行标识ID` = ?")
        print(f"Parameters count: {len(params)}")
        
        cursor.execute(update_sql, params)
        affected = cursor.rowcount
        conn.commit()
        
        if affected > 0:
            print(f"\n[OK] Success! affected_rows = {affected}")
            return True
        else:
            print(f"\n[WARN] No rows updated")
            
            # Check if record exists
            cursor.execute("SELECT COUNT(*) FROM `2025-12_yc` WHERE `通行标识ID` = %s", (test_id,))
            count = cursor.fetchone()[0]
            print(f"     Record exists check: COUNT(*) = {count}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def check_table_status(conn):
    """Check table status and space info"""
    print("\n" + "="*60)
    print("TABLE STATUS CHECK")
    print("="*60)
    
    try:
        cursor = conn.cursor()
        
        # Get table status
        cursor.execute("""
            SELECT 
                table_name,
                engine,
                row_format,
                table_rows,
                avg_row_length,
                data_length,
                max_data_length,
                index_length,
                data_free,
                auto_increment,
                create_time,
                update_time,
                check_time
            FROM information_schema.tables 
            WHERE table_schema = 'check_data' AND table_name = '2025-12_yc'
        """)
        
        row = cursor.fetchone()
        if row:
            print(f"Table Name:       {row[0]}")
            print(f"Engine:           {row[1]}")
            print(f"Row Format:       {row[2]}")
            print(f"Rows:             {row[3]:,}")
            print(f"Avg Row Length:   {row[4]:,} bytes")
            print(f"Data Length:      {row[5]:,} bytes ({row[5]/1024/1024:.2f} MB)")
            print(f"Max Data Length:  {row[6]:,} bytes ({row[6]/1024/1024:.2f} MB)" if row[6] else "Max Data Length:  UNLIMITED")
            print(f"Index Length:     {row[7]:,} bytes")
            print(f"Data Free:        {row[8]:,} bytes ({row[8]/1024/1024:.2f} MB)")
            print(f"Auto Increment:   {row[9]}")
            print(f"Created:          {row[10]}")
            print(f"Last Updated:     {row[11]}")
            print(f"Last Checked:     {row[12]}")
        
        # Check for errors or warnings
        cursor.execute("CHECK TABLE `2025-12_yc`")
        check_result = cursor.fetchone()
        print(f"\nTable Check Result: {check_result[2]} - {check_result[3]}")
        
        cursor.close()
        
    except Exception as e:
        print(f"[ERROR] Cannot get table status: {e}")

def main():
    print("="*60)
    print(" DATABASE UPDATE DIAGNOSTIC TEST")
    print(" Date:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*60)
    
    test_id = '020000440101920051312120251211090018'
    
    # Step 1: Connect to database
    conn = test_connection()
    if not conn:
        print("\n[FATAL] Cannot proceed without database connection")
        return
    
    # Step 2: Check table status
    check_table_status(conn)
    
    # Step 3: Run tests
    results = {}
    
    results['simple'] = test_simple_update(conn, test_id)
    results['small_image'] = test_small_image_update(conn, test_id)
    results['large_image'] = test_large_image_update(conn, test_id)
    results['multi_field'] = test_multi_field_update(conn, test_id)
    
    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    all_passed = all(results.values())
    print("\n" + ("="*60))
    if all_passed:
        print(" ALL TESTS PASSED!")
        print(" The database is working correctly.")
    else:
        print(" SOME TESTS FAILED!")
        print(" See above for detailed error information.")
    print("="*60)
    
    conn.close()

if __name__ == '__main__':
    main()
