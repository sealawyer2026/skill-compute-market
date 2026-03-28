---
name: compute-market
description: Compute Market - Distributed computing power marketplace. GPU/CPU resource pooling, task scheduling, and revenue sharing for AI workloads.
---

# Token算力市场

分布式算力调度平台

## 功能

- ✅ 算力提供商注册 (GPU/CPU)
- ✅ 计算任务提交与调度
- ✅ 智能任务分配 (成本/性能/信誉)
- ✅ 收益分配 (提供商85% / 平台15%)
- ✅ 信誉系统
- ✅ 市场统计

## 使用

```bash
# 查看市场行情
python main.py market

# 注册算力提供商
python main.py register --user u001 --name "MyGPU" --type gpu_rtx4090 --price 2.5

# 提交计算任务
python main.py submit --user u002 --type inference --compute 10 --vram 8 --duration 5 --reward 5.0

# 查看任务列表
python main.py tasks

# 运行演示
python main.py demo
```

## 支持的算力类型

| 类型 | 名称 | 显存 | 算力值 | 参考价格 |
|------|------|------|--------|----------|
| gpu_rtx4090 | RTX 4090 | 24GB | 100 | ¥2.5/小时 |
| gpu_a100 | A100 | 80GB | 300 | ¥8.0/小时 |
| gpu_h100 | H100 | 80GB | 500 | ¥15.0/小时 |
| cpu_standard | Standard CPU | - | 20 | ¥0.5/小时 |

## 任务类型

- inference: 模型推理
- training: 模型训练
- fine_tuning: 微调训练
- embedding: 向量嵌入

## 调度策略

- cost_optimized: 成本优先 (默认)
- performance: 性能优先
- reputation: 信誉优先
- balanced: 均衡策略

## 费率

- 平台手续费: 15%
- 提供商收益: 85%
