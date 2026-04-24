---
name: blucli
description: BluOS CLI (blu) 用于设备发现、播放控制、分组和音量调节。
homepage: https://blucli.sh
metadata:
  {
    "openclaw":
      {
        "emoji": "🫐",
        "requires": { "bins": ["blu"] },
        "install":
          [
            {
              "id": "go",
              "kind": "go",
              "module": "github.com/steipete/blucli/cmd/blu@latest",
              "bins": ["blu"],
              "label": "安装 blucli (go)",
            },
          ],
      },
  }
---

# blucli (blu)

使用 `blu` 控制 Bluesound/NAD 播放器。

快速开始

- `blu devices` (选择目标设备)
- `blu --device <id> status`
- `blu play|pause|stop`
- `blu volume set 15`

目标选择（按优先级顺序）

- `--device <id|name|alias>`
- `BLU_DEVICE`
- 配置默认值（如果已设置）

常用任务

- 分组：`blu group status|add|remove`
- TuneIn 搜索/播放：`blu tunein search "查询"`, `blu tunein play "查询"`

脚本建议使用 `--json` 格式。在更改播放前请确认目标设备。
