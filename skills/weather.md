---
name: weather
description: "获取地点或旅行规划的当前天气、降雨、温度和预报。"
homepage: https://wttr.in/:help
metadata:
  {
    "openclaw":
      {
        "emoji": "☔",
        "requires": { "bins": ["curl"] },
        "install":
          [
            {
              "id": "brew",
              "kind": "brew",
              "formula": "curl",
              "bins": ["curl"],
              "label": "安装 curl (brew)",
            },
          ],
      },
  }
---

# 天气技能

获取当前天气状况和预报。

## 何时使用

✅ **在以下情况下使用此技能：**

- "天气怎么样？"
- "今天/明天会下雨吗？"
- "[城市]的温度"
- "本周天气预报"
- 旅行规划天气检查

## 何时不使用

❌ **在以下情况下不要使用此技能：**

- 历史天气数据 → 使用天气档案/API
- 气候分析或趋势 → 使用专门的数据源
- 超局部微气候数据 → 使用本地传感器
- 恶劣天气警报 → 检查官方 NWS 来源
- 航空/海洋天气 → 使用专门的服务（METAR 等）

## 地点

在天气查询中始终包含城市、地区或机场代码。

## 命令

### 当前天气

```bash
# 单行摘要
curl "wttr.in/伦敦?format=3"

# 详细当前状况
curl "wttr.in/伦敦?0"

# 特定城市
curl "wttr.in/纽约?format=3"
```

### 预报

```bash
# 3 天预报
curl "wttr.in/伦敦"

# 本周预报
curl "wttr.in/伦敦?format=v2"

# 特定日期（0=今天，1=明天，2=后天）
curl "wttr.in/伦敦?1"
```

### 格式选项

```bash
# 单行
curl "wttr.in/伦敦?format=%l:+%c+%t+%w"

# JSON 输出
curl "wttr.in/伦敦?format=j1"

# PNG 图像
curl "wttr.in/伦敦.png"
```

### 格式代码

- `%c` — 天气状况表情符号
- `%t` — 温度
- `%f` — "体感温度"
- `%w` — 风速
- `%h` — 湿度
- `%p` — 降水量
- `%l` — 地点

## 快速响应

**"天气怎么样？"**

```bash
curl -s "wttr.in/伦敦?format=%l:+%c+%t+(体感+%f),+%w+风,+%h+湿度"
```

**"会下雨吗？"**

```bash
curl -s "wttr.in/伦敦?format=%l:+%c+%p"
```

**"周末预报"**

```bash
curl "wttr.in/伦敦?format=v2"
```

## 注意事项

- 不需要 API 密钥（使用 wttr.in）
- 受速率限制；不要发送过多请求
- 适用于大多数全球城市
- 支持机场代码：`curl wttr.in/ORD`
