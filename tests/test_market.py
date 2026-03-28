#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算力市场 - 测试套件
"""

import unittest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market import ComputeMarket, ComputeProvider, ComputeTask, TaskPriority, ProviderStatus, TaskStatus, get_compute_market


class TestComputeMarket(unittest.TestCase):
    """测试算力市场"""
    
    def setUp(self):
        """测试前准备"""
        self.market = get_compute_market()
    
    def test_register_provider(self):
        """测试注册提供商"""
        provider = self.market.register_provider(
            owner_id="u001",
            name="TestGPU",
            compute_type="gpu_rtx4090",
            price_per_hour=2.5
        )
        
        self.assertIsNotNone(provider.id)
        self.assertEqual(provider.name, "TestGPU")
        self.assertEqual(provider.compute_type, "gpu_rtx4090")
        self.assertEqual(provider.price_per_hour, 2.5)
        self.assertEqual(provider.status, ProviderStatus.ONLINE)
    
    def test_submit_task(self):
        """测试提交任务"""
        task = self.market.submit_task(
            user_id="u002",
            task_type="inference",
            required_compute=10,
            required_vram=8,
            estimated_duration=300,
            reward=5.0
        )
        
        self.assertIsNotNone(task.id)
        self.assertEqual(task.task_type, "inference")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.reward, 5.0)
    
    def test_task_priority(self):
        """测试任务优先级"""
        # 提交不同优先级的任务
        task_low = self.market.submit_task("u001", "test", 10, 8, 300, 5.0, TaskPriority.LOW)
        task_high = self.market.submit_task("u002", "test", 10, 8, 300, 5.0, TaskPriority.HIGH)
        task_normal = self.market.submit_task("u003", "test", 10, 8, 300, 5.0, TaskPriority.NORMAL)
        
        # 检查队列顺序 (高优先级在前)
        queue_ids = self.market.task_queue
        self.assertIn(task_high.id, queue_ids)
        self.assertIn(task_normal.id, queue_ids)
        self.assertIn(task_low.id, queue_ids)
    
    def test_get_market_stats(self):
        """测试获取市场统计"""
        # 添加测试数据
        self.market.register_provider("u001", "GPU1", "gpu_rtx4090", 2.5)
        self.market.submit_task("u002", "inference", 10, 8, 300, 5.0)
        
        stats = self.market.get_market_stats()
        
        self.assertIn("providers", stats)
        self.assertIn("compute_power", stats)
        self.assertIn("tasks", stats)
        self.assertIn("economy", stats)
        
        self.assertGreaterEqual(stats["providers"]["total"], 1)
        self.assertGreaterEqual(stats["tasks"]["total"], 1)
    
    def test_complete_task(self):
        """测试完成任务"""
        # 注册提供商
        provider = self.market.register_provider("u001", "GPU1", "gpu_rtx4090", 2.5)
        
        # 提交任务
        task = self.market.submit_task("u002", "inference", 10, 8, 300, 100.0)
        task.assigned_provider = provider.id
        
        # 完成任务
        result = self.market.complete_task(
            task_id=task.id,
            result_data="test result",
            actual_duration=300,
            success=True
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.task_id, task.id)
        
        # 检查提供商收益
        updated_provider = self.market.providers[provider.id]
        expected_earnings = 100.0 * 0.85  # 85%给提供商
        self.assertAlmostEqual(updated_provider.total_earnings, expected_earnings, places=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
