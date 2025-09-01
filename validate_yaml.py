#!/usr/bin/env python3
"""
简单的YAML验证脚本
"""

def validate_yaml_structure(file_path):
    """验证YAML文件的基本结构"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本的YAML结构检查
        lines = content.split('\n')
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 检查制表符
            if '\t' in line:
                issues.append(f"第{i}行包含制表符，YAML应使用空格缩进")
            
            # 检查基本的键值对格式
            if ':' in line and line.strip() and not line.strip().startswith('#'):
                # 简单检查冒号后是否有空格
                colon_pos = line.find(':')
                if colon_pos < len(line) - 1:
                    after_colon = line[colon_pos + 1:]
                    if after_colon and not after_colon.startswith(' '):
                        if not after_colon.startswith('\n') and after_colon != '':
                            issues.append(f"第{i}行冒号后缺少空格: {line.strip()}")
        
        if issues:
            print("发现的潜在问题：")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ YAML基本结构检查通过")
            return True
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    validate_yaml_structure('.github/workflows/ci-enhanced.yml')
