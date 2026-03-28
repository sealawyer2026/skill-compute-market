#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算力市场 - 分布式算力调度平台
Compute Market - Distributed Computing Power Marketplace

Token经济生态 Phase 3 - 战略级技能
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading


class ProviderStatus(Enum):
    """提供商状态"""
    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    SCHEDULING = "scheduling"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ComputeProvider:
    """算力提供商"""
    id: str
    name: str
    owner_id: str
    compute_type: str
    vram_gb: int
    compute_power: int
    price_per_hour: float
    status: ProviderStatus
    reputation_score: float
    total_tasks_completed: int
    total_earnings: float
    last_heartbeat: float
    location: str = ""


@dataclass
class ComputeTask:
    """计算任务"""
    id: str
    user_id: str
    task_type: str
    priority: TaskPriority
    required_compute: int
    required_vram: int
    estimated_duration: int
    reward: float
    status: TaskStatus
    created_at: float
    assigned_provider: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result_hash: Optional[str] = None


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    provider_id: str
    output_data: str
    actual_duration: int
    compute_used: int
    success: bool
    timestamp: float


class ComputeMarket:
    """算力市场"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化"""
        self.config = self._load_config(config_path)
        self.providers: Dict[str, ComputeProvider] = {}
        self.tasks: Dict[str, ComputeTask] = {}
        self.results: Dict[str, TaskResult] = {}
        self.task_queue: List[str] = []
        self.lock = threading.Lock()
        self.scheduler_running = False
        self.scheduler_thread = None
        
        self.platform_fee = self.config.get("market", {}).get("platform_fee", 0.15)
    
    def _load_config(self, path: str) -> Dict:
        """加载配置"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "market": {"platform_fee": 0.15},
            "scheduling": {"algorithm": "cost_optimized"}
        }
    
    def start_scheduler(self):
        """启动调度器"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        def schedule_loop():
            while self.scheduler_running:
                self._schedule_pending_tasks()
                time.sleep(5)
        
        self.scheduler_thread = threading.Thread(target=schedule_loop, daemon=True)
        self.scheduler_thread.start()
        print("✅ 算力调度器已启动")
    
    def stop_scheduler(self):
        """停止调度器"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("⏹️ 算力调度器已停止")
    
    def register_provider(self, owner_id: str, name: str, compute_type: str,
                         price_per_hour: float, location: str = "") -> ComputeProvider:
        """
        注册算力提供商
        
        Args:
            owner_id: 所有者ID
            name: 提供商名称
            compute_type: 算力类型 (gpu_rtx4090/gpu_a100等)
            price_per_hour: 每小时价格
            location: 地理位置
        
        Returns:
            ComputeProvider对象
        """
        # 获取算力类型配置
        compute_types = {t["id"]: t for t in self.config.get("compute_types", [])}
        type_config = compute_types.get(compute_type, {})
        
        provider = ComputeProvider(
            id=f"PRV{int(time.time())}{uuid.uuid4().hex[:6].upper()}",
            name=name,
            owner_id=owner_id,
            compute_type=compute_type,
            vram_gb=type_config.get("vram_gb", 0),
            compute_power=type_config.get("compute_power", 0),
            price_per_hour=price_per_hour,
            status=ProviderStatus.ONLINE,
            reputation_score=100.0,
            total_tasks_completed=0,
            total_earnings=0.0,
            last_heartbeat=time.time(),
            location=location
        )
        
        with self.lock:
            self.providers[provider.id] = provider
        
        return provider
    
    def submit_task(self, user_id: str, task_type: str, 
                   required_compute: int, required_vram: int,
                   estimated_duration: int, reward: float,
                   priority: TaskPriority = TaskPriority.NORMAL) -> ComputeTask:
        """
        提交计算任务
        
        Args:
            user_id: 用户ID
            task_type: 任务类型
            required_compute: 所需算力
            required_vram: 所需显存
            estimated_duration: 预估时长(秒)
            reward: 任务奖励
            priority: 优先级
        
        Returns:
            ComputeTask对象
        """
        task = ComputeTask(
            id=f"TSK{int(time.time())}{uuid.uuid4().hex[:6].upper()}",
            user_id=user_id,
            task_type=task_type,
            priority=priority,
            required_compute=required_compute,
            required_vram=required_vram,
            estimated_duration=estimated_duration,
            reward=reward,
            status=TaskStatus.PENDING,
            created_at=time.time()
        )
        
        with self.lock:
            self.tasks[task.id] = task
            # 按优先级插入队列
            insert_pos = len(self.task_queue)
            for i, tid in enumerate(self.task_queue):
                existing_task = self.tasks.get(tid)
                if existing_task and existing_task.priority.value < priority.value:
                    insert_pos = i
                    break
            self.task_queue.insert(insert_pos, task.id)
        
        return task
    
    def _schedule_pending_tasks(self):
        """调度待处理任务"""
        with self.lock:
            pending_tasks = [
                self.tasks[tid] for tid in self.task_queue
                if self.tasks[tid].status == TaskStatus.PENDING
            ]
            
            available_providers = [
                p for p in self.providers.values()
                if p.status == ProviderStatus.ONLINE
            ]
        
        for task in pending_tasks:
            # 寻找合适的提供商
            suitable_providers = [
                p for p in available_providers
                if p.compute_power >= task.required_compute
                and p.vram_gb >= task.required_vram
            ]
            
            if not suitable_providers:
                continue
            
            # 选择最优提供商 (成本优先)
            algorithm = self.config.get("scheduling", {}).get("algorithm", "cost_optimized")
            
            if algorithm == "cost_optimized":
                # 成本优先 - 选择价格最低的
                selected = min(suitable_providers, key=lambda p: p.price_per_hour)
            elif algorithm == "performance":
                # 性能优先 - 选择算力最强的
                selected = max(suitable_providers, key=lambda p: p.compute_power)
            elif algorithm == "reputation":
                # 信誉优先
                selected = max(suitable_providers, key=lambda p: p.reputation_score)
            else:
                # 均衡策略
                def score(p):
                    return (p.reputation_score / 100 * 0.4 + 
                           (1 / p.price_per_hour) * 0.3 +
                           (p.compute_power / 500) * 0.3)
                selected = max(suitable_providers, key=score)
            
            # 分配任务
            with self.lock:
                task.status = TaskStatus.SCHEDULING
                task.assigned_provider = selected.id
                selected.status = ProviderStatus.BUSY
            
            print(f"📋 任务 {task.id} 分配给提供商 {selected.name}")
    
    def start_task(self, task_id: str) -> ComputeTask:
        """
        开始执行任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            ComputeTask对象
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        return task
    
    def complete_task(self, task_id: str, result_data: str, 
                     actual_duration: int, success: bool = True) -> TaskResult:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result_data: 结果数据
            actual_duration: 实际执行时长
            success: 是否成功
        
        Returns:
            TaskResult对象
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        with self.lock:
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.completed_at = time.time()
            
            # 更新提供商状态
            provider = self.providers.get(task.assigned_provider)
            if provider:
                provider.status = ProviderStatus.ONLINE
                
                if success:
                    provider.total_tasks_completed += 1
                    # 计算收益
                    earnings = task.reward * (1 - self.platform_fee)
                    provider.total_earnings += earnings
                    provider.reputation_score = min(100, provider.reputation_score + 0.5)
            
            # 创建结果
            result = TaskResult(
                task_id=task_id,
                provider_id=task.assigned_provider,
                output_data=result_data,
                actual_duration=actual_duration,
                compute_used=task.required_compute * actual_duration // 3600,
                success=success,
                timestamp=time.time()
            )
            self.results[task_id] = result
        
        return result
    
    def get_market_stats(self) -> Dict:
        """获取市场统计"""
        total_providers = len(self.providers)
        online_providers = len([p for p in self.providers.values() if p.status == ProviderStatus.ONLINE])
        busy_providers = len([p for p in self.providers.values() if p.status == ProviderStatus.BUSY])
        
        total_compute = sum(p.compute_power for p in self.providers.values())
        available_compute = sum(p.compute_power for p in self.providers.values() if p.status == ProviderStatus.ONLINE)
        
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        pending_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        running_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        
        total_rewards = sum(t.reward for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        platform_revenue = total_rewards * self.platform_fee
        
        return {
            "providers": {
                "total": total_providers,
                "online": online_providers,
                "busy": busy_providers,
                "offline": total_providers - online_providers - busy_providers
            },
            "compute_power": {
                "total": total_compute,
                "available": available_compute,
                "utilization": round((total_compute - available_compute) / total_compute * 100, 1) if total_compute > 0 else 0
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "pending": pending_tasks,
                "running": running_tasks,
                "failed": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
            },
            "economy": {
                "total_rewards": round(total_rewards, 2),
                "platform_revenue": round(platform_revenue, 2),
                "provider_earnings": round(total_rewards - platform_revenue, 2)
            }
        }
    
    def get_provider_stats(self, provider_id: str) -> Optional[Dict]:
        """获取提供商统计"""
        provider = self.providers.get(provider_id)
        if not provider:
            return None
        
        completed_tasks = [t for t in self.tasks.values() 
                         if t.assigned_provider == provider_id and t.status == TaskStatus.COMPLETED]
        
        return {
            "id": provider.id,
            "name": provider.name,
            "compute_type": provider.compute_type,
            "status": provider.status.value,
            "reputation": round(provider.reputation_score, 1),
            "tasks_completed": provider.total_tasks_completed,
            "total_earnings": round(provider.total_earnings, 2),
            "hourly_rate": provider.price_per_hour,
            "uptime": "99.9%"  # 简化
        }


def get_compute_market(config_path: str = "config.json") -> ComputeMarket:
    """获取算力市场实例"""
    return ComputeMarket(config_path)
