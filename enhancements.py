#!/usr/bin/env python3
"""
算力市场增强模块 v2.5
Compute Market Enhancement v2.5

新增功能:
1. 智能任务调度器 (自动匹配最优提供商)
2. 动态定价引擎
3. 任务优先级队列
4. 自动扩缩容
5. 实时监控Dashboard数据
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/token-ecosys-core')

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import heapq
import asyncio
import json

from models import ComputeProvider, ComputeTask, TaskStatus, ComputeType


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0   # 紧急
    HIGH = 1       # 高
    NORMAL = 2     # 正常
    LOW = 3        # 低
    BACKGROUND = 4 # 后台


@dataclass
class ScheduledTask:
    """调度任务包装"""
    priority: int
    created_at: datetime
    task: ComputeTask
    
    def __lt__(self, other):
        # 优先级高的先执行，同优先级按创建时间
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at


class SmartScheduler:
    """
    智能任务调度器
    
    功能:
    - 优先级队列管理
    - 最优提供商匹配
    - 负载均衡
    - 任务预分配
    """
    
    def __init__(self):
        self.task_queue: List[ScheduledTask] = []
        self.running_tasks: Dict[str, ComputeTask] = {}
        self.task_history: List[Dict] = []
        self.max_concurrent = 100
    
    def submit_task(
        self,
        task: ComputeTask,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> bool:
        """
        提交任务到队列
        
        Args:
            task: 计算任务
            priority: 优先级
        
        Returns:
            是否成功提交
        """
        scheduled = ScheduledTask(
            priority=priority.value,
            created_at=datetime.now(),
            task=task
        )
        heapq.heappush(self.task_queue, scheduled)
        return True
    
    def find_best_provider(
        self,
        task: ComputeTask,
        providers: Dict[str, ComputeProvider]
    ) -> Optional[str]:
        """
        为任务寻找最优提供商
        
        策略:
        1. 满足算力需求
        2. 价格最优
        3. 延迟最低
        4. 信誉良好
        
        Returns:
            最佳提供商ID或None
        """
        candidates = []
        
        for provider_id, provider in providers.items():
            # 检查是否在线
            if provider.status != "online":
                continue
            
            # 检查算力是否满足
            if provider.compute_power < task.required_compute:
                continue
            
            # 检查显存是否满足
            if provider.vram_gb < task.required_vram:
                continue
            
            # 计算得分 (越低越好)
            # 价格权重40%, 延迟权重30%, 信誉权重30%
            price_score = provider.price_per_hour * 0.4
            latency_score = self._estimate_latency(provider.location) * 0.3
            reputation_score = (100 - provider.reputation) * 0.3
            
            total_score = price_score + latency_score + reputation_score
            
            candidates.append((total_score, provider_id))
        
        if not candidates:
            return None
        
        # 返回得分最低的（最优）
        candidates.sort()
        return candidates[0][1]
    
    def _estimate_latency(self, location: str) -> float:
        """估算延迟 (模拟)"""
        # 简化实现，实际应该根据真实网络测量
        latency_map = {
            "北京": 10, "上海": 15, "深圳": 20, "杭州": 15,
            "广州": 20, "成都": 25, "武汉": 20, "西安": 25
        }
        return latency_map.get(location, 30)
    
    async def schedule_loop(
        self,
        providers: Dict[str, ComputeProvider],
        assign_callback: callable
    ):
        """
        调度主循环
        
        Args:
            providers: 提供商列表
            assign_callback: 任务分配回调
        """
        while True:
            # 检查是否有等待任务
            if self.task_queue and len(self.running_tasks) < self.max_concurrent:
                scheduled = heapq.heappop(self.task_queue)
                task = scheduled.task
                
                # 寻找最佳提供商
                provider_id = self.find_best_provider(task, providers)
                
                if provider_id:
                    # 分配任务
                    task.status = TaskStatus.RUNNING
                    task.provider_id = provider_id
                    task.started_at = datetime.now()
                    
                    self.running_tasks[task.id] = task
                    
                    # 回调通知
                    await assign_callback(task, provider_id)
                    
                    # 记录历史
                    self.task_history.append({
                        "task_id": task.id,
                        "provider_id": provider_id,
                        "scheduled_at": datetime.now().isoformat(),
                        "priority": scheduled.priority
                    })
                else:
                    # 没有可用提供商，放回队列
                    heapq.heappush(self.task_queue, scheduled)
            
            # 清理已完成的任务
            completed = [
                task_id for task_id, task in self.running_tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]
            for task_id in completed:
                del self.running_tasks[task_id]
            
            await asyncio.sleep(1)
    
    def get_queue_status(self) -> Dict:
        """获取队列状态"""
        return {
            "waiting": len(self.task_queue),
            "running": len(self.running_tasks),
            "total_scheduled": len(self.task_history),
            "queue_by_priority": self._count_by_priority()
        }
    
    def _count_by_priority(self) -> Dict:
        """按优先级统计"""
        counts = {p.name: 0 for p in TaskPriority}
        for scheduled in self.task_queue:
            priority_name = TaskPriority(scheduled.priority).name
            counts[priority_name] += 1
        return counts


class DynamicPricing:
    """
    动态定价引擎
    
    根据供需关系自动调整价格
    """
    
    def __init__(self):
        self.base_prices = {
            ComputeType.GPU_H100: 45.0,
            ComputeType.GPU_A100: 25.0,
            ComputeType.GPU_RTX4090: 8.0,
            ComputeType.GPU_RTX3090: 5.0,
            ComputeType.CPU_HIGH: 3.0,
            ComputeType.CPU_STANDARD: 1.0
        }
        self.demand_history: List[Dict] = []
        self.price_adjustment_rate = 0.1  # 价格调整幅度
    
    def calculate_price(
        self,
        compute_type: ComputeType,
        current_utilization: float,
        queue_length: int
    ) -> float:
        """
        计算动态价格
        
        Args:
            compute_type: 算力类型
            current_utilization: 当前利用率 (0-1)
            queue_length: 队列长度
        
        Returns:
            调整后价格
        """
        base = self.base_prices.get(compute_type, 1.0)
        
        # 根据利用率调整
        if current_utilization > 0.8:
            # 高利用率，涨价
            multiplier = 1 + self.price_adjustment_rate
        elif current_utilization < 0.3:
            # 低利用率，降价吸引用户
            multiplier = 1 - self.price_adjustment_rate
        else:
            multiplier = 1.0
        
        # 根据队列长度调整
        if queue_length > 10:
            multiplier += 0.1
        elif queue_length > 50:
            multiplier += 0.2
        
        return round(base * multiplier, 2)
    
    def record_demand(self, compute_type: ComputeType, timestamp: datetime = None):
        """记录需求"""
        self.demand_history.append({
            "type": compute_type.value,
            "timestamp": (timestamp or datetime.now()).isoformat()
        })
    
    def get_price_trends(self, hours: int = 24) -> Dict:
        """获取价格趋势"""
        # 简化实现，实际应该聚合历史数据
        return {
            "period_hours": hours,
            "avg_prices": self.base_prices,
            "trend": "stable"
        }


class AutoScaler:
    """
    自动扩缩容管理
    
    根据负载自动调整提供商数量
    """
    
    def __init__(self):
        self.scale_up_threshold = 0.8   # 利用率超过80%扩容
        self.scale_down_threshold = 0.2 # 利用率低于20%缩容
        self.min_providers = 2
        self.max_providers = 100
    
    def should_scale_up(
        self,
        current_providers: int,
        avg_utilization: float,
        queue_length: int
    ) -> bool:
        """是否应该扩容"""
        if current_providers >= self.max_providers:
            return False
        
        return avg_utilization > self.scale_up_threshold or queue_length > 20
    
    def should_scale_down(
        self,
        current_providers: int,
        avg_utilization: float
    ) -> bool:
        """是否应该缩容"""
        if current_providers <= self.min_providers:
            return False
        
        return avg_utilization < self.scale_down_threshold
    
    def calculate_target_capacity(
        self,
        current_providers: int,
        avg_utilization: float,
        queue_length: int
    ) -> int:
        """计算目标容量"""
        if self.should_scale_up(current_providers, avg_utilization, queue_length):
            return min(current_providers + 2, self.max_providers)
        
        if self.should_scale_down(current_providers, avg_utilization):
            return max(current_providers - 1, self.min_providers)
        
        return current_providers


class MarketDashboard:
    """
    市场实时监控Dashboard
    
    提供聚合数据供前端展示
    """
    
    def __init__(self):
        self.metrics_history: List[Dict] = []
        self.max_history = 1000
    
    def record_metrics(
        self,
        providers: Dict[str, ComputeProvider],
        tasks: Dict[str, ComputeTask],
        scheduler: SmartScheduler
    ):
        """记录当前指标"""
        total_compute = sum(p.compute_power for p in providers.values())
        online_compute = sum(
            p.compute_power for p in providers.values()
            if p.status == "online"
        )
        
        running_tasks = sum(1 for t in tasks.values() if t.status == TaskStatus.RUNNING)
        completed_tasks = sum(1 for t in tasks.values() if t.status == TaskStatus.COMPLETED)
        
        queue_status = scheduler.get_queue_status()
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "providers": {
                "total": len(providers),
                "online": sum(1 for p in providers.values() if p.status == "online"),
                "total_compute": total_compute,
                "available_compute": online_compute,
                "utilization": (total_compute - online_compute) / total_compute if total_compute else 0
            },
            "tasks": {
                "total": len(tasks),
                "running": running_tasks,
                "completed": completed_tasks,
                "waiting": queue_status["waiting"]
            },
            "queue": queue_status
        }
        
        self.metrics_history.append(metrics)
        
        # 限制历史记录数量
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
    
    def get_current_metrics(self) -> Optional[Dict]:
        """获取当前指标"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, minutes: int = 60) -> List[Dict]:
        """获取历史指标"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
    
    def get_summary(self) -> Dict:
        """获取摘要统计"""
        if not self.metrics_history:
            return {}
        
        recent = self.metrics_history[-10:]  # 最近10个数据点
        
        return {
            "avg_utilization": sum(
                m["providers"]["utilization"] for m in recent
            ) / len(recent),
            "avg_queue_length": sum(
                m["queue"]["waiting"] for m in recent
            ) / len(recent),
            "total_tasks_processed": sum(
                m["tasks"]["completed"] for m in self.metrics_history
            )
        }


# 导出模块
__all__ = [
    'SmartScheduler',
    'TaskPriority',
    'DynamicPricing',
    'AutoScaler',
    'MarketDashboard'
]
