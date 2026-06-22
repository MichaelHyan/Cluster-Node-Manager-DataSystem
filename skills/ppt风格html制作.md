---
name: ppt_style_html
description: "使用 Reveal.js 制作 PPT 风格网页"
---

## 技能概述
该技能指导如何利用 Reveal.js 框架，将文本大纲（如论文、演讲稿）快速转换为全屏、可翻页的 PPT 风格 HTML 网页。支持键盘/触屏导航、进度条、页码、背景渐变、卡片布局、代码高亮等功能。

## 适用场景
- 课程设计报告、结课展示
- 技术分享、项目路演
- 论文答辩幻灯片
- 任何需要快速制作逻辑清晰、视觉效果良好的在线演示场景

## 前置条件
- 了解 HTML、CSS 基础知识
- 准备一份结构化的内容大纲（如 Markdown 格式）
- 可选：准备一个参考风格的 HTML 文件（用于提取配色、布局等）

## 核心工具
- **Reveal.js**：开源 HTML 演示框架（CDN 引用）
- **Google Fonts**：用于中文字体优化（如 Noto Sans SC、Noto Serif SC）
- **Highlight.js**：代码高亮（可选）

## 制作流程

### 步骤 1：确定页面结构与内容
将你的内容大纲（如 PPT 大纲）拆分为若干张幻灯片，每张幻灯片对应一个 `<section>` 标签。通常包含：
- 封面页（cover slide）
- 目录页（TOC）
- 正文页（背景、方法、结果、总结等）
- 结束页（感谢、提问等）

### 步骤 2：搭建基础 HTML 骨架
创建一个 `.html` 文件，引入 Reveal.js 的 CSS 和 JS 资源（使用 CDN），并设置主题为 `white`（或自定义）。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>你的标题</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/theme/white.css">
    <!-- 引入 Google Fonts 优化中文 -->
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Noto+Serif+SC:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        /* 自定义样式 */
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            <!-- 每张幻灯片一个 <section> -->
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.js"></script>
    <script>
        Reveal.initialize({
            hash: true,
            slideNumber: 'c/t',
            progress: true,
            center: false,
            transition: 'slide',
            width: 1280,
            height: 720,
            margin: 0.04,
            keyboard: true,
            overview: true,
            touch: true
        });
    </script>
</body>
</html>
```

### 步骤 3：设计自定义 CSS 样式（参考风格）
根据你的内容品牌或参考文件，定义以下关键样式：
- **全局字体**：使用 `Noto Sans SC`（正文）和 `Noto Serif SC`（标题）
- **标题样式**：`h2` 添加下划线或彩色边框
- **卡片/高亮框**：使用 `.highlight-box`、`.key-point`、`.warning-box`、`.success-box` 等，利用 `linear-gradient` 背景和左侧边框
- **流程图**：使用 `.flow-chart` 和 `.flow-box` 实现横向步骤箭头
- **表格**：表头使用渐变色，隔行变色
- **代码块**：深色背景，区分关键词和注释
- **封底**：使用渐变色 `.cover-slide`

### 步骤 4：填充每张幻灯片的内容
每个 `<section>` 内部编写 HTML 内容：
- 文字段落 `<p>`、列表 `<ul>`、表格 `<table>`、代码块 `<pre><code>`
- 可嵌套 `.highlight-box`、`.two-column`、`.three-column` 等布局类
- 底部可添加 `.slide-number` 和 `.footer` 实现左侧主题名（可选）

### 步骤 5：增强分页功能（可选）
- 默认 Reveal.js 已支持键盘方向键、空格、PageUp/Down 翻页
- 可添加 `.slide-footer` 显示当前幻灯片主题名称
- 页码使用 `slideNumber: 'c/t'` 自动显示

### 步骤 6：测试与调整
在浏览器中打开 HTML 文件，检查：
- 所有页面能否正常显示
- 键盘/触摸翻页是否流畅
- 内容是否完整，无溢出
- 样式是否与参考风格一致

## 常用 CSS 类名模板
以下是一套可直接复用的样式类（可根据需要调整颜色）：

```css
:root {
    --r-main-font: 'Noto Sans SC', sans-serif;
    --r-heading-font: 'Noto Serif SC', serif;
    --r-main-color: #333;
    --r-heading-color: #1a1a2e;
    --r-link-color: #667eea;
    --r-primary: #667eea;
    --r-secondary: #764ba2;
}

.highlight-box {
    background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%);
    border-left: 4px solid var(--r-primary);
    border-radius: 0 12px 12px 0;
    padding: 18px 22px;
    margin: 15px 0;
}

.key-point {
    background: linear-gradient(135deg, rgba(102,126,234,0.2) 0%, rgba(118,75,162,0.2) 100%);
    border: 2px solid var(--r-primary);
    border-radius: 12px;
    padding: 15px 20px;
    margin: 12px 0;
}

.warning-box {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    border-radius: 0 12px 12px 0;
    padding: 18px 22px;
    margin: 15px 0;
}

.success-box {
    background: #d4edda;
    border-left: 4px solid #28a745;
    border-radius: 0 12px 12px 0;
    padding: 18px 22px;
    margin: 15px 0;
}

.cover-slide {
    background: linear-gradient(135deg, var(--r-primary) 0%, var(--r-secondary) 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}

.two-column { display: grid; grid-template-columns: 1fr 1fr; gap: 35px; }
.three-column { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }

.flow-chart { display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap; }
.flow-box { background: linear-gradient(135deg, var(--r-primary) 0%, var(--r-secondary) 100%); color: #fff; padding: 15px 22px; border-radius: 10px; }
```

## 注意事项
- 中文字体建议使用 `Noto Sans SC` 和 `Noto Serif SC`，确保在移动端和桌面端都能正常显示
- 避免幻灯片内内容过多导致溢出，合理使用 `.two-column` 分栏
- 代码块建议使用 Highlight.js 进行语法着色，需引入对应 CDN
- 如果需要保留原始 URL 哈希（如直接跳转到某页），启用 `hash: true`

## 示例参考
- 技能文档本身即使用本方法生成，可查阅 `./skills/` 下的 `skill.md`
- 也可查看 `./files/` 目录下的实际 HTML 输出文件

## 扩展
- 可将生成的 HTML 文件上传至 GitHub Pages、Vercel 等平台，实现在线分享
- 可结合 Markdown 转 HTML 工具（如 pandoc）批量生成幻灯片
- 可结合动画库（如 Animate.css）增加过渡效果

## 版本
- v1.0（2025-03-07）：初始版本