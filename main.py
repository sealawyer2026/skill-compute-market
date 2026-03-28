#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算力市场 - CLI入口
Compute Market CLI

分布式算力调度平台
"""

import argparse
import json
import sys
import time

from market import ComputeMarket, TaskPriority, ProviderStatus, TaskStatus, get_compute_market


def print_header():
    """打印标题"""
    print("""
╔══════════════════════════════════════════════╗
║     Token算力市场 v1.0.0                     ║
║     分布式算力调度平台                       ║
╚══════════════════════════════════════════════╝
""")


def cmd_market(args):
    """查看市场行情"""
    market = get_compute_market(args.config)
    stats = market.get_market_stats()
    
    print("📊 算力市场行情")
    print("=" * 60)
    print()
    
    # 提供商统计
    print("🏢 提供商")
    print("-" * 60)
    print(f"   总数: {stats['providers']['total']}")
    print(f"   在线: {stats['providers']['online']} ✅")
    print(f"   忙碌: {stats['providers']['busy']} 🔄")
    print(f"   离线: {stats['providers']['offline']} ⚫")
    print()
    
    # 算力统计
    print("⚡ 算力资源")
    print("-" * 60)
    print(f"   总算力: {stats['compute_power']['total']}")
    print(f"   可用算力: {stats['compute_power']['available']}")
    print(f"   利用率: {stats['compute_power']['utilization']}%")
    print()
    
    # 任务统计
    print("📋 任务状态")
    print("-" * 60)
    print(f"   总任务: {stats['tasks']['total']}")
    print(f"   已完成: {stats['tasks']['completed']} ✅")
    print(f"   进行中: {stats['tasks']['running']} 🔄")
    print(f"   等待中: {stats['tasks']['pending']} ⏳")
    print(f"   失败: {stats['tasks']['failed']} ❌")
    print()
    
    # 经济统计
    print("💰 经济统计")
    print("-" * 60)
    print(f"   任务奖励总额: ¥{stats['economy']['total_rewards']:.2f}")
    print(f"   平台收入: ¥{stats['economy']['platform_revenue']:.2f}")
    print(f"   提供商收益: ¥{stats['economy']['provider_earnings']:.2f}")


def cmd_providers(args):
    """查看提供商列表"""
    market = get_compute_market(args.config)
    
    print("🏢 算力提供商")
    print("=" * 80)
    print(f"{'ID':<20} {'名称':<15} {'类型':<15} {'状态':<10} {'价格/小时':<12} {'信誉':<8}")
    print("-" * 80)
    
    for provider in market.providers.values():
        status_icon = {
            "online": "✅",
            "busy": "🔄",
            "offline": "⚫",
            "maintenance": "🔧"
        }.get(provider.status.value, "❓")
        
        print(f"{provider.id:<20} {provider.name:<15} {provider.compute_type:<15} {status_icon} {provider.status.value:<8} ¥{provider.price_per_hour:<10.2f} {provider.reputation_score:.1f}")


def cmd_register(args):
    """注册提供商"""
    market = get_compute_market(args.config)
    
    provider = market.register_provider(
        owner_id=args.user,
        name=args.name,
        compute_type=args.type,
        price_per_hour=args.price,
        location=args.location
    )
    
    print(f"✅ 算力提供商注册成功")
    print(f"   提供商ID: {provider.id}")
    print(f"   名称: {provider.name}")
    print(f"   算力类型: {provider.compute_type}")
    print(f"   算力值: {provider.compute_power}")
    print(f"   显存: {provider.vram_gb}GB")
    print(f"   定价: ¥{provider.price_per_hour}/小时")
    print(f"   初始信誉: {provider.reputation_score}")


def cmd_submit(args):
    """提交任务"""
    market = get_compute_market(args.config)
    
    priority = TaskPriority[args.priority.upper()]
    
    task = market.submit_task(
        user_id=args.user,
        task_type=args.type,
        required_compute=args.compute,
        required_vram=args.vram,
        estimated_duration=args.duration * 60,  # 转换为秒
        reward=args.reward,
        priority=priority
    )
    
    print(f"✅ 任务提交成功")
    print(f"   任务ID: {task.id}")
    print(f"   类型: {task.task_type}")
    print(f"   所需算力: {task.required_compute}")
    print(f"   所需显存: {task.required_vram}GB")
    print(f"   预估时长: {args.duration}分钟")
    print(f"   奖励: ¥{task.reward:.2f}")
    print(f"   优先级: {task.priority.name}")
    print(f"   状态: {task.status.value}")


def cmd_tasks(args):
    """查看任务列表"""
    market = get_compute_market(args.config)
    
    print("📋 任务列表")
    print("=" * 100)
    print(f"{'ID':<20} {'类型':<12} {'状态':<12} {'优先级':<8} {'算力':<8} {'奖励':<10} {'提供商':<15}")
    print("-" * 100)
    
    for task in list(market.tasks.values())[:20]:
        status_icon = {
            "pending": "⏳",
            "scheduling": "📋",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫"
        }.get(task.status.value, "❓")
        
        provider_name = "-"
        if task.assigned_provider and task.assigned_provider in market.providers:
            provider_name = market.providers[task.assigned_provider].name[:14]
        
        print(f"{task.id:<20} {task.task_type:<12} {status_icon} {task.status.value:<10} {task.priority.name:<8} {task.required_compute:<8} ¥{task.reward:<9.2f} {provider_name:<15}")


def cmd_demo(args):
    """运行演示"""
    market = get_compute_market(args.config)
    
    print("🎬 算力市场演示")
    print("=" * 60)
    print()
    
    # 1. 注册提供商
    print("1️⃣ 注册算力提供商...")
    providers = []
    for i in range(3):
        p = market.register_provider(
            owner_id=f"owner_{i}",
            name=f"Provider-{i+1}",
            compute_type="gpu_rtx4090" if i < 2 else "gpu_a100",
            price_per_hour=2.5 if i < 2 else 8.0
        )
        providers.append(p)
        print(f"   ✅ {p.name} (ID: {p.id})")
    print()
    
    # 2. 提交任务
    print("2️⃣ 提交计算任务...")
    tasks = []
    for i in range(5):
        t = market.submit_task(
            user_id="user_001",
            task_type=["inference", "training", "embedding"][i % 3],
            required_compute=[10, 50, 15][i % 3],
            required_vram=[8, 40, 4][i % 3],
            estimated_duration=[300, 7200, 600][i % 3],
            reward=[5.0, 100.0, 10.0][i % 3],
            priority=[TaskPriority.NORMAL, TaskPriority.HIGH, TaskPriority.LOW][i % 3]
        )
        tasks.append(t)
        print(f"   ✅ 任务 {t.id} (奖励: ¥{t.reward})")
    print()
    
    # 3. 启动调度器
    print("3️⃣ 启动算力调度器...")
    market.start_scheduler()
    time.sleep(3)
    print()
    
    # 4. 显示市场状态
    print("4️⃣ 当前市场状态")
    print("-" * 60)
    stats = market.get_market_stats()
    print(f"   在线提供商: {stats['providers']['online']}")
    print(f"   可用算力: {stats['compute_power']['available']}")
    print(f"   等待任务: {stats['tasks']['pending']}")
    print(f"   进行中任务: {stats['tasks']['running']}")
    print()
    
    # 5. 完成任务
    print("5️⃣ 模拟任务完成...")
    for task in tasks[:2]:
        if task.assigned_provider:
            market.start_task(task.id)
            result = market.complete_task(
                task_id=task.id,
                result_data=f"Result for {task.id}",
                actual_duration=task.estimated_duration,
                success=True
            )
            print(f"   ✅ 任务 {task.id} 完成")
    print()
    
    # 6. 最终统计
    print("6️⃣ 最终统计")
    print("-" * 60)
    stats = market.get_market_stats()
    print(f"   已完成任务: {stats['tasks']['completed']}")
    print(f"   平台收入: ¥{stats['economy']['platform_revenue']:.2f}")
    print(f"   提供商收益: ¥{stats['economy']['provider_earnings']:.2f}")
    print()
    
    market.stop_scheduler()
    print("✅ 演示完成!")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Token算力市场 - 分布式算力调度平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看市场行情
  python main.py market
  
  # 查看提供商列表
  python main.py providers
  
  # 注册算力提供商
  python main.py register --user u001 --name "MyGPU" --type gpu_rtx4090 --price 2.5
  
  # 提交计算任务
  python main.py submit --user u002 --type inference --compute 10 --vram 8 --duration 5 --reward 5.0
  
  # 查看任务列表
  python main.py tasks
  
  # 运行完整演示
  python main.py demo

支持的算力类型:
  - gpu_rtx4090: NVIDIA RTX 4090 (24GB VRAM)
  - gpu_a100: NVIDIA A100 (80GB VRAM)
  - gpu_h100: NVIDIA H100 (80GB VRAM)
  - cpu_standard: Standard CPU

任务类型:
  - inference: 模型推理
  - training: 模型训练
  - fine_tuning: 微调训练
  - embedding: 向量嵌入

调度策略:
  - cost_optimized: 成本优先 (默认)
  - performance: 性能优先
  - reputation: 信誉优先
  - balanced: 均衡策略

费率:
  - 平台手续费: 15%
        """
    )
    
    parser.add_argument('--version', action='version', version='Token算力市场 v1.0.0')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # market 命令
    subparsers.add_parser('market', help='查看市场行情')
    
    # providers 命令
    subparsers.add_parser('providers', help='查看提供商列表')
    
    # register 命令
    register_parser = subparsers.add_parser('register', help='注册算力提供商')
    register_parser.add_argument('--user', required=True, help='用户ID')
    register_parser.add_argument('--name', required=True, help='提供商名称')
    register_parser.add_argument('--type', required=True, help='算力类型')
    register_parser.add_argument('--price', type=float, required=True, help='每小时价格')
    register_parser.add_argument('--location', default='', help='地理位置')
    
    # submit 命令
    submit_parser = subparsers.add_parser('submit', help='提交计算任务')
    submit_parser.add_argument('--user', required=True, help='用户ID')
    submit_parser.add_argument('--type', required=True, help='任务类型')
    submit_parser.add_argument('--compute', type=int, required=True, help='所需算力')
    submit_parser.add_argument('--vram', type=int, default=0, help='所需显存(GB)')
    submit_parser.add_argument('--duration', type=int, required=True, help='预估时长(分钟)')
    submit_parser.add_argument('--reward', type=float, required=True, help='任务奖励')
    submit_parser.add_argument('--priority', default='NORMAL', choices=['LOW', 'NORMAL', 'HIGH', 'URGENT'], help='优先级')
    
    # tasks 命令
    subparsers.add_parser('tasks', help='查看任务列表')
    
    # demo 命令
    subparsers.add_parser('demo', help='运行演示')
    
    args = parser.parse_args()
    
    if not args.command:
        print_header()
        parser.print_help()
        sys.exit(0)
    
    try:
        if args.command == 'market':
            cmd_market(args)
        elif args.command == 'providers':
            cmd_providers(args)
        elif args.command == 'register':
            cmd_register(args)
        elif args.command == 'submit':
            cmd_submit(args)
        elif args.command == 'tasks':
            cmd_tasks(args)
        elif args.command == 'demo':
            cmd_demo(args)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
