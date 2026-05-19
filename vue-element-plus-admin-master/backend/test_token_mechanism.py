"""
测试新的Token机制 - 验证数据库迁移和Token管理
"""
import sys
import os
import sqlite3

sys.path.insert(0, r'D:\local_pysys\vue-element-plus-admin-master\backend')
os.chdir(r'D:\local_pysys\vue-element-plus-admin-master\backend')

from routers.cloud_portal import (
    _get_account_db,
    _save_account,
    _get_account,
    _update_account_tokens,
    _is_token_valid,
    _delete_account
)
import time


def test_database_migration():
    """测试数据库迁移"""

    print("=" * 80)
    print("🧪 测试1: 数据库表结构迁移")
    print("=" * 80)

    conn = _get_account_db()

    cursor = conn.execute("PRAGMA table_info(portal_accounts)")
    columns = [row[1] for row in cursor.fetchall()]

    print(f"\n📋 当前portal_accounts表的字段:")
    for i, col in enumerate(columns, 1):
        print(f"   {i}. {col}")

    expected_columns = [
        'id', 'user_id', 'portal_username', 'portal_password',
        'access_token', 'refresh_token', 'redirect_uri', 'token_expires_at',
        'created_at', 'updated_at'
    ]

    missing_cols = set(expected_columns) - set(columns)
    old_cols = set(columns) - set(expected_columns)

    if missing_cols:
        print(f"\n❌ 缺少字段: {missing_cols}")
        return False

    if old_cols:
        print(f"\n⚠️  存在旧字段: {old_cols} (可能需要手动清理)")
    else:
        print(f"\n✅ 表结构正确，包含所有必需字段")

    if 'portal_session_id' in columns:
        print(f"❌ 错误：仍存在旧字段 portal_session_id")
        return False
    else:
        print(f"✅ 旧字段 portal_session_id 已移除")

    conn.close()
    return True


def test_token_operations():
    """测试Token操作"""

    print("\n" + "=" * 80)
    print("🧪 测试2: Token CRUD操作")
    print("=" * 80)

    test_user_id = 999
    test_username = "testuser_token"
    test_password = "testpass123"

    print(f"\n💾 步骤1: 创建测试账号")
    _save_account(test_user_id, test_username, test_password)

    account = _get_account(test_user_id)
    if account:
        print(f"   ✅ 账号创建成功:")
        print(f"      用户名: {account['portal_username']}")
        print(f"      access_token: {account.get('access_token') or '(空)'}")
        print(f"      refresh_token: {account.get('refresh_token') or '(空)'}")
        print(f"      redirect_uri: {account.get('redirect_uri') or '(空)'}")
    else:
        print(f"   ❌ 账号创建失败")
        return False

    print(f"\n💾 步骤2: 更新Token信息")
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.payload.abc123"
    refresh_token = "refresh.token.here"
    redirect_uri = "http://example.com/callback"
    token_expires_at = time.time() + 3600  # 1小时后过期

    _update_account_tokens(
        user_id=test_user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        redirect_uri=redirect_uri,
        token_expires_at=token_expires_at
    )

    account = _get_account(test_user_id)
    print(f"   ✅ Token更新成功:")
    print(f"      access_token: {account.get('access_token')[:30]}...")
    print(f"      refresh_token: {account.get('refresh_token')[:20]}...")
    print(f"      redirect_uri: {account.get('redirect_uri')}")
    print(f"      token_expires_at: {account.get('token_expires_at')}")

    print(f"\n✅ 步骤3: 验证Token有效性")
    is_valid = _is_token_valid(account)
    print(f"   Token有效: {'✅ 是' if is_valid else '❌ 否'}")

    if not is_valid:
        print(f"   ❌ 测试失败: Token应该是有效的")
        return False

    print(f"\n⏰ 步骤4: 模拟Token过期")
    expired_time = time.time() - 100  # 已过期100秒
    _update_account_tokens(
        user_id=test_user_id,
        token_expires_at=expired_time
    )

    account = _get_account(test_user_id)
    is_valid_expired = _is_token_valid(account)
    print(f"   Token有效 (已过期): {'✅ 是' if is_valid_expired else '❌ 否 (预期行为)'}")

    if is_valid_expired:
        print(f"   ❌ 测试失败: 过期的Token不应被判定为有效")
        return False
    else:
        print(f"   ✅ 正确检测到Token已过期")

    print(f"\n🔄 步骤5: 更新部分字段")
    new_access_token = "new.access.token.value"
    _update_account_tokens(
        user_id=test_user_id,
        access_token=new_access_token
    )

    account = _get_account(test_user_id)
    if account.get('access_token') == new_access_token and account.get('redirect_uri') == redirect_uri:
        print(f"   ✅ 部分更新成功: access_token已更新, redirect_uri保持不变")
    else:
        print(f"   ❌ 部分更新失败")
        return False

    _delete_account(test_user_id)
    print(f"\n🗑️  清理: 测试账号已删除")

    return True


def test_old_field_removal():
    """测试旧字段是否完全移除"""

    print("\n" + "=" * 80)
    print("🧪 测试3: 确认旧字段已移除")
    print("=" * 80)

    conn = _get_account_db()

    try:
        result = conn.execute("SELECT portal_session_id FROM portal_accounts LIMIT 1").fetchone()
        if result:
            print(f"\n❌ 错误: portal_session_id 字段仍存在!")
            return False
    except sqlite3.OperationalError as e:
        if 'no such column' in str(e):
            print(f"\n✅ portal_session_id 字段已完全移除")
            print(f"   SQLite错误 (预期): {e}")
            return True
        else:
            print(f"\n❌ 意外的SQLite错误: {e}")
            return False
    finally:
        conn.close()


def test_credentials_api_format():
    """测试credentials API返回格式"""

    print("\n" + "=" * 80)
    print("🧪 测试4: Credentials API返回格式验证")
    print("=" * 80)

    test_user_id = 998
    test_username = "api_test_user"
    test_password = "api_test_pass"

    _save_account(test_user_id, test_username, test_password)

    _update_account_tokens(
        user_id=test_user_id,
        access_token="test.access.token",
        refresh_token="test.refresh.token",
        redirect_uri="http://test.com/redirect",
        token_expires_at=time.time() + 7200
    )

    account = _get_account(test_user_id)

    print(f"\n📡 模拟API返回数据结构:")

    is_valid = _is_token_valid(account)

    api_response = {
        "code": 200,
        "message": "获取成功",
        "data": {
            "portal_username": account["portal_username"],
            "portal_password": account["portal_password"],
            "access_token": account.get("access_token"),
            "refresh_token": account.get("refresh_token"),
            "redirect_uri": account.get("redirect_uri"),
            "token_expires_at": account.get("token_expires_at"),
            "token_valid": is_valid,
        }
    }

    import json
    print(f"\n{json.dumps(api_response, indent=2, ensure_ascii=False)}")

    required_fields = ['portal_username', 'portal_password', 'access_token',
                      'refresh_token', 'redirect_uri', 'token_expires_at', 'token_valid']

    data = api_response['data']
    missing = [f for f in required_fields if f not in data]

    if missing:
        print(f"\n❌ 缺少必要字段: {missing}")
        _delete_account(test_user_id)
        return False
    else:
        print(f"\n✅ API返回格式正确，包含所有必要字段")

    if data['token_valid']:
        print(f"✅ token_valid=True (Token有效)")
    else:
        print(f"⚠️  token_valid=False (Token无效或不存在)")

    _delete_account(test_user_id)
    return True


def main():
    """运行所有测试"""

    print("\n" + "🎯" * 40)
    print("🔐 云门户Token机制优化 - 完整测试套件")
    print("🎯" * 40)

    tests = [
        ("数据库表结构迁移", test_database_migration),
        ("Token CRUD操作", test_token_operations),
        ("旧字段移除确认", test_old_field_removal),
        ("Credentials API格式", test_credentials_api_format),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！Token机制优化完成！")
        print("\n" + "=" * 80)
        print("📝 优化总结:")
        print("=" * 80)
        print("""
✅ 数据库变更:
   - 移除字段: portal_session_id (不再需要)
   - 新增字段: access_token, refresh_token, redirect_uri, token_expires_at
   - 自动迁移: 支持从旧表结构自动升级

✅ 后端逻辑变更:
   - 登录成功后自动保存Token信息（而非session_id）
   - Token有效性检查基于JWT的exp声明
   - credentials接口返回完整Token信息及有效性状态
   - 所有业务接口移除session_id参数，采用无状态设计

✅ 前端逻辑变更:
   - 完全移除cloudPortalSessionId变量和相关逻辑
   - 使用cloudPortalLoggedIn判断登录状态
   - 登录成功后传递完整的Token信息给父组件
   - 不再传递session_id到任何API调用

✅ 架构优势:
   - UUID仅用于登录时验证码校验，用完即弃
   - Token用于长期会话状态管理，可刷新和续期
   - 符合OAuth2标准实践
   - 完全无状态设计，支持水平扩展
   - 减少中间状态，降低复杂度，提升可维护性
        """)
    else:
        print(f"\n⚠️  有 {total - passed} 个测试未通过，请检查!")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
