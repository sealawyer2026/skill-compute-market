# Compute Market Skill

Token算力市场 - 去中心化GPU算力交易平台

## 功能

- 查询算力市场实时统计
- 查看算力提供商列表
- 注册成为算力提供商
- 提交计算任务
- 查看任务状态

## 使用示例

```bash
# 查看市场概况
compute-market stats

# 查看算力提供商列表
compute-market providers

# 注册成为提供商
compute-market register --name "My GPU" --type gpu_rtx4090 --price 2.5

# 提交计算任务
compute-market submit --type inference --compute 10 --reward 5.0

# 查看任务列表
compute-market tasks
```

## API端点

- Web平台: http://compute.token-master.cn
- API基础路径: /api/v1

## 定价

| 套餐 | 价格 | 功能 |
|------|------|------|
| 免费版 | ¥0 | 基础查询，限次调用 |
| 专业版 | ¥99/月 | 无限调用，优先处理 |
| 企业版 | ¥999/月 | 私有化部署，SLA保障 |

访问完整平台: http://token-master.cn/shop/
