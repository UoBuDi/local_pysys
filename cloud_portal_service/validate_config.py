#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置文件完整性验证工具
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEFAULT_CONFIG

def validate_config_file(file_path, config_name=""):
    """验证配置文件的完整性"""
    print(f"\n{'='*60}")
    print(f"验证配置文件: {config_name or file_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return False
    
    # 必要字段清单
    required_fields = {
        # GUI配置
        'gui_host': str,
        'gui_port': int,
        
        # 常规配置
        'auto_start': bool,
        'minimize_to_tray': bool,
        'log_level': str,
        
        # 门户配置
        'portal_base_url': str,
        'portal_sso_url': str,
        'portal_home_url': str,
        'client_id': str,
        'session_timeout': int,
        'token_refresh_threshold': int,
        
        # 网络配置
        'network': dict,
        
        # 后端服务配置 (新增)
        'backend': dict,
    }
    
    errors = []
    warnings = []
    
    # 检查顶层字段
    for field, field_type in required_fields.items():
        if field not in config:
            errors.append(f"缺少必要字段: {field}")
        elif not isinstance(config[field], field_type):
            errors.append(f"字段类型错误: {field} 应为 {field_type.__name__}, 实际为 {type(config[field]).__name__}")
    
    # 检查network子字段
    if 'network' in config and isinstance(config['network'], dict):
        network_required = {
            'ethernet_ip': str,
            'ethernet2_ip': str,
            'use_ethernet2_for_portal': bool,
        }
        for field, field_type in network_required.items():
            if field not in config['network']:
                warnings.append(f"network缺少字段: {field} (将使用默认值)")
            elif not isinstance(config['network'][field], field_type):
                errors.append(f"network.{field} 类型错误")
    
    # 检查backend子字段 (关键新增功能)
    if 'backend' in config and isinstance(config['backend'], dict):
        backend_required = {
            'host': str,
            'port': int,
            'auto_generate_url': bool,
            'url': str,
        }
        for field, field_type in backend_required.items():
            if field not in config['backend']:
                errors.append(f"backend缺少必要字段: {field}")
            elif not isinstance(config['backend'][field], field_type):
                errors.append(f"backend.{field} 类型错误")
        
        # 验证backend配置的合理性
        backend = config['backend']
        
        # 端口范围检查
        port = backend.get('port', 0)
        if not (1 <= port <= 65535):
            errors.append(f"backend.port 超出范围: {port} (应在1-65535之间)")
        
        # host格式检查
        host = backend.get('host', '')
        valid_hosts = ['0.0.0.0', '127.0.0.1']
        if host and host not in valid_hosts:
            import socket
            try:
                socket.inet_aton(host)
            except socket.error:
                errors.append(f"backend.host 无效IP地址: {host}")
        
        # URL格式检查
        url = backend.get('url', '')
        auto_gen = backend.get('auto_generate_url', True)
        if not auto_gen and url:
            if not (url.startswith('http://') or url.startswith('https://')):
                errors.append(f"backend.url 格式错误: 应以http://或https://开头")
        
        # 输出backend配置详情
        print(f"\n📋 Backend配置详情:")
        print(f"   绑定地址 (host): {backend.get('host', 'N/A')}")
        print(f"   监听端口 (port): {backend.get('port', 'N/A')}")
        print(f"   自动生成URL: {backend.get('auto_generate_url', 'N/A')}")
        if auto_gen:
            print(f"   访问URL: [自动生成]")
        else:
            print(f"   访问URL (手动): {url or '[未设置]'}")
    
    else:
        errors.append("缺少backend配置节 (后端服务IP配置功能需要此配置)")
    
    # 显示验证结果
    print(f"\n📊 验证结果:")
    print(f"   总字段数: {len(config)}")
    print(f"   错误数: {len(errors)}")
    print(f"   警告数: {len(warnings)}")
    
    if errors:
        print(f"\n❌ 错误列表:")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    
    if warnings:
        print(f"\n⚠️  警告列表:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    
    if not errors and not warnings:
        print(f"\n✅ 配置文件完整且有效！")
        return True
    elif not errors:
        print(f"\n✅ 配置文件基本有效（有警告）")
        return True
    else:
        print(f"\n❌ 配置文件存在错误，需要修复")
        return False

def main():
    """主函数"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    configs_to_check = [
        (os.path.join(base_dir, 'service_config.json'), "源配置文件"),
        (os.path.join(base_dir, 'dist', 'service_config.json'), "打包目录配置文件"),
    ]
    
    all_valid = True
    results = []
    
    for file_path, name in configs_to_check:
        is_valid = validate_config_file(file_path, name)
        results.append((name, is_valid))
        all_valid = all_valid and is_valid
    
    # 总结
    print(f"\n{'='*60}")
    print("验证总结")
    print(f"{'='*60}")
    
    for name, is_valid in results:
        status = "✅ 通过" if is_valid else "❌ 失败"
        print(f"  {name}: {status}")
    
    if all_valid:
        print(f"\n🎉 所有配置文件验证通过！可以安全打包部署。")
        return 0
    else:
        print(f"\n⚠️  部分配置文件存在问题，请修复后重新打包。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
