#!/usr/bin/env python3
"""
main.py Import 使用情况分析工具
检查每个 import 语句是否在代码中被实际使用
"""

import re

def analyze_imports(file_path):
    """分析文件中的 import 使用情况"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 提取所有 import 语句
    imports = []
    in_import_section = True
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 检测 import 语句
        if stripped.startswith('import ') or stripped.startswith('from '):
            imports.append({
                'line_num': i,
                'statement': stripped,
                'used': False,
                'usage_count': 0,
                'usage_lines': []
            })
        elif in_import_section and stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
            # 遇到第一个非空、非注释、非 import 的行，结束导入区域
            if not any(keyword in stripped for keyword in ['def ', 'class ', '=', 'PASSWORD_SECRET_KEY']):
                in_import_section = False
    
    # 检查每个 import 的使用情况
    results = []
    
    for imp in imports:
        statement = imp['statement']
        line_num = imp['line_num']
        
        # 解析 import 语句，提取导入的名称
        imported_names = []
        
        if statement.startswith('from '):
            # from xxx import a, b, c
            match = re.match(r'from\s+\S+\s+import\s+(.+)', statement)
            if match:
                import_part = match.group(1).strip()
                # 处理括号包裹的多行导入
                if '(' in import_part:
                    import_part = import_part.replace('(', '').replace(')', '')
                
                for name in import_part.split(','):
                    name = name.strip()
                    if name == '*':
                        imported_names.append(('*',))
                    else:
                        # 处理 as 别名
                        parts = name.split(' as ')
                        if len(parts) == 2:
                            imported_names.append((parts[0].strip(), parts[1].strip()))
                        else:
                            imported_names.append((name.strip(), name.strip()))
        elif statement.startswith('import '):
            # import xxx
            match = re.match(r'import\s+(\S+)', statement)
            if match:
                import_part = match.group(1).strip()
                parts = import_part.split(' as ')
                if len(parts) == 2:
                    imported_names.append((parts[0].strip(), parts[1].strip()))
                else:
                    imported_names.append((import_part.strip(), import_part.strip()))
        
        # 检查每个导入名称的使用情况
        is_used = False
        total_usage = 0
        usage_examples = []
        
        for name in imported_names:
            if isinstance(name, tuple):
                if len(name) == 2:
                    original_name, use_name = name
                else:
                    original_name = use_name = name[0]
            else:
                original_name = use_name = name
            if original_name == '*':
                # 无法检查 * 导入的具体使用
                is_used = True
                usage_examples.append(f"行 {line_num}: * (无法自动检测)")
                continue
            
            # 构建搜索模式（单词边界匹配）
            pattern = r'\b' + re.escape(use_name) + r'\b'
            
            # 在整个文件中搜索（排除 import 行本身）
            matches = []
            for check_line_num, check_line in enumerate(lines, 1):
                if check_line_num != line_num:  # 排除 import 行本身
                    if re.search(pattern, check_line):
                        matches.append(check_line_num)
            
            count = len(matches)
            total_usage += count
            
            if count > 0:
                is_used = True
                if len(usage_examples) < 3:  # 只记录前3个使用示例
                    usage_examples.append(
                        f"{use_name}: 使用 {count} 次 "
                        f"(如: 行 {matches[0]})"
                    )
        
        results.append({
            'line': line_num,
            'statement': statement,
            'is_used': is_used,
            'usage_count': total_usage,
            'examples': usage_examples
        })
    
    return results

def main():
    file_path = r'd:\local_pysys\vue-element-plus-admin-master\backend\main.py'
    
    print("="*100)
    print("📊 main.py Import 使用情况分析报告")
    print("="*100)
    print(f"\n文件路径: {file_path}")
    
    results = analyze_imports(file_path)
    
    # 分类统计
    used_imports = [r for r in results if r['is_used']]
    unused_imports = [r for r in results if not r['is_used']]
    
    print(f"\n📈 统计摘要:")
    print(f"   总导入数: {len(results)}")
    print(f"   已使用:   {len(used_imports)} ({len(used_imports)/len(results)*100:.1f}%)")
    print(f"   未使用:   {len(unused_imports)} ({len(unused_imports)/len(results)*100:.1f}%)")
    
    # 显示未使用的导入
    if unused_imports:
        print("\n" + "="*100)
        print("⚠️  未使用的 Import 清单 (建议删除)")
        print("="*100)
        print(f"\n{'序号':<5} {'行号':<6} {'Import 语句'}")
        print("-"*100)
        
        for i, imp in enumerate(unused_imports, 1):
            print(f"{i:<5} {imp['line']:<6} {imp['statement']}")
    
    # 显示已使用的导入（简要）
    print("\n" + "="*100)
    print("✅ 已使用的 Import 清单")
    print("="*100)
    print(f"\n{'序号':<5} {'行号':<6} {'使用次数':<8} {'Import 语句'}")
    print("-"*100)
    
    for i, imp in enumerate(used_imports, 1):
        examples_str = '; '.join(imp['examples'][:2]) if imp['examples'] else ''
        print(f"{i:<5} {imp['line']:<6} {imp['usage_count']:<8} {imp['statement']}")
        if examples_str:
            print(f"      └─ {examples_str}")
    
    # 输出详细的未使用清单（用于复制）
    if unused_imports:
        print("\n" + "="*100)
        print("📋 未使用 Import 详细信息（用于确认删除）")
        print("="*100)
        
        for i, imp in enumerate(unused_imports, 1):
            print(f"\n[{i}] 行 {imp['line']}:")
            print(f"    {imp['statement']}")
    
    return unused_imports

if __name__ == "__main__":
    main()
