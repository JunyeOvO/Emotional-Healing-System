# 电商智能导购 App — UI/UX 原型分析报告

> 分析时间: 2026-05-25
> 原型来源: Figma 导出 (8 张页面截图)
> 分析方法: Qwen3-VL-2B 视觉分析 + Tesseract OCR 文字提取
> 目标: 商业级前端开发说明书

---

## 页面总览

| # | 页面 | 文件名 | 类型 |
|:--:|------|--------|------|
| P1 | 每日首次登录主页 | 每日第一次登录时"主页面" | 推荐流 |
| P2 | 对话导购页 | "主页面"对话时页面 | AI Chat |
| P3 | 历史对话侧栏 | 历史对话页面 | Drawer |
| P4 | 个人中心 | "我的"页面主页面 | Profile |
| P5 | 探索发现页 | "探索"页面 | Discovery |
| P6 | 比价列表页 | "比价"页面主页面 | Compare Grid |
| P7 | 商品详情+价格跟踪 | 商品详细颜色套装价格跟踪页面 | Detail |
| P8 | 设置页 | "设置"页面主页面 | Settings |

---

## 一、页面用途分析

### P1 — 每日首次登录主页
- **解决问题**: 用户打开 App 不知道买什么 → 主动推送每日推荐
- **用户路径**: App 启动 → 判断当日首次访问 → 展示此页
- **主要操作**: 点击商品卡片查看详情
- **次要操作**: 顶栏菜单(历史)、底部导航切换

### P2 — 对话导购页 (核心)
- **解决问题**: 用户有购买意图但不知道具体买哪个 → AI 对话式导购
- **用户路径**: 输入需求 → AI 流式搜索 → 返回商品卡片 + 推荐理由
- **主要操作**: 文本输入框发送消息
- **次要操作**: 相机拍照搜、语音输入(长按)、点击商品卡片

### P3 — 历史对话侧栏
- **解决问题**: 用户想回顾之前的推荐结果
- **用户路径**: 主页 → 点左上角菜单图标 → 滑出历史 Drawer
- **主要操作**: 点击历史条目恢复对话
- **次要操作**: 搜索历史

### P4 — 个人中心
- **解决问题**: 管理订单、收藏、优惠券、购物车
- **用户路径**: 底部导航"我的"
- **主要操作**: 查看订单、领券
- **次要操作**: 设置、客服、购物车预览

### P5 — 探索发现页
- **解决问题**: 无明确购买意图时的浏览发现
- **用户路径**: 底部导航"探索"
- **主要操作**: 分类标签筛选、滚动浏览商品网格
- **次要操作**: 搜索框、附近好货定位

### P6 — 比价列表页
- **解决问题**: 快速比价，找到最低价
- **用户路径**: 底部导航"比价"
- **主要操作**: 分类切换、浏览价格排序商品
- **次要操作**: 搜索特定商品、点击进入价格跟踪

### P7 — 商品详情+价格跟踪
- **解决问题**: 了解商品详情 + 多平台价格历史
- **用户路径**: 比价页点击商品 → 进入此页
- **主要操作**: 查看价格走势图、切换颜色/规格
- **次要操作**: 查看各平台最低价

### P8 — 设置页
- **解决问题**: 账户管理、隐私配置、App 偏好
- **用户路径**: 我的 → 设置
- **主要操作**: 账号安全、支付、地址管理
- **次要操作**: 模式切换(标准/长辈/未成年)、皮肤切换、退出登录

---

## 二、页面结构分析

### P1 — 每日登录主页
```
┌──────────────────────────┐
│ 状态栏: 9:41  5G  WiFi  100% │
├──────────────────────────┤
│ ☰ 菜单    电话图标   静音图标  │
├──────────────────────────┤
│  "111111，早上好"          │
│  ┌──────────────────┐   │
│  │ 今日推荐 (粉色背景)  │   │
│  └──────────────────┘   │
│  ┌────────┐ ┌────────┐ │
│  │商品卡片1│ │商品卡片2│ │  2×2 Grid
│  │商品卡片3│ │商品卡片4│ │
│  └────────┘ └────────┘ │
│  [快捷] [推荐] [比价] [交流] │  功能按钮行
│  ┌──────────────────┐   │
│  │ 输入框…      📷 + │   │
│  └──────────────────┘   │
├──────────────────────────┤
│ 首页 │ 比价 │ 探索 │ 我的  │  底部导航
└──────────────────────────┘
```

### P2 — 对话导购页
```
┌──────────────────────────┐
│ 状态栏 + 导航栏            │
├──────────────────────────┤
│  用户气泡: "我想买一双...  │
│  左右，有推荐的吗"         │
│                          │
│  AI 回复:                │
│  "以下是为您推荐的结果:"    │
│  ┌──────────────────┐   │
│  │ 轻盈透气运动鞋      │   │
│  │ [商品图]          │   │
│  │ ¥135-156          │   │
│  │ 来源: xxx          │   │
│  └──────────────────┘   │
│  "正在搜索中…"  + 动画    │  流式状态
│                          │
│  [快捷] [推荐] [比价] [交流] │
│  ┌──────────────────┐   │
│  │ 输入框…      📷 + │   │
│  └──────────────────┘   │
└──────────────────────────┘
```

### P3 — 历史对话侧栏
```
┌──────────────────────────┐
│ 9:41         ☰     >   │
├──────────────────────────┤
│  ┌──────────────────┐   │
│  │ 🔍 搜索...      ✏️ │   │
│  └──────────────────┘   │
│                          │
│  2026年1月               │
│  ├ 推荐一顶帽子      >   │
│                          │
│  2025年12月              │
│  ├ 给妈妈挑选礼物    >   │
│                          │
│  2025年8月               │
│  ├ 如何买到好价手机  >   │
│                          │
│  ┌──────────────────┐   │
│  │ 商品推荐区(右侧)    │   │
│  │ 帽子 ¥59         │   │
│  │ 耳机 ¥199        │   │
│  └──────────────────┘   │
├──────────────────────────┤
│ 首页 │         │ 比价 多 │
└──────────────────────────┘
```

### P4 — 个人中心
```
┌──────────────────────────┐
│ 状态栏 + [官方客服] [设置] │
│ 🧑 fujunye              │
├──────────────────────────┤
│ ┌──购物车────────────────┐│
│ │轻盈跑步鞋 ¥299        ││
│ │缓震运动鞋 ¥359        ││
│ │运动中筒袜 ¥39         ││
│ │运动健身包 ¥159        ││
│ └───────────────────────┘│
│ ┌──我的订单────── [全部>]┐│
│ │待付款│待发货│收货│待评价││
│ └───────────────────────┘│
│ ┌──足迹─────────────────┐│
│ │收藏 15件 │关注店铺 6家 ││
│ └───────────────────────┘│
│ ┌──领券中心── [更多优惠>]─┐│
│ │+260│+300│¥25│¥105   ││
│ │减消费│鞋服│通用│通用券包││
│ └───────────────────────┘│
├──────────────────────────┤
│ 比价 │ 探索              │
└──────────────────────────┘
```

### P5 — 探索页
```
┌──────────────────────────┐
│ 9:41                     │
│ "探索"                    │
├──────────────────────────┤
│ ┌──────────────┐ [搜索]  │
│ │📷 搜索想探索的好物  │   │
│ └──────────────┘         │
│ [推荐][运动鞋][袜子][包袋] │  分类标签行
│ [数码][随机]              │
│                          │
│ ┌──────┐┌──────┐┌──────┐│  3列 Grid
│ │安踏  ││特步  ││特步  ││
│ │¥329 ││¥359 ││¥49  ││
│ ├──────┤├──────┤├──────┤│
│ │匹克  ││李宁  ││耐克  ││
│ │¥579 ││¥498 ││¥159 ││
│ └──────┘└──────┘└──────┘│
│                          │
│ "附近好货"  定位图标       │
│ [更多商品 grid...]        │
├──────────────────────────┤
│ 首页│比价│探索│我的        │
└──────────────────────────┘
```

### P6 — 比价页
```
┌──────────────────────────┐
│ 9:41        5G       >  │
│ ┌──────────────┐ [搜索]  │
│ │📷 搜索运动商品    │   │
│ └──────────────┘         │
│ [推荐][零食][男装][运动]   │
│ [数码家电][三分类]         │
│                          │
│ ┌────────┐┌────────┐    │  2列 Grid
│ │运动鞋黄 ││运动鞋白 │    │
│ │¥319    ││¥299    │    │
│ │21万人付││16万人付 │    │
│ ├────────┤├────────┤    │
│ │运动中筒││篮球鞋  │    │
│ │¥19.9  ││¥429   │    │
│ └────────┘└────────┘    │
├──────────────────────────┤
│ 首页│比价│探索│我的        │
└──────────────────────────┘
```

### P7 — 商品详情+价格跟踪
```
┌──────────────────────────┐
│ < 返回                     │
│ ┌──────────────┐ [搜索]  │
│ │搜索商品名称或粘贴链接│   │
│ └──────────────┘         │
├──────────────────────────┤
│ 颜色选择(黄色/白色)        │
│                          │
│ ┌────────┐┌────────┐    │
│ │疾风轻跑 ││透气轻跑 │    │
│ │运动鞋黄 ││鞋 白色  │    │
│ │¥319    ││¥299    │    │
│ │透气网面││减震回弹 │    │
│ └────────┘└────────┘    │
│                          │
│ 价格走势图(折线图 ×4平台)  │
│ ┌──────────────────────┐ │
│ │ ¥400                 │ │
│ │ ¥320  ╱╲    ╱╲      │ │
│ │ ¥240 ╱  ╲╲╱  ╲     │ │
│ │   30天前 15天前 今天  │ │
│ │最低价来源: 抖音 ¥299  │ │
│ └──────────────────────┘ │
│ (同样图表 ×3 其他平台)    │
├──────────────────────────┤
│ 首页│比价│探索│我的        │
└──────────────────────────┘
```

### P8 — 设置页
```
┌──────────────────────────┐
│ < 返回    设置    🔔10  ⋮ │
├──────────────────────────┤
│ ┌──账号与安全────────────┐│
│ │🛡 收货地址            ││
│ │   账号与安全           ││
│ │   支付设置            ││
│ │   国家与地区           ││
│ └───────────────────────┘│
│ ┌──功能─────────────────┐│
│ │   隐私设置            ││
│ │   模式切换  标准/长辈> ││
│ │   个性皮肤            ││
│ │   有新版本可升级 © >  ││
│ └───────────────────────┘│
│ ┌──关于─────────────────┐│
│ │   商家入驻            ││
│ │   帮助与反馈           ││
│ │   关于拾物            ││
│ │   《个人信息共享清单》  ││
│ │   《个人信息收集清单》  ││
│ └───────────────────────┘│
│ [切换账号]   [退出登录]    │
└──────────────────────────┘
```

---

## 三、组件拆分表

### 3.1 全局组件

| 组件名 | 职责 | Props | 内部状态 | 复用场景 | Storybook |
|--------|------|-------|---------|---------|:---:|
| **StatusBar** | 系统状态栏 (时间/网络/电量) | — | — | 所有页面 | ❌ |
| **TopNavBar** | 顶部导航 (菜单/电话/静音) | onMenuClick, onCallClick, onMuteClick | — | P1/P2 | ✅ |
| **BottomNavBar** | 4 Tab 底部导航 | currentTab, onTabChange | selectedIndex | 所有页面 | ✅ |
| **GradientBackground** | 渐变背景容器 | colors: List<Color> | — | 全项目 | ❌ |
| **SearchBar** | 统一搜索栏 | placeholder, onSearch, leadingIcon, showCameraIcon | text, isFocused | P3/P5/P6/P7 | ✅ |

### 3.2 商品相关组件

| 组件名 | 职责 | Props | 内部状态 | 复用场景 | Storybook |
|--------|------|-------|---------|---------|:---:|
| **ProductCard** | 商品卡片 (垂直) | product: Product, onTap, variant: 'grid'\|'list' | — | P1/P5/P6 | ✅ |
| **ProductCardCompact** | 紧凑商品卡 (比价列表) | product, showSales, onTap | — | P6 | ✅ |
| **ProductCardHorizontal** | 横向商品卡片 (对话嵌入) | product, matchReason, onTap | — | P2 (对话流) | ✅ |
| **ProductDetailCard** | 商品详情卡片 | product, colorVariants, onColorSelect | selectedColor | P7 | ✅ |
| **PriceTrendChart** | 价格走势折线图 | priceHistory: List<PricePoint>, platformName | — | P7 | ✅ |
| **ProductSourceTag** | 来源标签 | sourceName, sourceIcon | — | P1/P2/P5 | ❌ |

### 3.3 对话相关组件

| 组件名 | 职责 | Props | 内部状态 | 复用场景 | Storybook |
|--------|------|-------|---------|---------|:---:|
| **MessageBubble** | 聊天气泡 | message: Message, isStreaming: bool | — | P2 | ✅ |
| **StreamingText** | 流式文字渲染 | text: String, isActive: bool | cursorVisible | P2 | ✅ |
| **ChatInputBar** | 输入栏 | onSend, onCamera, onVoice, onAttachment | text, isRecording | P1/P2 | ✅ |
| **QuickActionChips** | 快捷功能按钮行 | actions: List<QuickAction> | — | P1/P2 | ✅ |
| **HistoryDrawer** | 历史对话侧栏 | conversations, onSelect, onSearch | isOpen, searchQuery | P3 | ✅ |
| **HistoryItem** | 历史对话条目 | conversation: Conversation | — | P3 | ❌ |

### 3.4 个人中心组件

| 组件名 | 职责 | Props | 内部状态 | 复用场景 | Storybook |
|--------|------|-------|---------|---------|:---:|
| **UserProfileHeader** | 用户头像+昵称区 | user: User, onSettings, onCustomerService | — | P4 | ✅ |
| **CartPreview** | 购物车预览卡片 | cartItems, onViewAll | — | P4 | ✅ |
| **OrderStatusBar** | 订单状态栏 | orderCounts: OrderCounts | — | P4 | ✅ |
| **CouponCenter** | 领券中心卡片 | coupons, onClaim | — | P4 | ✅ |
| **SettingsGroup** | 设置分组列表 | title, icon, items: List<SettingItem> | — | P8 | ✅ |
| **SettingItem** | 单条设置项 | label, value, type: 'navigate'\|'toggle'\|'info' | P8 | ✅ |

### 3.5 浏览/比价组件

| 组件名 | 职责 | Props | 内部状态 | 复用场景 | Storybook |
|--------|------|-------|---------|---------|:---:|
| **CategoryTabs** | 分类标签横向滚动 | categories, selected, onSelect | scrollOffset | P5/P6/P7 | ✅ |
| **ProductGrid** | 商品网格布局 | products, columns, onProductTap, onLoadMore | — | P5/P6 | ✅ |
| **NearbyGoods** | 附近好货定位推荐 | location, products | — | P5 | ❌ |
| **ColorVariantPicker** | 颜色规格选择器 | variants, selected, onSelect | — | P7 | ✅ |

---

## 四、视觉规则

### 4.1 色彩系统

```
主色 (Primary):
  - 品牌红: #FF4757 (搜索按钮、底导选中、价格)
  - 品牌红深: #E03440 (按压态)

辅助色 (Secondary):
  - 粉色: #FFE4E8 (今日推荐背景)
  - 蓝色: #4A90D9 (设置盾牌图标、链接)
  - 绿色: #2ECC71 (价格下降指示)

中性色:
  - 背景: #F5F5F5 (页面底色)
  - 卡片: #FFFFFF (卡片/气泡背景)
  - 分割线: #EEEEEE
  - 文字主: #1A1A1A (标题/正文)
  - 文字辅: #8E8E93 (次要信息/付款人数)
  - 文字弱: #C7C7CC (占位符)

功能色:
  - 价格: #FF4757 (红色加粗)
  - 来源标签: #FF9500 (橙色)
  - 评分星: #FFD700 (金色)
  - 销量: #8E8E93 (灰色小字)
```

### 4.2 字号层级

```
显示大标题:  28sp Bold    (页面标题 "探索"/"设置")
标题1:      20sp SemiBold (卡片标题/商品名)
标题2:      18sp Medium   (对话气泡标题)
正文:       16sp Regular  (对话内容/列表项)
正文小:     14sp Regular  (辅助信息/来源)
价格大:     20sp Bold     (¥319, 红色)
价格小:     16sp Bold     (¥135-156)
说明文字:   12sp Regular  (付款人数/标签)
```

### 4.3 圆角规则

```
卡片:      12dp
按钮:      24dp (胶囊形)
输入框:    24dp (胶囊形)
标签Chip:  16dp (半圆角)
图片:      8dp (商品图)
气泡:      16dp (对话气泡, 一角4dp尖角)
底部导航:  0dp (直角)
```

### 4.4 间距规则

```
页面边距:    16dp (左右)
卡片间距:    12dp (Grid gap)
组件内边距:  12dp
列表项间距:  8dp
Section间距: 24dp
底部安全区:  根据设备
```

### 4.5 阴影规则

```
卡片阴影:  elevation 2dp, #000 8% alpha
浮层阴影:  elevation 8dp, #000 15% alpha
按钮阴影:  elevation 1dp, #000 5% alpha
```

### 4.6 组件样式规范

**商品卡片 (Grid)**:
- 宽: (屏幕宽-48dp)/2 (2列), (屏幕宽-64dp)/3 (3列)
- 高: 自适应, min 240dp
- 图片: 1:1 比例, 圆角8dp
- 名称: 2行截断, 16sp Medium
- 价格: 红色 #FF4757, 20sp Bold
- 付款人数: 灰色 #8E8E93, 12sp

**商品卡片 (对话嵌入)**:
- 宽: 屏幕宽-32dp (全宽)
- 高: 120dp
- 图片: 100×100dp 左侧
- 布局: 水平 (图左 + 信息右)
- 匹配理由: 绿色标签, 12sp

**输入框**:
- 高: 48dp, 圆角24dp
- 背景: #F0F0F0
- 占位符: "点击发送或长按说话…" #C7C7CC

**按钮 (搜索)**:
- 圆角24dp
- 背景: 品牌红 #FF4757
- 文字: 白色 16sp Medium
- 内边距: 水平24dp, 垂直12dp

**底部导航栏**:
- 高: 56dp + 安全区
- 4个Tab等宽
- 选中: 品牌红图标+文字
- 未选中: #8E8E93 图标+文字
- 文字: 10sp

---

## 五、交互规则

### 5.1 点击行为
- **商品卡片**: 点击 → 进入商品详情(P7)/弹出底部详情
- **搜索按钮**: 点击 → 跳转搜索/对话页并发送查询
- **分类标签**: 点击 → 切换分类 + 刷新商品列表
- **历史条目**: 点击 → 恢复对话 + 关闭抽屉
- **快捷功能按钮**: 点击 → 切换功能模式
- **设置项**: 点击 → 导航到子页面/弹出选择器
- **领券**: 点击 → 领取 + Toast反馈 + 动画

### 5.2 长按行为
- **商品卡片**: 长按 → 弹出快捷菜单 (收藏/分享/加购)
- **消息气泡**: 长按 → 复制文字
- **输入框语音按钮**: 长按 → 开始录音, 松开发送

### 5.3 滑动行为
- **商品网格**: 上下滑动 → 滚动加载更多
- **分类标签行**: 左右滑动 → 滚动更多分类
- **历史抽屉**: 左滑边缘 → 关闭抽屉
- **商品详情页**: 左滑 → 返回上一页
- **对话列表**: 上滑 → 加载历史消息

### 5.4 下拉行为
- **商品列表**: 下拉 → 刷新 (Pull-to-Refresh)
- **对话列表**: 下拉 → 加载更早消息

### 5.5 AI 流式回答 (核心交互)
```
1. 用户发送消息 → 消息气泡立即显示(带发送中动画)
2. SSE text_delta 到达:
   - 显示新AI气泡
   - 逐字追加文字 + 闪烁光标 "▌"
   - 搜索状态提示: "正在搜索中…" + 旋转动画
3. SSE product_cards 到达:
   - 文字下方插入商品卡片(渐入动画)
   - 显示价格+来源+匹配理由
4. SSE done:
   - 光标消失, 消息固化
   - 反馈按钮出现 (有帮助/无帮助)
```

### 5.6 图片上传行为
- **点相机图标** → 底部弹出选择器:
  - "拍照" → 调用系统相机
  - "从相册选择" → 系统图片选择器
  - 选择后 → 预览 → 确认上传或重选
- **上传中**: 缩略图+进度条
- **上传完成**: 图片消息气泡 → 触发 AI 图片搜索

### 5.7 语音输入行为 (原型暗示)
- **长按麦克风按钮** → 开始录音:
  - 按钮变红, 波形动画
  - 手指上滑 → 取消发送
  - 松手 → 语音转文字 → 填入输入框 → 自动发送

### 5.8 异常状态反馈
- **网络断开**: 顶部横幅 "网络连接已断开"
- **发送失败**: 消息气泡显示红色感叹号 + "重试"按钮
- **搜索无结果**: 空状态插图 + "未找到相关商品, 试试其他关键词"
- **加载超时**: "加载超时, 请重试" + 重试按钮
- **语音识别失败**: Toast "未识别到语音, 请重试"
- **图片上传失败**: Toast "图片上传失败, 请重试"

---

## 六、工程落地

### 6.1 推荐目录结构
```
src/
├── app/
│   ├── MainActivity.kt              # 入口
│   └── ShoppingApp.kt               # Application
│
├── ui/
│   ├── theme/
│   │   ├── Color.kt                 # 品牌色板
│   │   ├── Type.kt                  # 字体层级
│   │   ├── Shape.kt                 # 圆角/阴影
│   │   └── Theme.kt                 # Material3 主题
│   │
│   ├── navigation/
│   │   ├── NavGraph.kt              # 路由图
│   │   └── Screen.kt                # 路由枚举
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── TopNavBar.kt
│   │   │   ├── BottomNavBar.kt
│   │   │   ├── SearchBar.kt
│   │   │   ├── GradientBackground.kt
│   │   │   ├── LoadingStates.kt
│   │   │   └── CategoryTabs.kt
│   │   ├── product/
│   │   │   ├── ProductCard.kt
│   │   │   ├── ProductCardCompact.kt
│   │   │   ├── ProductCardHorizontal.kt
│   │   │   ├── ProductDetailCard.kt
│   │   │   ├── ProductGrid.kt
│   │   │   ├── PriceTrendChart.kt
│   │   │   └── ColorVariantPicker.kt
│   │   ├── chat/
│   │   │   ├── MessageBubble.kt
│   │   │   ├── StreamingText.kt
│   │   │   ├── ChatInputBar.kt
│   │   │   ├── QuickActionChips.kt
│   │   │   ├── HistoryDrawer.kt
│   │   │   └── HistoryItem.kt
│   │   └── profile/
│   │       ├── UserProfileHeader.kt
│   │       ├── CartPreview.kt
│   │       ├── OrderStatusBar.kt
│   │       ├── CouponCenter.kt
│   │       ├── SettingsGroup.kt
│   │       └── SettingItem.kt
│   │
│   └── screens/
│       ├── HomeScreen.kt            # P1/P7 每日推荐主页
│       ├── ChatScreen.kt            # P2 对话导购页
│       ├── ExploreScreen.kt         # P5 探索发现页
│       ├── CompareScreen.kt         # P6 比价列表页
│       ├── ProductDetailScreen.kt   # P7 商品详情+价格跟踪
│       ├── ProfileScreen.kt         # P4 个人中心
│       ├── SettingsScreen.kt        # P8 设置页
│       └── HistoryScreen.kt         # P3 历史对话(可作Drawer)
│
├── data/
│   ├── model/
│   │   ├── Product.kt
│   │   ├── Message.kt
│   │   ├── User.kt
│   │   ├── Order.kt
│   │   ├── Coupon.kt
│   │   ├── Conversation.kt
│   │   └── PriceHistory.kt
│   ├── remote/
│   │   ├── ApiClient.kt
│   │   ├── ApiService.kt
│   │   └── SseClient.kt
│   ├── repository/
│   │   ├── ChatRepository.kt
│   │   ├── ProductRepository.kt
│   │   └── UserRepository.kt
│   └── mock/
│       ├── MockProducts.kt
│       ├── MockChats.kt
│       ├── MockUser.kt
│       └── MockPriceHistory.kt
│
└── viewmodel/
    ├── ChatViewModel.kt
    ├── ProductViewModel.kt
    ├── ExploreViewModel.kt
    ├── CompareViewModel.kt
    ├── ProfileViewModel.kt
    └── SettingsViewModel.kt
```

### 6.2 推荐 TypeScript/Kotlin 类型定义

```kotlin
// Product.kt
data class Product(
    val id: String,
    val name: String,
    val price: Double,
    val originalPrice: Double?,
    val imageUrl: String,
    val category: String,
    val brand: String?,
    val source: String,           // 来源平台: "京东"/"天猫"/"抖音"
    val salesCount: Int?,         // 销量: 210000
    val rating: Float?,           // 评分 1-5
    val matchReason: String?,     // AI匹配理由
    val colorVariants: List<ColorVariant>?,
    val attributes: Map<String, String>,
)

data class ColorVariant(
    val color: String,
    val imageUrl: String,
    val price: Double,
)

// Message.kt
data class Message(
    val id: String,
    val role: MessageRole,        // USER / ASSISTANT / SYSTEM
    val content: String,
    val productCards: List<Product>?,  // 嵌入的商品卡片
    val timestamp: Long,
    val status: MessageStatus,    // SENDING / SENT / STREAMING / ERROR
)

enum class MessageRole { USER, ASSISTANT, SYSTEM }
enum class MessageStatus { SENDING, SENT, STREAMING, ERROR }

// Conversation.kt
data class Conversation(
    val id: String,
    val title: String,
    val preview: String,
    val date: String,             // "2026年1月"
    val messages: List<Message>,
)

// PriceHistory.kt
data class PricePoint(
    val date: String,             // "30天前"
    val price: Double,
)
data class PlatformPriceHistory(
    val platform: String,         // "抖音商城"
    val lowestPrice: Double,
    val history: List<PricePoint>,
)

// User.kt
data class User(
    val id: String,
    val nickname: String,
    val avatarUrl: String,
)

// Order.kt
data class OrderCounts(
    val pendingPayment: Int,
    val pendingShipment: Int,
    val pendingReceipt: Int,
    val pendingReview: Int,
)

// Coupon.kt
data class Coupon(
    val id: String,
    val amount: String,           // "+260"
    val label: String,            // "减消费"
    val isClaimed: Boolean,
)

// SSE Event
sealed class SSEEvent {
    data class TextDelta(val delta: String, val content: String) : SSEEvent()
    data class ProductCards(val cards: List<Product>) : SSEEvent()
    data class Done(val sessionId: String) : SSEEvent()
    data class Error(val code: String, val message: String) : SSEEvent()
}
```

### 6.3 Mock 数据示例

```kotlin
// MockProducts.kt
val mockProducts = listOf(
    Product(
        id = "p001",
        name = "轻盈透气运动鞋",
        price = 319.0,
        originalPrice = 499.0,
        imageUrl = "https://example.com/shoe1.jpg",
        category = "运动鞋",
        brand = "安踏",
        source = "天猫旗舰店",
        salesCount = 21000,
        rating = 4.8f,
        matchReason = "透气网面设计，适合夏季运动，价格在预算范围内",
        colorVariants = listOf(
            ColorVariant("黄色", "https://...", 319.0),
            ColorVariant("白色", "https://...", 299.0),
        ),
        attributes = mapOf(
            "材质" to "透气网面",
            "功能" to "减震回弹",
            "适用" to "跑步/日常",
        ),
    ),
    // ... more products
)

val mockPriceHistory = listOf(
    PlatformPriceHistory(
        platform = "抖音商城",
        lowestPrice = 299.0,
        history = listOf(
            PricePoint("30天前", 399.0),
            PricePoint("15天前", 349.0),
            PricePoint("今天", 299.0),
        ),
    ),
    PlatformPriceHistory(
        platform = "天猫",
        lowestPrice = 309.0,
        history = listOf(
            PricePoint("30天前", 420.0),
            PricePoint("15天前", 340.0),
            PricePoint("今天", 309.0),
        ),
    ),
    PlatformPriceHistory(
        platform = "京东",
        lowestPrice = 329.0,
        history = listOf(
            PricePoint("30天前", 420.0),
            PricePoint("15天前", 340.0),
            PricePoint("今天", 329.0),
        ),
    ),
)
```

### 6.4 API 端点设计

```
POST   /api/chat              # SSE流式对话 (text_delta + product_cards + done)
GET    /api/products           # 商品列表 (?category=&page=&size=)
GET    /api/products/:id       # 商品详情
GET    /api/products/:id/price-history  # 价格历史 (?days=30)
POST   /api/compare            # 商品对比 (body: {product_ids: [...]})
POST   /api/upload/image       # 图片上传搜商品
GET    /api/conversations      # 历史对话列表
GET    /api/conversations/:id  # 对话详情
GET    /api/user/profile       # 用户信息
GET    /api/user/orders        # 订单列表
GET    /api/user/coupons       # 优惠券列表
POST   /api/user/coupons/:id/claim  # 领取优惠券
POST   /api/feedback           # 反馈 (helpful/not)
```

### 6.5 推荐测试点

```
□ 组件渲染测试:
  - ProductCard 各variant渲染正常
  - MessageBubble user/assistant样式正确
  - PriceTrendChart 数据映射正确

□ 交互测试:
  - 底部导航Tab切换正常
  - 分类标签点击切换+高亮
  - 搜索框输入+搜索触发
  - 历史Drawer滑出/关闭

□ 状态测试:
  - Loading状态显示骨架屏
  - Empty状态显示空状态图
  - Error状态显示重试按钮
  - Streaming状态显示光标动画

□ API集成测试:
  - SSE text_delta 逐字追加
  - SSE product_cards 卡片渲染
  - SSE done 消息固化
  - 断线重连

□ 性能测试:
  - 商品Grid滚动60fps
  - 对话列表100条消息不卡顿
  - 图片加载不阻塞UI
```

---

## 七、还原优先级

### P0 — 必须高度还原 (核心体验)
| 元素 | 原因 |
|------|------|
| **对话流式渲染** | 核心差异化, 逐字+商品卡片嵌入 |
| **商品卡片样式** | 红色价格+来源标签+匹配理由, 品牌识别 |
| **底部4Tab导航** | 用户心智模型基础 |
| **输入栏 (文本+相机+语音)** | 主要操作入口 |
| **AI搜索状态提示** | "正在搜索中…"给用户反馈 |
| **比价网格布局** | 核心功能, 价格+销量信息层级 |
| **品牌红色系** | #FF4757主色调, 统一品牌感知 |

### P1 — 建议还原 (体验完善)
| 元素 | 原因 |
|------|------|
| 每日登录问候 + 今日推荐 | 提升留存, 但非核心功能 |
| 价格走势折线图 | 比价核心, 但可用简易版 |
| 历史对话侧栏 | 用户价值高, 但可延后 |
| 分类标签横向滚动 | 浏览体验, 标准交互 |
| 领券中心 | 电商标配, 可Mock |
| 颜色/规格选择器 | 商品详情必要, 但可用简单版 |

### P2 — 可以优化
| 元素 | 原因 |
|------|------|
| 附近好货 (LBS) | 加分项, 需定位权限 |
| 交流论坛入口 | 社区功能, 非MVP必需 |
| 个性皮肤切换 | 视觉增强, 非功能需求 |
| 长辈/未成年模式 | 合规项, 可延后 |
| 语音输入完整流程 | 加分项, 需ASR集成 |

### P3 — 可以删减
| 元素 | 原因 |
|------|------|
| 多平台价格跟踪图表 (4个) | 可简化为1个主平台 |
| "快捷"功能按钮行 | 功能重叠, 可合并到输入栏 |
| 电话/静音图标 | 电商App中意义不明 |
| 足迹收藏数 | 静态信息, 无交互价值 |

---

## 八、优化建议

### 8.1 信息层级问题
- **问题**: P4 个人中心塞了太多信息 (购物车+订单+收藏+领券)，视觉密度过高
- **建议**: 购物车独立为一个Tab, 个人中心只保留订单+设置+领券

### 8.2 商品卡片密度
- **问题**: P5 探索页3列Grid在375px宽屏幕上, 单卡宽度约110px, 过密
- **建议**: 改为2列, 卡片信息更完整; 或3列但仅显示图+价, 点开看详情

### 8.3 价格突出度
- **问题**: P6 比价页的价格已为红色, 但与付款人数同级, 视觉权重不够
- **建议**: 价格字号加大至22sp, 付款人数缩小至11sp, 形成 3:1 视觉权重比

### 8.4 输入入口不统一
- **问题**: 多个页面都有搜索框, 但样式不完全一致 (有的带相机图标, 有的不带)
- **建议**: 统一为 SearchBar 组件, 统一透传 placeholder/leadingIcon/onSearch

### 8.5 视觉风格稳定性
- **问题**: 首页用粉色背景的"今日推荐", 其他页面无此风格, 跳跃感强
- **建议**: 统一品牌色(#FF4757)作为强调色, 粉色仅作点缀; 所有页面使用统一渐变背景

### 8.6 触控区域过小
- **问题**: P5 3列Grid时卡片过小, 手指误触风险高; 分类标签间距过窄
- **建议**: 最小触控区域 44×44dp (iOS HIG) / 48×48dp (Material), 标签间距≥8dp

### 8.7 缺少空/错状态
- **问题**: 原型图中所有页面都是"理想状态", 无空数据/加载/错误状态
- **建议**: 为每个列表页设计 Empty/Loading/Error 三态, P0 交付

### 8.8 缺少手势反馈
- **问题**: 原型未体现点击态/按压态/禁用态
- **建议**: 所有可交互元素必须有 Pressed (scale 0.97 + alpha 0.8), Disabled (gray) 状态

### 8.9 底部导航图标语义
- **问题**: P4 底部导航只显示 "比价 | 探索" (2个), 与其他页面4Tab不一致
- **建议**: 统一为 首页 | 对话 | 探索 | 我的 4Tab, 全局一致

### 8.10 设置页功能膨胀
- **问题**: P8 设置页将"账号与安全"/"功能"/"关于"三大类塞在一个ScrollView
- **建议**: 拆分为子页面, 设置主页只显示分类入口 (iOS Settings风格)

---

## 九、前端开发任务清单

以下任务按 P0→P3 排列, 可直接委派给 Claude Code 执行。

### Sprint 0: 项目地基 (1h)

```
□ T0.1  创建 Compose 项目骨架, 配置 Material3 主题
□ T0.2  实现 Color.kt / Type.kt / Theme.kt 品牌色板
□ T0.3  实现 BottomNavBar (4 Tab: 首页/对话/探索/我的)
□ T0.4  实现 NavGraph 路由框架, 4个占位页面
□ T0.5  实现 GradientBackground 全屏渐变组件
□ T0.6  验证: 4 Tab可切换, 主题色正确
```

### Sprint 1: 核心对话 (3h) — P0

```
□ T1.1  实现 Product 数据模型 + MockProducts (10条, 3品类)
□ T1.2  实现 Message 数据模型 (USER/ASSISTANT/STREAMING)
□ T1.3  实现 SseClient (OkHttp SSE, 解析 text_delta/product_cards/done)
□ T1.4  实现 ChatViewModel (sendMessage, streamingText, streamingCards, cart)
□ T1.5  实现 MessageBubble (user/assistant样式, 圆角气泡)
□ T1.6  实现 StreamingText (逐字追加 + 闪烁光标)
□ T1.7  实现 ProductCardHorizontal (对话嵌入, 图左+信息右+匹配理由)
□ T1.8  实现 ChatInputBar (文本输入+相机+语音+发送)
□ T1.9  实现 ChatScreen (消息列表+输入栏+流式状态+空状态)
□ T1.10 实现 LoadingStates 骨架屏/空/错三态
□ T1.11 验证: 发送消息→流式回复→商品卡片→可点击
```

### Sprint 2: 商品浏览 (2h) — P1

```
□ T2.1  实现 ProductCard (垂直Grid卡片: 图+名+价+销量)
□ T2.2  实现 ProductGrid (2列/3列可配置, 下拉刷新, 上拉加载)
□ T2.3  实现 CategoryTabs (横向滚动, 选中高亮)
□ T2.4  实现 SearchBar (统一搜索栏, 相机图标可选)
□ T2.5  实现 HomeScreen (每日推荐首页, 2×2商品Grid+问候语)
□ T2.6  实现 ExploreScreen (探索页, 分类Tab+3列Grid+附近好货)
□ T2.7  实现 CompareScreen (比价列表, 2列Grid+分类Tab+价格销量)
□ T2.8  验证: 3个浏览页面正常渲染, 滚动流畅
```

### Sprint 3: 商品详情+比价 (2h) — P1

```
□ T3.1  实现 ColorVariantPicker (颜色规格选择器)
□ T3.2  实现 PriceTrendChart (Canvas折线图, 30天走势)
□ T3.3  实现 ProductDetailCard (大图+属性+价格+来源)
□ T3.4  实现 PriceHistory 数据模型 + MockPriceHistory
□ T3.5  实现 ProductDetailScreen (颜色切换+价格走势+多平台)
□ T3.6  验证: 商品详情完整展示, 颜色切换联动价格
```

### Sprint 4: 个人中心 (1.5h) — P1

```
□ T4.1  实现 UserProfileHeader (头像+昵称+客服/设置入口)
□ T4.2  实现 CartPreview (购物车预览, 4商品横向列表)
□ T4.3  实现 OrderStatusBar (待付款/待发货/收货/待评价)
□ T4.4  实现 CouponCenter (领券中心, 4券卡片)
□ T4.5  实现 ProfileScreen (组合以上组件)
□ T4.6  验证: 个人中心信息完整, 交互正常
```

### Sprint 5: 设置+历史 (1.5h) — P2

```
□ T5.1  实现 SettingItem / SettingsGroup (分组设置列表)
□ T5.2  实现 SettingsScreen (账号+功能+关于+退出)
□ T5.3  实现 HistoryItem / HistoryDrawer (历史对话侧栏)
□ T5.4  验证: 设置页面导航正常, 抽屉滑出/关闭流畅
```

### Sprint 6: 联调+打磨 (2h) — P2

```
□ T6.1  对接 POST /api/chat SSE 真实接口
□ T6.2  对接 GET /api/products 真实接口
□ T6.3  对接 POST /api/feedback 真实接口
□ T6.4  添加所有错误状态处理 (网络/超时/空结果)
□ T6.5  添加点击态/按压态动画
□ T6.6  真机测试 + 截图证据收集
□ T6.7  Release APK 打包
```

---

> **总计**: 6个Sprint, 预估 11h 工时, 覆盖 8个页面 + 25+组件 + 后端联调
> 
> 本分析报告基于原型图还原, 遵循 REQS-竞赛核心需求.md 的 9 场景要求.
> 原型中缺少的「拍照找货」「购物车CRUD」「主动反问Chip」需另行设计补充.
