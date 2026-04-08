#!/usr/bin/env python3
"""
忆伴 MemPal v1.0.0 - Performance Benchmark
性能基准测试：测试不同数据量下的性能表现
"""

import sys
import time
import tempfile
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "memory_v41", 
    Path(__file__).parent.parent / "bin" / "memory-v4.1.py"
)
memory_v41 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory_v41)

# ─────────────────────────────────────────────────────────────
# 基准测试
# ─────────────────────────────────────────────────────────────

def benchmark_capture(count):
    """测试采集性能"""
    print(f"\n📝 采集性能测试 ({count} 条)...")
    
    start = time.time()
    for i in range(count):
        result = memory_v41.capture(
            type="event",
            content=f"基准测试记忆 {i+1}",
            importance=0.3
        )
    end = time.time()
    
    total = end - start
    avg = total / count * 1000  # 毫秒
    
    print(f"  总耗时：{total:.3f} 秒")
    print(f"  平均每条：{avg:.2f} ms")
    print(f"  吞吐量：{count/total:.1f} 条/秒")
    
    return {"total": total, "avg_ms": avg, "per_sec": count/total}

def benchmark_search(total_memories, query_count):
    """测试搜索性能"""
    print(f"\n🔍 搜索性能测试 ({total_memories} 条记忆，{query_count} 次查询)...")
    
    # 先创建测试数据
    test_dir = tempfile.mkdtemp()
    daily_file = Path(test_dir) / "2026-04-08.md"
    
    with open(daily_file, 'w', encoding='utf-8') as f:
        f.write("# 2026-04-08\n\n")
        for i in range(total_memories):
            f.write(f"- [12:00:00] [event] 测试记忆 {i+1} 包含关键词\n")
    
    # 临时修改 DAILY_DIR
    original_daily = memory_v41.DAILY_DIR
    memory_v41.DAILY_DIR = Path(test_dir)
    
    # 执行搜索
    start = time.time()
    for i in range(query_count):
        result = memory_v41.search(query="关键词", limit=10)
    end = time.time()
    
    # 恢复原路径
    memory_v41.DAILY_DIR = original_daily
    
    total = end - start
    avg = total / query_count * 1000  # 毫秒
    
    print(f"  总耗时：{total:.3f} 秒")
    print(f"  平均每次：{avg:.2f} ms")
    print(f"  吞吐量：{query_count/total:.1f} 次/秒")
    
    return {"total": total, "avg_ms": avg, "per_sec": query_count/total}

def benchmark_weight_calculation(count):
    """测试权重计算性能"""
    print(f"\n⚖️  权重计算性能测试 ({count} 次)...")
    
    memory = {"content": "[decision] 测试记忆", "created_at": ""}
    
    start = time.time()
    for i in range(count):
        memory_v41.calculate_weight_advanced(memory, "测试")
    end = time.time()
    
    total = end - start
    avg = total / count * 1000  # 毫秒
    
    print(f"  总耗时：{total:.3f} 秒")
    print(f"  平均每次：{avg:.3f} ms")
    print(f"  吞吐量：{count/total:.1f} 次/秒")
    
    return {"total": total, "avg_ms": avg, "per_sec": count/total}

def main():
    """主测试"""
    print("=" * 70)
    print("🧠 忆伴 MemPal v1.0.0 - 性能基准测试")
    print("=" * 70)
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 测试 1：采集性能（不同数据量）
    print("\n" + "=" * 70)
    print("测试 1: 采集性能")
    print("=" * 70)
    for count in [10, 50, 100]:
        results[f"capture_{count}"] = benchmark_capture(count)
    
    # 测试 2：搜索性能（不同数据量）
    print("\n" + "=" * 70)
    print("测试 2: 搜索性能")
    print("=" * 70)
    for total in [50, 100, 200]:
        results[f"search_{total}"] = benchmark_search(total, 10)
    
    # 测试 3：权重计算性能
    print("\n" + "=" * 70)
    print("测试 3: 权重计算性能")
    print("=" * 70)
    results["weight_1000"] = benchmark_weight_calculation(1000)
    
    # 输出总结
    print("\n" + "=" * 70)
    print("📊 性能总结")
    print("=" * 70)
    
    print("\n采集性能:")
    for key, val in results.items():
        if key.startswith("capture"):
            count = int(key.split("_")[1])
            print(f"  {count} 条：{val['avg_ms']:.2f} ms/条 ({val['per_sec']:.1f} 条/秒)")
    
    print("\n搜索性能:")
    for key, val in results.items():
        if key.startswith("search"):
            count = int(key.split("_")[1])
            print(f"  {count} 条记忆：{val['avg_ms']:.2f} ms/次 ({val['per_sec']:.1f} 次/秒)")
    
    print("\n权重计算:")
    print(f"  1000 次：{results['weight_1000']['avg_ms']:.3f} ms/次")
    
    print("\n" + "=" * 70)
    print("✅ 性能测试完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
