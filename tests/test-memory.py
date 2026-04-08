#!/usr/bin/env python3
"""
Unified Memory System - Test Suite
测试记忆系统功能
"""

import sys
import json
sys.path.insert(0, '/Users/sissname/.openclaw/workspace/skills/unified-memory-system/bin')

from memory import capture, search, govern, forget, export, print_status

def test_capture():
    """测试采集功能"""
    print("\n📝 测试采集功能...")
    
    # 测试 1：普通采集
    result = capture(
        type="decision",
        content="测试决策内容",
        importance=0.5,
        tags=["测试"]
    )
    assert result['status'] == 'success', "采集失败"
    print(f"  ✅ 普通采集：{result['id']}")
    
    # 测试 2：高重要性采集（应该写入 L1）
    result = capture(
        type="insight",
        content="高重要性洞察",
        importance=0.95,
        tags=["重要"]
    )
    assert result['layer'] == 'L1', "高重要性应该写入 L1"
    print(f"  ✅ 高重要性采集 (L1): {result['id']}")
    
    return True

def test_search():
    """测试搜索功能"""
    print("\n🔍 测试搜索功能...")
    
    # 测试 1：关键词搜索
    results = search(query="测试", limit=5)
    assert len(results) > 0, "搜索应该返回结果"
    print(f"  ✅ 关键词搜索：找到 {len(results)} 条")
    
    # 测试 2：类型过滤
    results = search(query="决策", type="decision", limit=5)
    print(f"  ✅ 类型过滤：找到 {len(results)} 条")
    
    return True

def test_govern():
    """测试治理功能"""
    print("\n⚖️  测试治理功能...")
    
    result = govern(auto=True)
    print(f"  ✅ 治理完成：评分 {result.get('scored', 0)} 条，归档 {result.get('archived', 0)} 条")
    
    return True

def test_export():
    """测试导出功能"""
    print("\n📤 测试导出功能...")
    
    result = export(format="json")
    data = json.loads(result)
    print(f"  ✅ JSON 导出：{len(data)} 条记录")
    
    return True

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧠 Unified Memory System - 测试套件")
    print("="*60)
    
    tests = [
        ("采集功能", test_capture),
        ("搜索功能", test_search),
        ("治理功能", test_govern),
        ("导出功能", test_export)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ {name} 失败：{e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("="*60 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
