#!/usr/bin/env python3
"""
Token算力市场 - OpenClaw Skill
去中心化GPU算力交易平台
"""

import sys
import requests
import argparse
from typing import Optional

# API配置
API_BASE = "http://compute.token-master.cn"
# 备用地址
API_BACKUP = "http://compute.token-master.ai"

def get_api_url() -> str:
    """获取可用的API地址"""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        if resp.status_code == 200:
            return API_BASE
    except:
        pass
    return API_BACKUP

def format_stats(data: dict) -> str:
    """格式化市场统计数据"""
    providers = data.get('providers', {})
    tasks = data.get('tasks', {})
    economy = data.get('economy', {})
    
    output = []
    output.append("📊 算力市场实时统计")
    output.append("=" * 40)
    output.append("")
    output.append("🔌 算力提供商:")
    output.append(f"   总计: {providers.get('total', 0)}")
    output.append(f"   在线: {providers.get('online', 0)}")
    output.append(f"   繁忙: {providers.get('busy', 0)}")
    output.append("")
    output.append("📋 任务状态:")
    output.append(f"   总计: {tasks.get('total', 0)}")
    output.append(f"   待处理: {tasks.get('pending', 0)}")
    output.append(f"   运行中: {tasks.get('running', 0)}")
    output.append(f"   已完成: {tasks.get('completed', 0)}")
    output.append("")
    output.append("💰 经济统计:")
    output.append(f"   总奖励: ¥{economy.get('total_rewards', 0):.2f}")
    output.append(f"   平台收入: ¥{economy.get('platform_revenue', 0):.2f}")
    output.append("")
    output.append("💡 提示: 访问 http://token-master.cn/shop/ 查看完整平台")
    
    return "\n".join(output)

def format_providers(providers: list) -> str:
    """格式化提供商列表"""
    if not providers:
        return "暂无算力提供商\n\n💡 使用 'compute-market register' 注册成为提供商"
    
    output = []
    output.append("🔌 算力提供商列表")
    output.append("=" * 60)
    output.append("")
    
    for p in providers:
        output.append(f"📦 {p.get('name', 'Unknown')}")
        output.append(f"   ID: {p.get('id', 'N/A')}")
        output.append(f"   类型: {p.get('type', 'N/A')}")
        output.append(f"   价格: ¥{p.get('price', 0)}/小时")
        output.append(f"   状态: {p.get('status', 'unknown')}")
        output.append("")
    
    return "\n".join(output)

def format_tasks(tasks: list) -> str:
    """格式化任务列表"""
    if not tasks:
        return "暂无任务\n\n💡 使用 'compute-market submit' 提交新任务"
    
    output = []
    output.append("📋 最近任务列表")
    output.append("=" * 60)
    output.append("")
    
    for t in tasks[-10:]:  # 只显示最近10个
        output.append(f"📝 {t.get('id', 'Unknown')}")
        output.append(f"   类型: {t.get('type', 'N/A')}")
        output.append(f"   状态: {t.get('status', 'unknown')}")
        output.append(f"   优先级: {t.get('priority', 'NORMAL')}")
        output.append(f"   奖励: ¥{t.get('reward', 0)}")
        output.append("")
    
    return "\n".join(output)

def cmd_stats():
    """查看市场统计"""
    try:
        api = get_api_url()
        resp = requests.get(f"{api}/api/stats", timeout=5)
        resp.raise_for_status()
        print(format_stats(resp.json()))
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到算力市场服务器")
        print("   请检查网络连接或稍后再试")
    except Exception as e:
        print(f"❌ 获取统计数据失败: {e}")

def cmd_providers():
    """查看提供商列表"""
    try:
        api = get_api_url()
        resp = requests.get(f"{api}/api/providers", timeout=5)
        resp.raise_for_status()
        print(format_providers(resp.json()))
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到算力市场服务器")
    except Exception as e:
        print(f"❌ 获取提供商列表失败: {e}")

def cmd_tasks():
    """查看任务列表"""
    try:
        api = get_api_url()
        resp = requests.get(f"{api}/api/tasks", timeout=5)
        resp.raise_for_status()
        print(format_tasks(resp.json()))
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到算力市场服务器")
    except Exception as e:
        print(f"❌ 获取任务列表失败: {e}")

def cmd_register(name: str, compute_type: str, price: float):
    """注册算力提供商"""
    try:
        api = get_api_url()
        data = {
            "user_id": "cli_user",
            "name": name,
            "compute_type": compute_type,
            "price_per_hour": price
        }
        resp = requests.post(f"{api}/api/providers", json=data, timeout=5)
        resp.raise_for_status()
        result = resp.json()
        print(f"✅ 提供商注册成功!")
        print(f"   ID: {result.get('id')}")
        print(f"   名称: {name}")
        print(f"   类型: {compute_type}")
        print(f"   价格: ¥{price}/小时")
        print("")
        print("💡 访问完整平台管理您的算力资源:")
        print("   http://token-master.cn/shop/")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到算力市场服务器")
    except Exception as e:
        print(f"❌ 注册失败: {e}")

def cmd_submit(task_type: str, compute: int, reward: float, priority: str = "NORMAL"):
    """提交计算任务"""
    try:
        api = get_api_url()
        data = {
            "user_id": "cli_user",
            "type": task_type,
            "compute": compute,
            "duration": 5,
            "reward": reward,
            "priority": priority
        }
        resp = requests.post(f"{api}/api/tasks", json=data, timeout=5)
        resp.raise_for_status()
        result = resp.json()
        print(f"✅ 任务提交成功!")
        print(f"   任务ID: {result.get('id')}")
        print(f"   类型: {task_type}")
        print(f"   算力需求: {compute}")
        print(f"   奖励: ¥{reward}")
        print(f"   状态: {result.get('status')}")
        print("")
        print("💡 使用 'compute-market tasks' 查看任务状态")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到算力市场服务器")
    except Exception as e:
        print(f"❌ 提交任务失败: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Token算力市场 - 去中心化GPU算力交易平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  compute-market stats                    # 查看市场统计
  compute-market providers                # 查看提供商列表
  compute-market register -n "MyGPU" -t gpu_rtx4090 -p 2.5
  compute-market submit -t inference -c 10 -r 5.0
  compute-market tasks                    # 查看任务列表

访问完整平台: http://token-master.cn/shop/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # stats命令
    subparsers.add_parser('stats', help='查看市场统计')
    
    # providers命令
    subparsers.add_parser('providers', help='查看算力提供商列表')
    
    # tasks命令
    subparsers.add_parser('tasks', help='查看任务列表')
    
    # register命令
    register_parser = subparsers.add_parser('register', help='注册成为算力提供商')
    register_parser.add_argument('-n', '--name', required=True, help='提供商名称')
    register_parser.add_argument('-t', '--type', default='gpu_rtx4090', 
                                 help='算力类型 (默认: gpu_rtx4090)')
    register_parser.add_argument('-p', '--price', type=float, default=2.5,
                                 help='每小时价格 (默认: 2.5)')
    
    # submit命令
    submit_parser = subparsers.add_parser('submit', help='提交计算任务')
    submit_parser.add_argument('-t', '--type', default='inference',
                               help='任务类型 (默认: inference)')
    submit_parser.add_argument('-c', '--compute', type=int, default=10,
                               help='算力需求 (默认: 10)')
    submit_parser.add_argument('-r', '--reward', type=float, default=5.0,
                               help='任务奖励 (默认: 5.0)')
    submit_parser.add_argument('--priority', default='NORMAL',
                               help='优先级: LOW/NORMAL/HIGH/URGENT (默认: NORMAL)')
    
    args = parser.parse_args()
    
    if args.command == 'stats':
        cmd_stats()
    elif args.command == 'providers':
        cmd_providers()
    elif args.command == 'tasks':
        cmd_tasks()
    elif args.command == 'register':
        cmd_register(args.name, args.type, args.price)
    elif args.command == 'submit':
        cmd_submit(args.type, args.compute, args.reward, args.priority)
    else:
        parser.print_help()
        print("\n💡 访问完整平台: http://token-master.cn/shop/")

if __name__ == '__main__':
    main()
