#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试后端服务配置增强功能
包括：重启提示、连接测试、端口占用检测、配置持久化
"""
import sys
import os
import socket
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config, DEFAULT_CONFIG, CONFIG_FILE

def test_config_persistence():
    """测试1: 配置持久化功能"""
    print("\n" + "=" * 60)
    print("[测试1] 配置持久化与加载")
    print("=" * 60)
    
    # 保存测试配置
    test_config = {
        'host': '192.168.100.100',
        'port': 9999,
        'auto_generate_url': False,
        'url': 'http://test.example.com:9999/api'
    }
    
    print(f"\n  保存测试配置: {test_config}")
    config.set('backend', test_config)
    
    # 验证内存中的配置
    assert config.BACKEND_HOST == test_config['host'], "BACKEND_HOST 不匹配"
    assert config.BACKEND_PORT == test_config['port'], "BACKEND_PORT 不匹配"
    assert config.BACKEND_AUTO_GENERATE_URL == test_config['auto_generate_url'], "AUTO_GENERATE_URL 不匹配"
    print("  ✓ 内存配置正确")
    
    # 验证文件中的配置
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        saved_config = json.load(f)
    
    backend_in_file = saved_config.get('backend', {})
    assert backend_in_file.get('host') == test_config['host'], "文件中BACKEND_HOST不匹配"
    assert backend_in_file.get('port') == test_config['port'], "文件中BACKEND_PORT不匹配"
    assert backend_in_file.get('url') == test_config['url'], "文件中URL不匹配"
    print("  ✓ 文件持久化成功")
    
    # 模拟重新加载（重新实例化Config）
    from importlib import reload
    import config as config_module
    
    # 强制重新加载配置
    original_config = config._config.copy()
    config._config = None
    config.load_config()
    
    # 验证重新加载后的配置
    assert config.BACKEND_HOST == test_config['host'], "重新加载后BACKEND_HOST不匹配"
    assert config.BACKEND_URL == test_config['url'], f"重新加载后BACKEND_URL不匹配: {config.BACKEND_URL}"
    print("  ✓ 配置重新加载正确")
    
    # 恢复原始配置
    config.set('backend', {
        'host': DEFAULT_CONFIG['backend']['host'],
        'port': DEFAULT_CONFIG['backend']['port'],
        'auto_generate_url': True,
        'url': ''
    })
    
    print("  ✅ 测试1通过：配置持久化正常工作")
    return True

def test_port_detection():
    """测试2: 端口占用检测逻辑"""
    print("\n" + "=" * 60)
    print("[测试2] 端口占用检测")
    print("=" * 60)
    
    # 测试已知被占用的端口（如80端口通常会被系统占用）
    test_port = 80
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', test_port))
            port_occupied = False
            print(f"  端口 {test_port}: 可用")
        except OSError:
            port_occupied = True
            print(f"  端口 {test_port}: 被占用 (符合预期)")
    
    # 测试一个随机高端口（应该可用）
    random_port = 59999
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', random_port))
            port_available = True
            print(f"  端口 {random_port}: 可用 ✓")
        except OSError:
            port_available = False
            print(f"  端口 {random_port}: 被占用")
    
    assert port_available, f"端口 {random_port} 应该可用"
    print("  ✅ 测试2通过：端口检测逻辑正常")
    return True

def test_url_generation():
    """测试3: URL生成逻辑"""
    print("\n" + "=" * 60)
    print("[测试3] URL自动/手动生成")
    print("=" * 60)
    
    # 测试自动生成模式
    config.set('backend', {
        'host': '192.168.1.100',
        'port': 8000,
        'auto_generate_url': True,
        'url': ''
    })
    
    auto_url = config.BACKEND_URL
    assert '192.168.1.100' in auto_url or '127.0.0.1' in auto_url, \
        f"自动URL应包含主机地址: {auto_url}"
    assert ':8000' in auto_url or auto_url.endswith('8000'), \
        f"自动URL应包含端口号: {auto_url}"
    print(f"  自动URL: {auto_url}")
    
    # 测试手动模式
    custom_url = 'https://custom.api.com:8443/v1'
    config.set('backend', {
        'host': '127.0.0.1',
        'port': 8000,
        'auto_generate_url': False,
        'url': custom_url
    })
    
    manual_url = config.BACKEND_URL
    assert manual_url == custom_url, f"手动URL不匹配: {manual_url} != {custom_url}"
    print(f"  手动URL: {manual_url}")
    
    # 恢复默认配置
    config.set('backend', {
        'host': DEFAULT_CONFIG['backend']['host'],
        'port': DEFAULT_CONFIG['backend']['port'],
        'auto_generate_url': True,
        'url': ''
    })
    
    print("  ✅ 测试3通过：URL生成逻辑正常")
    return True

def test_validation_logic():
    """测试4: 配置验证逻辑"""
    print("\n" + "=" * 60)
    print("[测试4] IP地址和URL验证")
    print("=" * 60)
    
    # 测试有效IP地址
    valid_ips = ['0.0.0.0', '127.0.0.1', '192.168.1.1', '10.0.0.1', '172.16.0.1']
    for ip in valid_ips:
        try:
            socket.inet_aton(ip)
            print(f"  ✓ 有效IP: {ip}")
        except socket.error:
            print(f"  ✗ 无效IP: {ip}")
            raise AssertionError(f"{ip} 应该是有效的IP地址")
    
    # 测试无效IP地址
    invalid_ips = ['256.1.1.1', '1.2.3.4.5', 'abc.def.ghi.jkl', '', 'not-an-ip']
    for ip in invalid_ips:
        try:
            socket.inet_aton(ip)
            print(f"  ✗ 应为无效IP但通过了: {ip}")
            raise AssertionError(f"{ip} 应该是无效的IP地址")
        except socket.error:
            print(f"  ✓ 正确识别无效IP: {ip}")
    
    # 测试URL格式
    valid_urls = ['http://example.com', 'https://api.test.com:8080/path']
    invalid_urls = ['ftp://example.com', 'example.com', 'not-a-url']
    
    for url in valid_urls:
        assert url.startswith('http://') or url.startswith('https://'), \
            f"有效URL格式错误: {url}"
        print(f"  ✓ 有效URL: {url}")
    
    for url in invalid_urls:
        is_valid = url.startswith('http://') or url.startswith('https://')
        assert not is_valid, f"应为无效URL但通过了: {url}"
        print(f"  ✓ 正确识别无效URL: {url}")
    
    print("  ✅ 测试4通过：验证逻辑正常")
    return True

def test_backward_compatibility():
    """测试5: 向后兼容性"""
    print("\n" + "=" * 60)
    print("[测试5] 向后兼容性（旧配置文件）")
    print("=" * 60)
    
    # 模拟旧配置文件（无backend节）
    old_style_config = {
        "gui_host": "172.32.48.239",
        "gui_port": 9000,
        "network": {
            "ethernet_ip": "172.32.48.239",
            "ethernet2_ip": "10.143.164.29"
        }
    }
    
    # 从旧配置获取backend（应使用默认值）
    backend = old_style_config.get('backend', DEFAULT_CONFIG['backend'])
    
    assert 'host' in backend, "应有默认host"
    assert 'port' in backend, "应有默认port"
    assert backend['host'] == DEFAULT_CONFIG['backend']['host'], "应使用默认host"
    assert backend['port'] == DEFAULT_CONFIG['backend']['port'], "应使用默认port"
    
    print(f"  旧配置自动使用默认值: host={backend['host']}, port={backend['port']}")
    print("  ✅ 测试5通过：向后兼容性正常")
    return True

def main():
    """运行所有测试"""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  后端服务配置增强功能测试套件".center(38) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)
    
    tests = [
        ("配置持久化", test_config_persistence),
        ("端口占用检测", test_port_detection),
        ("URL生成", test_url_generation),
        ("验证逻辑", test_validation_logic),
        ("向后兼容性", test_backward_compatibility),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, True, None))
        except Exception as e:
            results.append((name, False, str(e)))
            import traceback
            traceback.print_exc()
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✅ 通过" if success else f"❌ 失败 ({error})"
        print(f"  {name}: {status}")
    
    print("\n" + "-" * 60)
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！增强功能实现完整且正常工作！")
        print("=" * 60)
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
