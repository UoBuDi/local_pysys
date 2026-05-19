"""
验证码OCR识别测试脚本 - 测试HTTP响应中的base64数据
"""
import sys
import os
import base64
import time

sys.path.insert(0, r'D:\local_pysys\vue-element-plus-admin-master\backend')
os.chdir(r'D:\local_pysys\vue-element-plus-admin-master\backend')

from captcha_ocr import captcha_ocr, recognize_captcha, is_ocr_available

def test_captcha_recognition():
    """测试验证码识别"""

    base64_data = "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"

    print("=" * 80)
    print("🔍 验证码 OCR 识别测试")
    print("=" * 80)

    print(f"\n📊 输入数据信息:")
    print(f"   Base64长度: {len(base64_data)} 字符")
    print(f"   前20字符: {base64_data[:20]}...")
    print(f"   是否包含data:image前缀: {base64_data.startswith('data:image')}")

    try:
        image_data = base64.b64decode(base64_data)
        print(f"   解码后大小: {len(image_data)} 字节 ({len(image_data)/1024:.2f} KB)")
        print(f"   图片格式标识: {image_data[:10]}")
    except Exception as e:
        print(f"   ❌ Base64解码失败: {e}")
        return

    print(f"\n🤖 OCR引擎状态:")
    print(f"   OCR可用性: {'✅ 可用' if is_ocr_available() else '❌ 不可用'}")

    if not is_ocr_available():
        print("\n❌ OCR引擎未初始化，无法进行测试")
        return

    print(f"\n🧪 开始识别测试...")

    for attempt in range(3):
        print(f"\n--- 第 {attempt + 1} 次识别 ---")

        start_time = time.time()

        result = captcha_ocr.recognize(
            base64_data,
            preprocess=True,
            expected_length=4
        )

        elapsed = time.time() - start_time

        print(f"⏱️  耗时: {elapsed:.3f}s")
        print(f"✅ 成功: {result['success']}")
        print(f"📝 识别结果: {result.get('text', 'N/A')}")
        print(f"❌ 错误信息: {result.get('error', '无')}")

        if result['success']:
            print(f"\n🎉 识别成功! 验证码: {result['text']}")
        else:
            print(f"\n⚠️  识别失败")

    print(f"\n📈 OCR统计信息:")
    stats = captcha_ocr.get_stats()
    print(f"   总识别次数: {stats['total']}")
    print(f"   成功次数: {stats['success']}")
    print(f"   失败次数: {stats['failed']}")
    print(f"   成功率: {stats['success_rate']*100:.1f}%")
    print(f"   平均耗时: {stats['avg_time']:.3f}s")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_captcha_recognition()
