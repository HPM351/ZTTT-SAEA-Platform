# SAEA 平台知识图谱

> 来源：基于 `F:\HPM_opt_Web` 项目代码全量分析
>
> 用法：看到感兴趣的知识点编号，直接问我 "讲一下 #12" 或 "什么是SQLAlchemy ORM"，我结合你的项目代码给你讲清楚。

---

## 一、Python 基础核心

### #1 Python 导入与模块系统
`import os` 导入整个模块；`from database import Task` 只导入指定项；`from .evaluator import calc_score` 中的 `.` 指"同级目录"。`__init__.py` 把文件夹标记为 Python 包。

### #2 类型提示 (Type Hints)
`: str`、`-> dict`、`List[ParamItem]` 是告诉阅读者（及 PyCharm/AI）函数期望和返回什么类型的"注释"，Python 不强制检查，但极大提升可读性。

### #3 异常处理 (try/except/finally)
`try` 里代码崩了 -> 跳进 `except` 处理 -> `finally` 无论如何都会执行。你的项目有三层容错：指标级别给兜底值、CST 级别标记无效个体、数据库级别 commit/rollback/close。

### #4 上下文管理器 (with 语句)
`with open(...) as f:` = 自动开 + 自动关，等价于 try/finally 的缩略版，避免忘记释放文件/数据库连接等资源。

### #5 列表/字典推导式
`[表达式 for 变量 in 可迭代对象]` 把 for 循环压缩成一行。`{key: val for ...}` 是字典版。本质是"对每个元素做同一件事，收集结果"的加工写法。

### #6 Lambda 与匿名函数
`lambda x: x * 2` = 临时的一次性小函数，常用于 `sorted(list, key=lambda x: x.score)` 这类"拿出来用一次就丢"的场景。

### #7 Python 面向对象基础
class = 把相关数据（属性）和操作（方法）打包在一起的容器。`self` 是"这个实例自身"，方法调用时 Python 自动传入。适合需要保存状态或创建多个独立副本的场景。

### #8 `*args` 与 `**kwargs`
`*args` 收位置参数为元组，`**kwargs` 收关键字参数为字典。你项目里 `{**dict1, **dict2}` 是把字典"炸开"合并；Pydantic 的 `extra="ignore"` 就是 `**kwargs` 思想 -- 多余的参数自动丢弃不报错。

### #9 变量作用域与 `global`
函数内能读外部变量，但不能替换（会创建同名的局部变量）。`task_status_flags[key] = val` 是改字典内容（允许），`task_status_flags = {}` 是替换变量（不允许，除非声明 `global`）。跨文件传状态用参数，比全局变量干净。

### #10 装饰器 (Decorator)
`@xxx` = 给下面函数"加一层包装"的缩写。`@app.get("/api/health")` 把普通函数注册为 FastAPI 路由处理器，自动处理 HTTP 请求解析和 JSON 序列化。

### #11 可迭代对象与生成器
能放在 `for x in ...` 里的都是可迭代对象（列表、字典、range、字符串等）。生成器 `(x for x in list if ...)` 是省内存版 -- 用到哪个才算出哪个，`next()` 一个一个取到符合条件的就停。

---

## 二、FastAPI 后端框架

### #12 FastAPI 应用与路由
`app = FastAPI()` 创建了一个服务器对象，所有路由、中间件都注册在这上面。`@app.get()` 读数据（路径/查询参数），`@app.post()` 写数据（请求体 JSON）。

### #13 路径参数与查询参数
路径参数 `{task_id}` 嵌在 URL 里，标识要访问的具体资源（哪个任务、哪个用户）。查询参数跟在 ? 后面，key=value 格式，标识过滤/排序条件（取多少条、筛选状态）。

### #14 Request Body 与 Pydantic
前端 POST 的 JSON 请求体 -> FastAPI 看函数参数类型提示 -> Pydantic 自动解析校验 -> 你拿到一个完整的 Python 对象。config.model_dump() 再把它变回普通字典。

### #15 CORS 中间件
浏览器安全策略：不同端口/域名算跨域，默认拦截。CORSMiddleware 在后端响应头加 Access-Control-Allow-Origin: *，告诉浏览器放行。局域网 ["*"] 没问题，公网要写具体域名。

### #16 BackgroundTasks
background_tasks.add_task(func, ...) 把耗时操作（跑几小时的优化）登记到后台队列。FastAPI 先返回响应，任务再慢慢跑，互不阻塞。页面不会白转圈。

### #17 WebSocket 实时通信
HTTP 是一问一答，WebSocket 建立永久双向通道。后台每算完一个个体 -> manager.send_to_task() 推数据 -> 前端 ECharts 实时更新。刷新页面只断通道，后台任务不停。

### #18 Router 模块化
app.include_router(nn_router) 把不同功能的路由拆到不同文件。nn_service.py 只管神经网络、llm_service.py 只管文献助手。找接口不用在千行 main.py 里搜索。

### #19 StreamingResponse / FileResponse
普通接口返回 JSON，文件接口返回图片/文件。StreamingResponse(buf, media_type="image/png") 把二进制数据流式发给前端。CST 预览图就是用这个接口把 .dib 转成 PNG 返回的。

### #20 生命周期事件
@app.on_event("startup") 在服务器启动时自动执行一次，比第一个请求来得早。你的 init_db() 就在这里跑，保证 tasks/generations 等表已经建好。

### #21 BaseModel 与字段类型
继承 BaseModel 后，Pydantic 自动做四件事：解析 JSON 为 Python 对象、校验类型（自动转型或报错）、序列化回字典、生成 API 文档。字段定义的写法就是类型提示。

### #22 嵌套模型
Pydantic 模型里可以套另一个 Pydantic 模型。JSON 里的 `{"ga": {...}}` 按类型提示 `Optional[GaConfig]` 自动转成 GaConfig 对象，用 `config.algo.ga.pc` 直接访问内层字段。

### #23 Optional / 默认值
`cstPath: str` = 必填。`selectedHistoryPath: Optional[str] = None` = 选填，没传就是 None。`targetsList: Optional[List] = []` = 选填，没传就是空列表。None 表示"没这个值"，[] 表示"有但空的"。

### #24 `model_dump()` 与 `model_dump_json()`
Pydantic 对象 -> `model_dump()` 变普通字典（传给其他 Python 函数），-> `model_dump_json()` 变 JSON 字符串（写文件/网络传输）。返回给前端时 FastAPI 自动序列化，不需要手动调。

### #25 `extra = "ignore"` 配置
`model_config = {"extra": "ignore"}` 告诉 Pydantic：前端多传了我没定义的字段？直接丢掉不报错。三种策略：ignore（丢）、forbid（报错）、allow（收下不管）。你的项目用 ignore 最稳妥。

---

## 四、SQLAlchemy 数据库

### #26 ORM 基本概念
ORM = 用 Python 类操作数据库，SQLAlchemy 自动翻译成 SQL。类 => 表，对象实例 => 行，属性 => 列。不用手写 SQL 字符串，查出来的是有字段名的 Python 对象而不是元组。

> 总结：ORM 让你用 Python 对象思维操作数据库，SQLAlchemy 在背后翻译成 SQL。你写 `obj.attr`，它翻译成 `SELECT attr FROM table`；你 `db.add(obj)`，它转成 `INSERT INTO`。查出来的是带字段名的对象而不是裸元组，代码可读性高得多。

### #27 引擎、会话与声明基类
engine = 怎么连数据库（只创建一次）。SessionLocal = 每次读写的独立连接（用完 close）。Base = 所有表模型继承的声明基类。三者各管一摊。

> 总结：engine 是全局唯一的连接配置（数据库类型+路径），SessionLocal 用 engine 生成一个个独立会话（用完必 close），Base 是所有表模型的父类。三者各管一摊：engine 管连、Session 管操、Base 管定义。

### #28 表定义（Column 类型）
Column(类型, 参数) 定义一列。String/Integer/Float/Boolean/DateTime/JSON 决定了数据库存成的格式。primary_key=True 设主键，ForeignKey 关联其他表，default 设默认值，index=True 加速查询。

> 总结：String/Integer/JSON 等决定了数据库怎么存；primary_key 唯一标识一行；ForeignKey 声明跨表引用关系；index 给这列建索引，查询快但写入稍慢。你项目里大量用 JSON 列来存去物理化的参数和指标，表结构不改也能适配不同优化问题。

### #29 外键与关系
`task_id = Column(String, ForeignKey("tasks.id"))` 和 `relationship("User", back_populates="sessions")` —— 数据表之间的关联是怎么建立的？

> 总结：ForeignKey 是数据库层面的硬约束——`generations.task_id` 的值必须在 `tasks.id` 中存在，否则报错。relationship 是 Python 层面的导航属性——`task.generations` 自动 JOIN 出关联行。配合 cascade="all, delete-orphan"，删父表行时子表行自动清干净，不留孤儿数据。建表时修路（定义外键），插数据时通车（实际引用）。

### #30 CRUD 查询操作
```python
db.query(Task).filter(Task.id == task_id).first()
```
—— `query`, `filter`, `first`, `all`, `order_by`, `.limit()` 的用法链。

> 总结：标准链是 `query → filter → order_by → limit → first()/all()`。first() 返回一个对象（没有则 None），all() 返回列表（可能空）。update/delete 不走 add，直接用 `.update()`/`.delete()`，但必须 commit 才生效。查询操作不需要 commit。

### #31 聚合函数
`func.max(Generation.gen_index)` —— 怎么在查询时直接取最大值、计数？

> 总结：`func.max(col)` 和 `func.count(col)` 等聚合函数需要配合 `.scalar()` 使用——它直接返回数值本身，而 `.first()` 返回含元组的行对象。你项目里用 `func.max(Individual.ind_index)` 获取当前优化代数，用 `func.max(Generation.best_score)` 取历代最优分数。

### #32 JSON 列类型
`config_json = Column(JSON)` —— 为什么可以直接存 Python 字典到数据库？

> 总结：SQLAlchemy 的 JSON 列自动做 json.dumps()（写入时字典→字符串）和 json.loads()（读出时字符串→字典），代码里始终操作字典。你项目几乎所有可变数据都用 JSON 列（params_json/metrics_json/waves_json），这是"去物理化"的核心——表结构固定不变，前端传什么参数字段都能存。

### #33 会话生命周期
`db.commit()`, `db.rollback()`, `db.close()` —— 什么时候必须 commit？不 commit 会怎样？finally 里关会话为什么重要？

> 总结：add/update/delete 操作在 commit 前只存在内存草稿区，不 commit 程序退出就丢光。rollback 撤销异常状态下未 commit 的修改，让会话恢复可用。close 归还连接到连接池，不关会导致连接耗尽。标准模板：try { 操作 → commit } except { rollback } finally { close }。

---

## 五、异步 Python (Async/Await)

### #34 `async` / `await` 基本概念
你项目里有 `async def` 的函数，也有普通 `def` 的函数 —— 区别在哪？`await` 什么时候必须加？

> 总结：async def 定义异步函数，await 挂起等待但不阻塞事件循环。调用 async def 的函数时必须加 await，否则拿回来的是协程对象而不是结果。你项目中数据库操作用同步 def（快，没必要异步），WebSocket/网络操作用 async def（不知道对方啥时候响应）。

### #35 `asyncio` 事件循环
`asyncio.get_running_loop()` —— 后端的"事件循环"是什么？为什么后台任务需要传入 `loop`？

> 总结：事件循环是服务器的调度心脏，单线程循环执行：等通知→处理就绪任务→继续等。它不是轮询而是靠操作系统（Windows IOCP）推送通知。`loop = asyncio.get_running_loop()` 拿到事件循环的引用，后台任务需要它才能用 `await` 做异步操作。同一进程只有一个事件循环，BackgroundTasks 本质上是往这个循环注册新协程。

### #36 WebSocket 异步通信
`await websocket.receive_text()` / `await manager.send_to_task()` —— 为什么 WebSocket 操作全是 `async`？

> 总结：WebSocket 的收发操作全是 async 因为不知道对方啥时候响应。三个关键 await：accept（等连接确认）、receive_text（等客户端发消息）、send_to_task（等数据真正发出去），每个都利用事件循环的"等通知"机制，不阻塞服务器处理其他请求。你项目的实时推送链路：CST 评分→落库→WS推送→前端 ECharts 刷新，只有推送这一步是异步的。

---

## 六、Vue 3 前端框架

### #37 Composition API (`<script setup>`)
你的 Vue 文件都用的 `<script setup>` —— 和传统 Options API (`data`, `methods`) 有什么区别？

> 总结：Composition API 按功能聚合代码（一个功能的数据+逻辑写在一起），Options API 按类型分（data/methods/mounted 分散三处）。script setup 是语法糖，省去 export default，顶层变量和函数直接可在模板中使用。你的项目场景只需要看懂结构，不需要深究响应式原理。

### #38 响应式系统 (ref / reactive / computed)
```javascript
const isDarkMode = ref(false);
const sysEnv = reactive({ python: "检测中..." });
const cpuColor = computed(() => ...)
```
—— 为什么要用 `ref` 和 `reactive` 包裹数据？`computed` 有什么特殊？

> 总结：ref 包单个值（JS 里 .value，模板自动脱壳），reactive 包对象（直接改属性），computed 自动计算依赖变化后重新求值。三者在模板里用起来没区别，Vue 编译时自动处理 ref 的脱壳。

### #39 模板语法
`v-model:value="isDarkMode"`, `v-for`, `v-if`, `@click`, `{{ cpuUsage }}` —— 这些模板指令在干什么？

> 总结：{{ }} 插值显示变量，@click 绑定点击事件，v-model 双向绑定（数据↔界面互相同步），v-for 循环渲染列表，v-if 条件渲染（真才存在 DOM 中），: 动态绑定 JS 变量到组件 prop。

### #40 生命周期钩子
`onMounted(() => { fetchEnvInfo() })` —— `onMounted` 什么时候执行？还有哪些生命周期函数？

> 总结：onMounted 在组件渲染到 DOM 后触发一次，本质是"页面加载完成触发器"，最适合发请求、连 WebSocket。其他常用钩子：onUnmounted（页面关闭时清理连接）。

### #41 组件间通信
`const showDocs = inject("globalDocsVisible")` 和 App.vue 的 `provide` —— 为什么不用 props 层层传？

> 总结：provide/inject 跨过中间组件层直接传递数据（类似打地道），避免 props 层层中转。作用域限制在 Vue 组件树内，不是全局。适合全局状态（手册开关、主题色等）。

### #42 Vue Router
`const router = useRouter(); router.push({ name: 'CstOpt' })` —— 单页应用（SPA）的页面跳转不是真实的链接跳转，那它在干什么？

> 总结：Vue Router 只换组件不刷新页面（无白屏），WebSocket 等长连接不会断开。整个应用一个 HTML 文件，靠 URL 决定渲染哪个组件（<router-view /> 根据路径切换）。

### #43 作用域 CSS
`<style scoped>` —— 为什么这里写的 CSS 不会影响到其他页面？

> 总结：scoped 自动给组件每个元素加唯一属性（data-v-xxxxx），CSS 选择器附带该属性，只命中本组件元素。需要穿透到子组件时用 :deep()。

---

## 七、Naive UI 组件库

### #44 布局系统 (n-grid / n-gi)
```html
<n-grid :x-gap="24" :cols="2">
  <n-gi :span="1">...</n-gi>
</n-grid>
```
—— 怎么用网格系统做响应式布局？

> 总结：n-grid 是棋盘容器（定义列数和间距），n-gi 是格子（定义占几列宽）。n-gi 必须嵌套在 n-grid 里使用，一个管排布一个管占位。

### #45 n-card 卡片组件
你的页面几乎全是卡片（`n-card`），`hoverable`, `segmented`, `size="small"` 这些属性是什么意思。

> 总结：n-card 提供白底圆角阴影的视觉框架，title 显示标题，hoverable 悬停浮起，segmented 标题栏分割线，size="small" 紧凑模式。n-gi 画格子，n-card 装饰格子，二者配合实现整齐的区块化布局。

### #46 n-form / n-form-item
表单验证和布局 —— `label-placement="top"` 和 `show-feedback="false"` 的意义。

> 总结：n-form 的 :model 绑定整个数据对象（供验证系统定位字段），n-form-item 的 path 指定验证哪个字段，v-model 才是真正的双向绑定。label-placement 控制标签位置，show-feedback 控制是否显示验证错误提示。

### #47 n-data-table 表格
列定义 `title`, `key`, `render` —— `render` 那一栏的 `h()` 函数是干嘛的（渲染函数）？

> 总结：title 是表头文字，key 对应数据对象的属性名（简单取值），render(row) 用 h() 函数动态创建组件/标签（复杂渲染）。h(NTag, {props}, children) 等价于模板里的 <n-tag>，因为列定义是 JS 对象不能写 HTML。

### #48 n-progress 进度条
`type="dashboard"` 和 `type="line"` —— 你的 CPU 圆环仪表盘和任务进度条怎么实现的。

> 总结：type="dashboard" 画圆环仪表盘（CPU 使用率），type="line" 画直线进度条（优化进度）。:percentage 控制进度值 0~100，可结合 computed 做颜色分段（绿→黄→红）。

### #49 n-drawer 抽屉
平台使用手册的侧边弹出面板 —— `placement`, `width`, 自定义 class。

> 总结：n-drawer 从屏幕边缘滑出一个面板，不离开当前页面。v-model:show 控制开关，placement 控制滑出方向（默认 right），适合文档/设置/详情等临时查看场景。

### #50 n-tabs / n-tab-pane
使用手册里的三大标签页（Q&A / 图表辞典 / 打分机制）。

> 总结：n-tabs 是标签容器，n-tab-pane 是每个标签页（name 唯一标识，tab 显示文字）。default-value 设默认选中，type 切换标签栏样式（line/card/segment）。同一位置换内容，适合结构化说明书。

### #51 n-collapse 折叠面板
FAQ 的展开/收起列表 —— `n-collapse-item` 的 `name` 属性有什么用？

> 总结：n-collapse 容器管理多个可折叠面板，accordion 属性开启手风琴模式（一次只展开一个）。n-collapse-item 的 name 是唯一标识，Vue 通过它控制哪个面板展开/收起。

### #52 n-tag / n-badge
任务状态标签（运行中/已完成）和探针指示灯（绿/红圆点）。

> 总结：n-tag 是独立彩色标签（type 控制颜色：success/warning/error），表格状态列和任务卡片常用。n-badge 在子元素右上角挂小标记（圆点或数字），适合探针在线状态指示。

---

## 八、Vite + 构建工具

### #53 Vite 配置 (`vite.config.js`)
为什么前端代码能写 `.vue` 和从 `@/components` 导入？开发服务器的反向代理怎么配置？

> 总结：Vite 在开发时实时编译 .vue 为浏览器可识别的 JS+CSS。@ 是 src 目录的路径别名（resolve.alias 配置）。反向代理把前端 /api 请求转发到后端 localhost:8000，解决开发时跨域问题，生产模式走打包后的静态文件则不需要。

### #54 `package.json`
`dependencies` 和 `devDependencies` 的区别，`npm install` 时发生了什么。

> 总结：dependencies 是运行时必须的库（Vue/Naive UI/Axios），打包后还要用；devDependencies 只在开发时需要（Vite/编译器），打包时不塞进最终 JS。npm install 下载全部依赖到 node_modules 并生成锁文件锁定版本。

### #55 ES Module (ESM)
你的 `import axios from "axios"` —— 和 `require('axios')` 有什么区别？

> 总结：import（ESM）是 JS 官方模块标准，编译时解析、浏览器原生支持，支持按需导入。require（CommonJS）是运行时加载、浏览器不支持需转译。你前端用 import、Node 后端（新版本）也可用 import，但同一文件不能混用。

---

## 九、Axios / 网络请求

### #56 axios 基础
```javascript
const res = await axios.get(`${API_BASE}/health`);
```
—— GET 和 POST 的参数位置，`res.data` 为什么能直接拿到后端返回的 JSON？

> 总结：GET 参数在 URL 后（params 对象），POST 参数在请求体（第二个参数）。res.data 是 axios 自动把后端 JSON 字符串解析成 JS 对象后的结果。生产模式 API_BASE 为空字符串走 Vite 代理，开发模式直接指向 localhost:8000。

### #57 错误处理
`try { axios.get(...) } catch (e) { console.error(e) }` —— 网络断开时前端怎么优雅地处理。

> 总结：axios 请求失败会抛异常，不加 try/catch 会中断执行。但本地自用项目可以不写——后端崩了前端白屏，看一眼 PyCharm 报错修得比前端弹窗更快。过度工程对单人/小团队本地工具没有意义。

---

## 十、ECharts 数据可视化

### #58 ECharts 基本架构
`option` 对象里的 `xAxis`, `yAxis`, `series` —— ECharts 渲染图形的基本组件树。

> 总结：所有 ECharts 图表统一由 option 对象驱动，核心三要素：xAxis（X轴）、yAxis（Y轴）、series（数据系列）。series.type 决定图表类型（scatter/line/surface/heatmap/parallel）。WebSocket 推新数据时只需 chart.setOption() 更新 series.data，ECharts 自动动画过渡。

### #59 散点图 (Scatter) — 帕累托云图
你优化页面的散点云图 —— `series` 的 `type: 'scatter'` 怎么接受 `[{value: [x,y], itemStyle: {color: ...}}]` 的数据。

> 总结：散点图每个数据点对应一次 CST 仿真的个体。数据格式为 {value: [x, y], itemStyle: {color}}，可独立控制颜色。普通个体蓝色，帕累托前沿上的个体橙色，形成"云图"的散点集群。前端根据后端推送的帕累托标记切换颜色，WebSocket 推新个体时图表动态更新。

### #60 折线图 (Line) — 代际收敛趋势
多条 Y 轴对应不同优化目标 —— `yAxis` 的 `min`/`max` 和 `series` 的 `yAxisIndex`。

> 总结：折线图展示各代最优个体的目标值随代数推进的变化，判断优化是否收敛。不同量纲的目标用左右双 Y 轴（yAxisIndex: 0/1 指定挂载），各自的 min/max 独立缩放避免数值小的一方被压平。曲线趋于平稳说明算法已找到最优区域。

### #61 3D 表面图 (Surface)
神经网络页面的 3D 参数地形扫描 —— ECharts GL 的三维数据格式。

> 总结：3D 表面图用 [x, y, z] 三维坐标网格渲染参数地形，z 轴是代理模型预测的指标值。配合 visualMap 颜色映射，直观找到"效率山峰"的最佳参数区域。训练好的代理模型能在毫秒级预测整个参数空间，可视化取代人工翻表格。

### #62 平行坐标系 (Parallel)
高分个体的多维轨迹追踪 —— `parallelAxis` 和 `type: 'parallel'` 的数据格式。

> 总结：平行坐标系不受维度限制，每根 axis 表示一个参数，每个个体是一条穿越所有轴的折线。当优化变量超过 3 个时（散点图和 3D 图无法展示），用平行坐标一眼看出高分个体的参数分布规律。

### #63 热力图 (Heatmap)
优胜个体相关性（Pearson 相关系数） —— `type: 'heatmap'` 和颜色映射。

> 总结：热力图展示各参数之间的 Pearson 相关系数（-1~1），蓝正红负。用于事后分析：发现功率与得分强相关（打分偏功率）、效率与功率负相关（物理矛盾）、两参数强相关（下轮优化缩小搜索范围而非固定变量）。是诊断打分公式和参数设置的辅助工具，不应用来降维。

---

## 十一、NumPy / SciPy

### #64 数组基础操作
`np.array()`, `np.mean()`, `np.max()`, `np.linspace()` —— 在你的 evaluator.py 里是怎么用的。

> 总结：NumPy 数组运算是对每个元素分别操作（列表是整体重复），适合波形分析。np.array() 把 CST 结果转数组，np.mean()/np.max() 统计稳定段均值/频域峰值，np.linspace() 生成均匀采样点做参数扫描。

### #65 布尔索引 (Mask)
`stable_y = y[mask]` —— 提取稳定段的波形数据，不用写循环。

> 总结：mask 是布尔数组（True/False），y[mask] 只取 True 位置的元素。替代 for+if 的写法，一行搞定数据筛选。支持条件组合 &/|，如 (time > 1.5) & (y > 0.01)。

### #66 SciPy 寻峰
`scipy.signal.find_peaks(y, height=max_val * 0.05)` —— 怎么自动找到频域谱里的所有峰值。

> 总结：find_peaks 从波形数据中自动识别所有显著峰值。height 参数设定幅值门槛滤除噪声毛刺。返回峰在数组中的索引，配合 freq[peaks] 即可读出基波/谐波的频率和幅值，直接进评分公式。

---

## 十二、Python 标准库

### #67 `os` 模块
`os.path.join()`, `os.path.dirname()`, `os.environ`, `os.getenv()` —— 文件和环境的交互操作。

> 总结：os.path.join() 自动处理系统路径分隔符（Win/Linux），os.path.dirname(__file__) 定位当前文件所在目录，os.getenv() 读取环境变量（可设默认值）。项目里用它定位数据库文件路径和读取配置。

### #68 `json` 模块
`json.load()` / `json.dump()` —— 读写 JSON 配置文件。`indent=4, ensure_ascii=False` 的意义。

> 总结：json.load(f) 从文件读 JSON 为 Python 字典，json.dump(obj, f) 写回文件。indent=4 让输出可读（缩进换行），ensure_ascii=False 让中文正常显示不被转成 \u 编码。带 s 的函数（loads/dumps）操作字符串而非文件。

### #69 `hashlib` 模块
`hashlib.md5(norm_path.encode()).hexdigest()` —— 用 CST 路径生成固定哈希，作为配置文件名的原理。

> 总结：MD5 将任意长度的输入映射为 128 位（32 位十六进制）固定长度的哈希值。同一个 CST 路径永远输出相同哈希，作为唯一且安全的配置文件名。碰撞概率约 2^64 输入才出现 50%，本地方案中（几十个输入）可视为零。

### #70 `datetime` 模块
`Column(DateTime, default=datetime.now)` —— 自动记录创建时间戳。

> 总结：default=datetime.now（不加括号）传入的是可调用对象，每插一行自动取当前时间。onupdate=datetime.now 在行被修改时自动刷新时间戳。SQLAlchemy 存入 SQLite 时为 ISO 格式字符串，读回时恢复为 datetime 对象。

### #71 `io` 模块
`io.BytesIO()` —— 在内存中处理二进制数据（图片）、不写磁盘直接返回给前端。

> 总结：BytesIO 创建内存缓冲区模拟文件对象，避免临时文件写入磁盘。项目中将 CST 的 3D 预览图（.dib）转为 PNG 后通过 StreamingResponse 直接返回给前端，不产生磁盘 IO。

### #72 `re` (正则表达式)
`re.search(r'CST.*?(\d{4})', value, re.IGNORECASE)` —— 从环境变量值里提取 CST 版本年份。

> 总结：re.match() 要求从字符串开头匹配（开头不对就 None），re.search() 在整个字符串里搜到第一个匹配为止。项目中的环境变量和日志文本格式不固定，适合用 search 从中提取年份数字。

### #73 `psutil` 系统监控
`psutil.cpu_percent()`, `psutil.virtual_memory().percent`, `psutil.process_iter()` —— 实时读取 CPU、内存和进程状态。

> 总结：psutil 跨平台读取系统资源，无需对不同操作系统写不同调用。cpu_percent(interval=0.5) 采样半秒求真实负载，virtual_memory().percent 取内存使用率，process_iter 遍历进程检测 CST 是否运行。

### #74 `ctypes` Windows API
`ctypes.windll.shcore.SetProcessDpiAwareness(1)` —— 解决 Windows 文件选择器在高 DPI 显示器上的缩放问题。

> 总结：高 DPI 显示器上老程序会被 Windows 强行放大导致模糊。SetProcessDpiAwareness(1) 声明进程支持 DPI 感知，让 tkinter 文件选择器在高分屏上显示清晰。参数 0=不感知(糊) 1=系统级感知 2=每监视器感知。

### #75 `tkinter.filedialog`
用 Python 唤起 Windows 原生"打开文件"对话框 —— 为什么不用前端实现而要在后端调 tkinter？

---

## 十三、geatpy 进化算法库

### #76 种群与编码 (Phen)
`Phen` 矩阵 —— 算法是怎么办一个个体的参数传进来的？染色体编码和实数参数的映射。

> 总结：geatpy 只操作数值矩阵（Phen），每一行是一个个体每一列是一个变量。eval_pop 中用 zip(opt_names, Phen[i,:]) 把数字行映射成参数字典传入 CST。去物理化设计的核心：换变量名只改 opt_names 列表，算法层一行不动。

### #77 适应度计算
`Fit[i, 0] = scr` —— geatpy 要求适应度是什么形状的矩阵？为什么是 `(n, 1)` 而不是一维数组？

> 总结：Fit 必须是 (n, m) 二维矩阵，n 个体数 m 目标数。用 (n, 1) 而非一维数组是为了兼容多目标扩展——切多目标时只需改 m 值，eval_pop 的数据结构不用动。单目标优化只是多目标的一个特例 (m=1)。

### #78 遗传算子
`recCode`, `mutCode`, `pc`, `pm` —— 交叉概率和变异概率怎么影响搜索行为？

> 总结：pc（交叉率）控制多少个体通过两两杂交产生后代（高=多样性好），pm（变异率）控制每个参数被随机扰动的概率（高=探索强但收敛慢）。recCode/mutCode 选择交叉/变异的具体数学方式（均匀/高斯/线性等）。两者共同决定算法的探索-开发平衡。

### #79 精英保留策略
你的"注入优良基因"功能 —— geatpy 如何确保最优个体不丢失？

> 总结：np.vstack([Chrom[best_idx], Sel]) 将当代最优个体原样复制到下一代首行，不经过交叉变异破坏。防止最优解因随机探索而丢失（遗传退化）。"注入优良基因"是人工版的精英保留——用户指定已知好参数强行加入初始种群，加速收敛。

---

## 十四、CST 集成 (COM 接口)

### #80 COM 自动化的基本原理
`import cst.results` —— Python 是如何通过 COM 接口操控 CST Studio Suite 的？

> 总结：COM 是 Windows 跨进程通讯协议，Python 通过它操控 CST。两条通道：cst.interface 用 VBA 命令（add_to_history）改参数+启动求解器，cst.results 读结果树（3D→结果项→get_ydata/xdata）。需要 CST_PYTHON_PATH 环境变量指向 CST 的 Python 包装库才能导入 cst.results。

### #81 参数写入
`modeler.add_to_history('StoreParameter', f'StoreParameter("{k}", "{v}")')` —— 用 VBA 历史命令间接修改 CST 设计变量的原理。

> 总结：add_to_history 往 CST 历史记录列表插入一条 VBA 命令字符串，CST 在自己的环境里执行它来修改变量值。参数名是任意字符串——只要跟 CST 模型里的变量名一致，什么物理量都能写。这是去物理化在最底层的落实。

### #82 结果读取
`cst.results.ProjectFile(cst_path)` —— Python 读取 CST 计算结果的对象模型（3D 树 → 结果项 → 数据提取）。

> 总结：ProjectFile 打开 .cst 项目文件，三层结构取数据：res.get_3d() → get_result_item(path) → get_ydata()/get_xdata()。path 对应 CST 结果树的节点路径（如 1D Results\Port signals\p1），由前端 targets_list 配置。

### #83 时域 / 频域曲线提取
`.get_3d().get_result_item(path)` → `.get_ydata()` / `.get_xdata()` —— 数据格式和转换。

> 总结：get_xdata() 返回横轴（时间/频率），get_ydata() 返回纵轴（幅值/功率）。时域→布尔索引取稳定段均值，频域→find_peaks 找主峰频率和幅值，0D 标量→直接取 ydata[0]。数据从 CST 二进制→numpy array→float 标量的链条。操作完 del res + gc.collect() 释放 COM 对象防内存泄漏。

---

## 十五、项目架构与数据流

### #84 前后端分离架构
你的 `main.py`（后端 :8000）和 `hpm-frontend`（开发 :5173）的关系，`IS_PRODUCTION_MODE` 切换逻辑。

> 总结：开发模式开两个端口（Vite :5173 + FastAPI :8000），Vite 反向代理转发 /api 请求。生产模式前端打包成静态文件由后端直接 serve，一个端口搞定。WebSocket 直连后端不走代理。

### #85 配置驱动设计
为什么优化目标、变量、算法参数全由前端配置 JSON 驱动 —— "去物理化"设计思想。

> 总结：代码不硬编码任何变量名，全链路从 config_json 解析。opt_names 定义变量、Phen 矩阵存数字、zip(opt_names, Phen[i]) 拼字典传 CST。换模型/换算法/换目标只需改前端配置，后端一行不动。

### #86 WebSocket 实时推送的数据链路
```
CST 跑完个体 → evaluator 打分 → 落库 SQLite → WS 推送 → ECharts 刷新
```
—— 这条路径上每个环节的角色。

> 总结：全链路除 CST 仿真外都在毫秒级。WS 逐个推送让散点图实时增长，用户确认优化没卡死。急停指令走逆向 WS 通道设定标记，eval_pop 下次循环检测后优雅退出（不等当前 CST 跑完不会中断）。

### #87 算力白嫖 (Result Cache)
`global_cache[param_key] = m` —— 为什么同样参数组合的仿真结果可以复用？哈希键的设计。

> 总结：param_key = tuple(round(p[k], 5) ...) 将参数字典转元组作为 key，浮点截断避免精度误差导致缓存未命中。精英保留/注入基因/收敛后期是主要命中场景，省去同代内重复仿真时间。仅当前 eval_pop 调用内有效，跨代不共享。

### #88 JSON 配置文件持久化
`configs/conf_{pure_name}_{hash}.json` —— 前端切换 CST 项目时自动恢复上次配置的机制。

> 总结：CST 路径→MD5 哈希→唯一配置文件名。切回同个 .cst 文件时自动加载之前保存的参数/目标/算法设置，无需手动重新配置。哈希保证跨机器拷贝文件时配置还能匹配。

---

## 十六、SAEA 算法原理（领域专用）

### #89 代理模型 (Surrogate Model)
你的 `models/` 里的 `.pth` 和 `.pt` 文件 —— 神经网络替代 CST 仿真的思想。

> 总结：用 NN 预测代替大部分 CST 调用。阶段一冷启动（真机采集），阶段二训练 NN，阶段三代理辅助进化（90% NN 预测+10% 真机验证），阶段四在线微调。NN 预测毫秒级，CST 仿真秒~分钟级。代理模型不直接算分，只预测物理指标，分数由 evaluator 统一计算。

### #90 在线微调 (Online Learning)
`nn_online_logs` 表记录的 Loss 和 Error —— 怎么用真机验证结果反向微调代理模型？

> 总结：每代用少量真机数据（3~5 个个体）对代理模型做一步梯度下降微调，不重新训练。nn_online_logs 记录每代的 loss、error、预测 vs 真实值。数据量从初始几十条增长到上千条，模型精度随之提升。

### #91 自适应变异
`useAutoMut` 和 `autoMutRange` —— 从均匀→高斯→布列德变异，搜索行为如何平滑过渡。

> 总结：代码按代数比例分段切换变异方式——前 r_low% 代用 mutuni（均匀，大范围探索），中间到 r_high% 用 mutgau（高斯，区域搜索），之后全部用 mutbga（布列德，精细微调）。autoMutRange=[30,80] 表示前 30% 均匀、30%~80% 高斯、之后布列德。

### #92 双轨打分体系
`algo_type == "BO"` vs GA/PSO 的不同死区策略 —— BO 为什么需要平滑梯度而 GA 可以断崖淘汰。

> 总结：BO 用高斯过程回归拟合目标函数，要求分数连续平滑，死区给低分（非零）保持可微性。GA/PSO 只看适应度相对大小，死区直接给 0 分淘汰，不关心突变。

### #93 评分公式详解
Maximize / Minimize / Target 三种模式的数学公式 → 软硬惩罚 → 最终分数量级放大 100x。

> 总结：Maximize 用 raw/ref 归一化，Minimize 用 ref/raw 归一化，Target 用高斯/线性衰减按偏差距离算分。软惩罚减半不留死角，硬惩罚归零直接淘汰。最终总分放大 100x 让轮盘赌更好区分相近个体，加速收敛。

---

## 十七、Git 版本控制

### #94 Git 基础操作
`git init`, `git add`, `git commit`, `git log`, `git diff`, `.gitignore`。

> 总结：.gitignore 排除 __pycache__/.venv/node_modules/saea_data.db/configs/ 等本地生成文件。日常循环是 git add . → git commit -m "说明"。改出 bug 可以 git checkout 回滚，想看改动用 git diff。

### #95 分支管理
`git branch`, `git checkout -b`, `git merge` —— 试一个大胆的想法，不满意直接删分支。

> 总结：main 放稳定版，新想法开分支（git checkout -b exp-tag），测试通过再 merge 回 main，不行直接 -D 删分支不影响 main。PIERS 论文期间建议用分支隔离实验性改动。

---

## 十八、项目开发工具链

### #96 PyCharm 调试器
断点调试的基本用法（行断点、条件断点、单步跳过/步入、查看变量、观察表达式）。

> 总结：行断点点行号设置，条件断点右键设条件表达式。F7 步入函数内部、F8 跳过执行下一行、F9 继续到下一个断点。你项目最常用断点位置：eval_pop 看参数字典、run_single_simulation 看 CST 返回、calc_score 看分数来源。

### #97 虚拟环境 (venv / conda)
`.venv` 文件夹的用途 —— 为什么每个项目要有独立的环境？

> 总结：虚拟环境隔离每个项目的 Python 包版本。项目 A 用 PyTorch 2.0，项目 B 用 PyTorch 1.8，各装各的不冲突。.venv 不提交 Git（在 .gitignore 里），其他人拉项目后自己 pip install 重建环境。

### #98 `requirements.txt`
`pip install -r requirements.txt` —— 项目依赖的一键安装。

> 总结：requirements.txt 列出所有依赖包及其版本，一行一个。git pull 后执行 pip install -r requirements.txt 一键装完所有依赖。和 .venv 配合：先建虚拟环境 → pip install -r requirements.txt → 直接跑，不会污染全局 Python 环境。

---

> 总共 **98 个知识点**，覆盖你项目里用的所有技术栈。
>
> 随便挑一个编号问我，我结合你的 `main.py` / `schemas.py` / `Home.vue` 代码给你讲清楚。
