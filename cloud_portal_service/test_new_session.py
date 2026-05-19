"""
测试修改后的Session机制 - 验证使用云门户UUID作为Session_ID
"""
import sys
import os

sys.path.insert(0, r'D:\local_pysys\cloud_portal_service')
os.chdir(r'D:\local_pysys\cloud_portal_service')

from api_server import store_captcha, validate_captcha, _captcha_store
import time

def test_new_session_mechanism():
    """测试新的Session机制"""

    print("=" * 80)
    print("🧪 测试新的Session机制 (使用云门户UUID作为Session_ID)")
    print("=" * 80)

    cloud_portal_uuid = "1762df44dceede1d3f9af2561131815f"

    print(f"\n📥 模拟云门户口令返回:")
    print(f"   UUID: {cloud_portal_uuid}")

    print(f"\n💾 步骤1: 存储验证码记录")
    print(f"   调用: store_captcha('{cloud_portal_uuid}', '{cloud_portal_uuid}')")
    store_captcha(cloud_portal_uuid, cloud_portal_uuid)

    print(f"\n   当前_captcha_store内容:")
    for key, timestamp in _captcha_store.items():
        print(f"     '{key}' → {timestamp}")

    print(f"\n✅ 步骤2: 验证验证码 (使用相同的UUID作为session_id和uuid)")
    print(f"   调用: validate_captcha('{cloud_portal_uuid}', '{cloud_portal_uuid}')")

    valid, error = validate_captcha(cloud_portal_uuid, cloud_portal_uuid)

    if valid:
        print(f"   结果: ✅ 验证通过!")
        print(f"   错误信息: 无")
    else:
        print(f"   结果: ❌ 验证失败!")
        print(f"   错误信息: {error}")

    print(f"\n📊 验证后_captcha_store内容 (应该为空，因为pop了):")
    if len(_captcha_store) == 0:
        print("   ✅ 已清空 (正常行为)")
    else:
        for key, timestamp in _captcha_store.items():
            print(f"     '{key}' → {timestamp}")

    print("\n" + "=" * 80)
    print("🔄 测试场景2: 重复验证同一验证码 (应失败)")
    print("=" * 80)

    print(f"\n💾 重新存储验证码")
    store_captcha(cloud_portal_uuid, cloud_portal_uuid)

    print(f"\n✅ 第一次验证:")
    valid1, error1 = validate_captcha(cloud_portal_uuid, cloud_portal_uuid)
    print(f"   结果: {'✅ 通过' if valid1 else '❌ 失败'} - {error1 or '无错误'}")

    print(f"\n❌ 第二次验证 (同一验证码):")
    valid2, error2 = validate_captcha(cloud_portal_uuid, cloud_portal_uuid)
    print(f"   结果: {'✅ 通过' if valid2 else '❌ 失败'} - {error2 or '无错误'}")

    if not valid2 and "不存在或已使用" in error2:
        print(f"   ✅ 正确! 验证码已被消费，不能重复使用")

    print("\n" + "=" * 80)
    print("⏰ 测试场景3: 验证码过期检测")
    print("=" * 80)

    test_uuid_expired = "test-uuid-expired-12345"
    from session_manager import Limits

    print(f"\n💾 存储验证码并模拟过期")
    store_captcha(test_uuid_expired, test_uuid_expired)

    print(f"   手动设置过期时间戳...")
    import session_manager as sm
    expired_key = f"{test_uuid_expired}:{test_uuid_expired}"
    if expired_key in _captcha_store:
        _captcha_store[expired_key] = time.time() - (Limits.CAPTCHA_TTL + 100)  # 设置为过期
        print(f"   时间戳设置为: {_captcha_store[expired_key]} (当前时间: {time.time()})")
        print(f"   过期时间: {Limits.CAPTCHA_TTL}秒")

    print(f"\n⏰ 验证过期的验证码:")
    valid3, error3 = validate_captcha(test_uuid_expired, test_uuid_expired)
    print(f"   结果: {'✅ 通过' if valid3 else '❌ 失败'}")
    print(f"   错误信息: {error3}")

    if not valid3 and "已过期" in error3:
        print(f"   ✅ 正确! 检测到验证码已过期")

    print("\n" + "=" * 80)
    print("🎯 测试总结")
    print("=" * 80)
    print("""
    新机制工作原理:
    ┌─────────────────────────────────────────────┐
    │ 1. 前端调用 GET /api/portal/captcha         │
    │    ↓                                        │
    │ 2. GUI服务调用云门户口令获取验证码          │
    │    ↓ 返回 {img, uuid: "abc-123"}           │
    │    ↓                                        │
    │ 3. GUI使用uuid作为session_id               │
    │    store_captcha("abc-123", "abc-123")      │
    │    ↓                                        │
    │ 4. 返回给前端:                             │
    │    {session_id: "abc-123",                 │
    │     img: "...",                            │
    │     uuid: "abc-123"}                      │
    │    ↓                                        │
    │ 5. 前端调用登录时:                         │
    │    POST /api/portal/login                   │
    │    {session_id: "abc-123",                 │
    │     uuid: "abc-123",                       │
    │     captcha: "2163", ...}                  │
    │    ↓                                        │
    │ 6. GUI验证:                                │
    │    validate_captcha("abc-123", "abc-123")  │
    │    查找 "abc-123:abc-123" → 找到! ✅      │
    └─────────────────────────────────────────────┘

    优势:
    ✅ Session_ID来自云门户口令，权威可靠
    ✅ 不依赖GUI服务自建UUID，避免重启丢失问题
    ✅ Session与验证码一一对应，逻辑更清晰
    ✅ 减少中间状态管理复杂度
    """)

if __name__ == "__main__":
    test_new_session_mechanism()
