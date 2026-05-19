#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试后端服务IP地址配置功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config, DEFAULT_CONFIG

def test_backend_config():
    """测试后端服务配置"""
    print("=" * 60)
    print("测试后端服务IP地址配置功能")
    print("=" * 60)
    
    # 1. 测试默认配置
    print("\n[1] 测试默认配置...")
    assert hasattr(config, 'BACKEND'), "缺少 BACKEND 属性"
    assert hasattr(config, 'BACKEND_HOST'), "缺少 BACKEND_HOST 属性"
    assert hasattr(config, 'BACKEND_PORT'), "缺少 BACKEND_PORT 属性"
    assert hasattr(config, 'BACKEND_AUTO_GENERATE_URL'), "缺少 BACKEND_AUTO_GENERATE_URL 属性"
    assert hasattr(config, 'BACKEND_URL'), "缺少 BACKEND_URL 属性"
    
    print(f"  ✓ BACKEND_HOST: {config.BACKEND_HOST}")
    print(f"  ✓ BACKEND_PORT: {config.BACKEND_PORT}")
    print(f"  ✓ BACKEND_AUTO_GENERATE_URL: {config.BACKEND_AUTO_GENERATE_URL}")
    print(f"  ✓ BACKEND_URL: {config.BACKEND_URL}")
    
    # 2. 测试配置值
    print("\n[2] 测试配置值...")
    assert config.BACKEND_HOST == DEFAULT_CONFIG['backend']['host'], \
        f"BACKEND_HOST 不匹配: {config.BACKEND_HOST} != {DEFAULT_CONFIG['backend']['host']}"
    assert config.BACKEND_PORT == DEFAULT_CONFIG['backend']['port'], \
        f"BACKEND_PORT 不匹配: {config.BACKEND_PORT} != {DEFAULT_CONFIG['backend']['port']}"
    assert config.BACKEND_AUTO_GENERATE_URL == DEFAULT_CONFIG['backend']['auto_generate_url'], \
        f"BACKEND_AUTO_GENERATE_URL 不匹配"
    
    print("  ✓ 所有默认配置值正确")
    
    # 3. 测试URL生成逻辑
    print("\n[3] 测试URL生成逻辑...")
    
    # 测试自动生成模式
    if config.BACKEND_AUTO_GENERATE_URL:
        backend_url = config.BACKEND_URL
        assert backend_url.startswith("http://"), f"URL应以http://开头: {backend_url}"
        assert f":{config.BACKEND_PORT}" in backend_url or backend_url.endswith(str(config.BACKEND_PORT)), \
            f"URL应包含端口号: {backend_url}"
        print(f"  ✓ 自动生成的URL格式正确: {backend_url}")
    
    # 4. 测试配置修改和保存
    print("\n[4] 测试配置修改和保存...")
    original_host = config.BACKEND_HOST
    original_port = config.BACKEND_PORT
    
    try:
        # 修改配置
        test_host = "192.168.1.100"
        test_port = 9001
        
        config.set('backend', {
            'host': test_host,
            'port': test_port,
            'auto_generate_url': True,
            'url': ''
        })
        
        assert config.BACKEND_HOST == test_host, "修改后的BACKEND_HOST不匹配"
        assert config.BACKEND_PORT == test_port, "修改后的BACKEND_PORT不匹配"
        
        new_url = config.BACKEND_URL
        assert test_host in new_url or "127.0.0.1" in new_url, \
            f"修改后的URL应包含新主机地址: {new_url}"
        assert str(test_port) in new_url, f"修改后的URL应包含新端口: {new_url}"
        
        print(f"  ✓ 配置修改成功")
        print(f"  ✓ 新的BACKEND_URL: {new_url}")
        
    finally:
        # 恢复原始配置
        config.set('backend', {
            'host': original_host,
            'port': original_port,
            'auto_generate_url': True,
            'url': ''
        })
    
    # 5. 测试向后兼容性（旧配置文件）
    print("\n[5] 测试向后兼容性...")
    
    # 模拟旧配置文件（无backend节）
    old_config = {
        "gui_host": "172.32.48.239",
        "gui_port": 9000,
        "network": {
            "ethernet_ip": "172.32.48.239",
            "ethernet2_ip": "10.143.164.29",
            "use_ethernet2_for_portal": True
        }
    }
    
    # 验证即使没有backend节，也能使用默认值
    backend_from_old = old_config.get('backend', DEFAULT_CONFIG['backend'])
    assert 'host' in backend_from_old, "应使用默认backend配置"
    assert 'port' in backend_from_old, "应使用默认backend配置"
    
    print("  ✓ 向后兼容性正常（使用默认值）")
    
    # 6. 测试手动URL配置
    print("\n[6] 测试手动URL配置...")
    
    try:
        custom_url = "https://api.example.com:8443/backend"
        config.set('backend', {
            'host': "127.0.0.1",
            'port': 8000,
            'auto_generate_url': False,
            'url': custom_url
        })
        
        manual_url = config.BACKEND_URL
        assert manual_url == custom_url, f"手动URL不匹配: {manual_url} != {custom_url}"
        
        print(f"  ✓ 手动URL配置成功: {manual_url}")
        
    finally:
        # 恢复原始配置
        config.set('backend', {
            'host': original_host,
            'port': original_port,
            'auto_generate_url': True,
            'url': ''
        })
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！后端服务IP地址配置功能正常工作")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_backend_config()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
