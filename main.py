import os
import io
import asyncio
import hashlib
import json
import sys
import re
import httpx
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import psutil
from sqlalchemy import desc, func
from database import init_db
import platform # 引入系统判断库
from PIL import Image
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from engine.nn_service import nn_router
from engine.llm_service import llm_router
from engine.api_data_center import router as data_center_router
import tkinter as tk
from tkinter import filedialog
from database import SessionLocal, Task, Generation, Individual, Waveform
from schemas import OptimizationConfig
from engine.task_saea import run_optimization_task
from typing import Dict, Any
from engine.task_sweep import run_sweep_task
from fastapi import Query
from fastapi import APIRouter
app = FastAPI(title="ZTTT SAEA Backend Engine")
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")
# ==========================================
# 🌐 环境切换开关
# ==========================================
# 开发时设为 False (配合 npm run dev)
# 映射公网/打包部署时设为 True (先运行 npm run build)
IS_PRODUCTION_MODE = False

# ==========================================
# 1. 核心基建与中间件
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册业务模块
app.include_router(nn_router)
app.include_router(llm_router)
app.include_router(data_center_router)


@app.on_event("startup")
def on_startup():
    init_db()
    print("📦 数据库与 SAEA 引擎初始化完成")


@app.get("/api/env_info")  # 如果你用的是 router，这里就是 @router.get
async def get_system_env_info():
    try:
        # 1. 侦测 Python 环境
        py_version = sys.version.split(' ')[0]
        is_conda = os.path.exists(os.path.join(sys.prefix, 'conda-meta')) or "conda" in sys.version.lower()
        env_type = "Conda" if is_conda else "Native"

        # 2. 侦测 PyTorch 版本 (修复 CUDA CPU 错误)
        try:
            import torch
            # 严格判断是否真实拥有 CUDA
            if torch.cuda.is_available() and torch.version.cuda:
                torch_info = f"{torch.__version__} (CUDA {torch.version.cuda})"
            else:
                clean_version = torch.__version__.split('+')[0]
                torch_info = f"{clean_version}+cpu (CPU Only)"
        except ImportError:
            torch_info = "Not Installed"

        # 3. 侦测 CST 版本 (改良版：全盘扫描环境变量的 Value 路径)
        cst_info = "CST Studio Suite (Unknown)"
        for key, value in os.environ.items():
            # 只要环境变量的 Key 或 Value 里面包含 CST
            if "CST" in key.upper() or "CST" in value.upper():
                # 用正则去抓取紧跟在后面的 4 位年份数字 (例如 C:\Program Files\CST Studio Suite 2024)
                match = re.search(r'(?:CST Studio Suite|CST).*?(\d{4})', value, re.IGNORECASE)
                if not match:
                    # 如果 Value 里没有，再去 Key 里找找看
                    match = re.search(r'(?:CST Studio Suite|CST).*?(\d{4})', key, re.IGNORECASE)

                if match:
                    cst_info = f"CST Studio Suite {match.group(1)} (AMD64)"
                    break

        return {
            "status": "success",
            "data": {
                "python": f"{py_version} ({env_type})",
                "pytorch": torch_info,
                "cst": cst_info
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
# ==========================================
# 2. 生产环境静态文件托管 (方案 2 的核心)
# ==========================================
if IS_PRODUCTION_MODE:
    dist_path = os.path.join(os.path.dirname(__file__), "dist")

    if os.path.exists(dist_path):
        # 1. 挂载编译后的静态资源 (js, css, images)
        app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")


        # 2. 智能捕获：所有非 /api 的 GET 请求全部导向 index.html
        # 这确保了在公网刷新页面时，Vue Router 能正常接管路由
        @app.get("/{catchall:path}")
        async def serve_vue_app(catchall: str):
            # 如果请求的是物理存在的文件，则直接返回
            full_path = os.path.join(dist_path, catchall)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                return FileResponse(full_path)
            # 否则返回入口文件
            return FileResponse(os.path.join(dist_path, "index.html"))
    else:
        print("⚠️ 警告: 未找到 dist 文件夹，请先执行 npm run build")


def get_config_filename(cst_path: str):
    """根据路径生成唯一且固定的配置文件名，并存入专属文件夹"""
    # 如果 configs 文件夹不存在，系统自动帮你建一个
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    if not cst_path:
        return os.path.join(CONFIG_DIR, "conf_unknown.json")

    norm_path = os.path.normpath(cst_path.strip()).lower()
    path_hash = hashlib.md5(norm_path.encode('utf-8')).hexdigest()
    pure_name = os.path.splitext(os.path.basename(cst_path))[0]

    # 拼装文件名
    filename = f"conf_{pure_name}_{path_hash[:8]}.json"

    # 返回带 configs 文件夹前缀的绝对路径
    return os.path.join(CONFIG_DIR, filename)

@app.post("/api/save_config")
async def api_save_config(config: OptimizationConfig):
    """保存前端当前的完整配置到本地 JSON"""
    try:
        config_dict = config.model_dump()
        filename = get_config_filename(config_dict['cstPath'])
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
        return {"status": "success", "message": f"配置已保存至 {filename}"}
    except Exception as e:
        return Response(status_code=500, content=str(e))

class LoadConfigRequest(BaseModel):
    cstPath: str


@app.get("/api/get_task_data/{task_id}")
async def get_task_data(task_id: str):
    """供前端刷新页面时，一键恢复所有历史数据（动态 JSON 版）"""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"status": "error", "message": "任务不存在"}

        # 1. 提取所有个体的散点数据 (修复核心：填补缺失的 scatter_data)
        inds = db.query(Individual).filter(Individual.task_id == task_id).all()
        scatter_data = [{
            "gen": ind.gen_index,
            "ind": ind.ind_index,
            "score": ind.score,
            "metrics": ind.metrics_json or {},
            "params": ind.params_json or {}
        } for ind in inds]

        #  2. 提取波形池数据
        waves = db.query(Waveform).filter(Waveform.task_id == task_id).all()
        all_data_pool = {}
        for w in waves:
            g, i = w.gen_index, w.ind_index
            if str(g) not in all_data_pool:
                all_data_pool[str(g)] = {}

            wave_dict = w.waves_json or {}
            # 从个体列表中找到对应的参数，挂载到波形字典上，供前端波形审查台显示
            match_ind = next((x for x in inds if x.gen_index == g and x.ind_index == i), None)
            if match_ind:
                wave_dict["params"] = match_ind.params_json or {}

            all_data_pool[str(g)][str(i)] = wave_dict

        # 3. 提取收敛趋势数据 (动态多目标自适应)
        gens = db.query(Generation).filter(Generation.task_id == task_id).order_by(Generation.gen_index).all()
        trend_data = {"axis": [g.gen_index for g in gens]}

        # 根据配置 JSON 动态初始化目标的空列表 (如 "效率": [], "频率": [])
        targets = []
        if task.config_json and "targetsList" in task.config_json:
            targets = [t["name"] for t in task.config_json["targetsList"]]

        for t_name in targets:
            trend_data[t_name] = []

        # 遍历代数，将对应的指标填入
        for g in gens:
            metrics = g.best_metrics_json or {}
            for t_name in targets:
                # 容错处理：如果旧数据没这个指标，就给 0
                trend_data[t_name].append(metrics.get(t_name, 0.0))

        # 提取总代数兜底
        total_gen = 50
        if task.config_json and "algo" in task.config_json:
            total_gen = task.config_json["algo"].get("nGen", 50)

        return {
            "status": "success",
            "config_json": task.config_json,
            "total_gen": getattr(task, "total_gen", total_gen),
            "scatter_data": scatter_data,
            "trend_data": trend_data,
            "all_data_pool": all_data_pool
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"后端解析数据异常: {str(e)}"}
    finally:
        db.close()

@app.post("/api/load_config")
async def api_load_config(req: LoadConfigRequest):
    """前端输入路径后，尝试加载本地的历史配置"""   
    filename = get_config_filename(req.cstPath)
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
            return {"status": "success", "config": saved_config}
        except Exception as e:
            return {"status": "error", "message": f"读取损坏: {str(e)}"}
    return {"status": "not_found", "message": "未找到历史配置"}
# ==========================================
# 2. WebSocket 连接管理器 (实时通信枢纽)
# ==========================================
class ConnectionManager:
    def __init__(self):
        # 字典结构: {"sim_12345": [ws1, ws2], "sim_67890": [ws3]}
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)

    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            # 如果房间里没前端了，就把房间销毁防内存泄漏
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def send_to_task(self, message: str, task_id: str):
        """精准推送：只发给订阅了当前 task_id 的浏览器网页"""
        if task_id in self.active_connections:
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"WS 发送异常 [任务 {task_id}]: {e}")


# 实例化全局管理器
manager = ConnectionManager()
task_status_flags = {}

class CstPathRequest(BaseModel):
    cstPath: str

@app.get("/api/get_running_task")
def get_running_task():
    """新增：供前端刷新重连使用，检查是否有正在运行的后台任务"""
    for task_id, status in task_status_flags.items():
        if status == "running":
            return {"status": "success", "task_id": task_id}
    return {"status": "none"}


@app.post("/api/stop_optimization/{task_id}")
async def stop_optimization(task_id: str):
    """前端调用此接口强制停止指定任务"""
    if task_id in task_status_flags:
        task_status_flags[task_id] = "stopped"
        return {"status": "success", "message": "已发送终止指令，引擎将在当前个体算完后安全退出"}

    # 修复：防御性编程，就算前端传入的 ID 不对，也强制把内存里所有任务停掉
    for k in task_status_flags.keys():
        task_status_flags[k] = "stopped"
    return {"status": "success", "message": "已广播全局终止指令"}

@app.post("/api/parse_cst_params")
async def api_parse_cst_params(req: CstPathRequest):
    """供前端调用的提取变量接口"""
    from engine.cst_wrapper import parse_cst_parameters
    params = parse_cst_parameters(req.cstPath)
    if params:
        return {"status": "success", "params": params}
    else:
        return {"status": "error", "message": "未找到有效变量或目录不存在"}


@app.get("/api/browse_cst")
def browse_cst_file():
    """
    唤起 Windows 原生资源管理器，获取绝对路径
    """
    try:
        # === 核心修复：强制开启 Windows 高 DPI 适配 ===
        if platform.system() == 'Windows':
            import ctypes
            try:
                # 针对 Windows 8.1 及以上版本
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                try:
                    # 针对旧版 Windows
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
        # =================================================

        # 初始化隐藏窗口
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        file_path = filedialog.askopenfilename(
            title="请选择 CST 项目文件",
            filetypes=[("CST Studio Files", "*.cst"), ("All Files", "*.*")]
        )

        root.destroy()

        if file_path:
            norm_path = os.path.normpath(file_path)
            return {"status": "success", "path": norm_path}
        else:
            return {"status": "cancelled", "message": "用户取消了选择"}

    except Exception as e:
        return {"status": "error", "message": f"弹窗失败: {str(e)}"}
# ==========================================
# 3. HTTP 路由: 任务控制与状态
# ==========================================
@app.get("/api/health")
async def health_check():
    """终极健康检查：环境变量测 CST + 进程快照测 Agents"""

    # 1. CST 探针：检测环境变量或默认路径
    cst_alive = False
    try:
        for key, value in os.environ.items():
            if "CST" in key.upper() or "CST" in value.upper():
                cst_alive = True
                break

        if not cst_alive:
            env_cst_path = os.getenv("CST_PYTHON_PATH", "")
            common_paths = [
                env_cst_path,  # 优先探测配置文件或终端引导填写的路径
                r"C:\Program Files (x86)\CST Studio Suite 2024",
                r"C:\Program Files (x86)\CST Studio Suite 2023",
                r"C:\Program Files\CST Studio Suite 2024"
            ]
            for p in common_paths:
                if p and os.path.exists(p):
                    cst_alive = True
                    break
    except Exception:
        cst_alive = False

    # 2. Agents (OpenClaw) 探针：纯物理进程扫描
    agents_alive = False
    try:
        # 遍历当前计算机所有正在运行的进程
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline') or []
                name = proc.info.get('name') or ""

                # 将进程名和启动命令拼接起来转小写，寻找 openclaw 的身影
                # 不管它是以 python -m openclaw 启动，还是以 openclaw.exe 启动，都能抓到
                full_cmd = " ".join(cmdline).lower() + " " + name.lower()

                if "openclaw" in full_cmd:
                    agents_alive = True
                    break  # 只要抓到一个活着的进程，直接亮灯并结束扫描
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # 忽略权限不足或已退出的幽灵进程
                continue
    except Exception:
        agents_alive = False

    return {
        "status": "ok",
        "cst_alive": cst_alive,
        "agents_alive": agents_alive
    }


@app.get("/api/system_status")
def get_system_status():
    """实时读取当前服务器硬件占用 (真实探针)"""
    try:
        # interval=0.1 防止第一次获取为0，用极短的阻塞换取真实的瞬时 CPU 负载
        return {
            "status": "success",
            "cpu": psutil.cpu_percent(interval=0.1),
            "ram": psutil.virtual_memory().percent
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/recent_tasks")
def get_recent_tasks(task_type: str = Query("all", description="任务类型: all, opt, sweep 或 nn")):
    """从数据库读取最近的 5 次历史任务及其真实进度 (智能兼容全类型)"""
    db = SessionLocal()
    try:
        query = db.query(Task)
        # 根据请求隔离类型，如果是 all 则全盘扫描
        if task_type == "sweep":
            query = query.filter(Task.id.like("sweep_%"))
        elif task_type == "opt":
            query = query.filter(Task.id.like("sim_%"))
        elif task_type == "nn":
            query = query.filter(Task.id.like("nn_%"))

        tasks = query.order_by(desc(Task.created_at)).limit(5).all()

        result = []
        for t in tasks:
            is_sweep = t.id.startswith("sweep_")
            is_nn = t.id.startswith("nn_")

            # 1. 动态界定当前任务属于哪条业务线
            task_category = "sweep" if is_sweep else ("nn" if is_nn else "opt")

            # 2. 智能提取当前进度 (Current Progress)
            if is_sweep:
                # 扫参任务没有 Generation，进度等于跑完的个体数 (ind_index)
                current_progress = db.query(func.max(Individual.ind_index)).filter(
                    Individual.task_id == t.id).scalar() or 0
                max_score = None  # 扫参无冠军分数
            else:
                # 优化与在线学习，进度看已完成的代数 (gen_index)
                current_progress = db.query(func.max(Generation.gen_index)).filter(
                    Generation.task_id == t.id).scalar() or 0
                max_score = db.query(func.max(Generation.best_score)).filter(Generation.task_id == t.id).scalar()

            # 3. 智能计算总任务量 (Total Progress)
            total_progress = 50
            if t.config_json:
                if is_sweep:
                    sweep_vars = [v for v in t.config_json.get('paramsList', []) if v.get('isSweep')]
                    total_progress = 1
                    for v in sweep_vars:
                        total_progress *= int(v.get('points', 1))
                elif 'algo' in t.config_json:
                    total_progress = t.config_json['algo'].get('nGen', 50)

            result.append({
                "id": t.id,
                "name": t.name,
                "status": t.status,
                "type": task_category,  # 告诉前端这是什么任务
                "currentGen": current_progress,
                "totalGen": total_progress,
                "bestEff": f"Score: {max_score:.2e}" if max_score is not None else "--"
            })
        return {"status": "success", "tasks": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@app.post("/api/start_sweep")
async def start_sweep(config: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    接收前端发来的配置，准备启动网格化扫参引擎
    """
    try:
        # 获取当前事件循环
        loop = asyncio.get_running_loop()

        # 强制清空并停止当前正在运行的其他任务（互斥锁）
        for k in task_status_flags.keys():
            task_status_flags[k] = "stopped"

        # 生成唯一的扫参任务 ID
        task_id = f"sweep_{int(asyncio.get_event_loop().time())}"

        # 提前在数据库中建立 Task 档案
        db = SessionLocal()
        try:
            new_task = Task(
                id=task_id,
                name=config.get('taskName', 'Unnamed_Sweep'),
                cst_path=config.get('cstPath', ''),
                config_json={**config, "task_type": "sweep"},  # 打上 sweep 烙印
                status="running"
            )
            db.add(new_task)
            db.commit()
        except Exception as db_e:
            db.rollback()
            print(f"创建扫参任务记录失败: {db_e}")
            return Response(status_code=500, content=f"Database error: {str(db_e)}")
        finally:
            db.close()

        # 更新全局状态字典
        task_status_flags[task_id] = "running"
        print(f"收到扫参任务: {config.get('taskName')} | 分配 ID: {task_id}")

        # 投递到后台异步执行，绝不阻塞当前 HTTP 响应
        background_tasks.add_task(run_sweep_task, task_id, config, manager, loop, task_status_flags)

        return {"status": "success", "task_id": task_id, "message": "网格扫参引擎已成功启动..."}
    except Exception as e:
        return Response(status_code=500, content=f"Failed to start sweep task: {str(e)}")


@app.post("/api/start_optimization")
async def start_optimization(config: OptimizationConfig, background_tasks: BackgroundTasks):
    """
    接收前端发来的配置，准备启动 SAEA 算法引擎
    """
    try:
        # 获取当前事件循环
        loop = asyncio.get_running_loop()

        # 将 Pydantic 对象转换为字典
        config_dict = config.model_dump()
        for k in task_status_flags.keys():
            task_status_flags[k] = "stopped"

        # 生成唯一任务 ID
        task_id = f"sim_{int(asyncio.get_event_loop().time())}"

        # 核心修复：必须在此处提前建立 Task 档案！
        db = SessionLocal()
        try:
            new_task = Task(
                id=task_id,
                name=config.taskName,
                cst_path=config.cstPath,
                config_json=config_dict,
                status="running"
            )
            db.add(new_task)
            db.commit()
        except Exception as db_e:
            db.rollback()
            print(f"创建任务记录失败: {db_e}")
            return Response(status_code=500, content=f"Database error: {str(db_e)}")
        finally:
            db.close()

        task_status_flags[task_id] = "running"
        print(f"收到优化任务: {config.taskName} | 分配 ID: {task_id}")

        # 将核心计算任务扔给后台执行
        background_tasks.add_task(run_optimization_task, task_id, config_dict, manager, loop, task_status_flags)

        return {"status": "success", "task_id": task_id, "message": "引擎指令已下发..."}
    except Exception as e:
        return Response(status_code=500, content=f"Failed to start task: {str(e)}")


@app.get("/api/get_model_image")
async def get_model_image(cst_path: str):
    """
    提取 CST 结构预览图
    """
    try:
        cst_dir = os.path.dirname(cst_path)
        pure_name = os.path.splitext(os.path.basename(cst_path))[0]
        dib_path = os.path.join(cst_dir, pure_name, "Model", "3D", "Model.dib")

        if os.path.exists(dib_path):
            img = Image.open(dib_path)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/png")
        else:
            return Response(status_code=404, content="Model.dib not found")
    except Exception as e:
        return Response(status_code=500, content=f"Image parse error: {str(e)}")


# ==========================================
# 4. WebSocket 路由: 实时日志与图表数据流
# ==========================================
@app.websocket("/ws/progress/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """前端通过传入专属的 task_id 建立连接"""
    await manager.connect(websocket, task_id)
    print(f"🟢 前端已连入专属频道: {task_id}")
    try:
        while True:
            # 保持连接不断开，等待前端可能发来的指令（例如中断任务）
            data = await websocket.receive_text()
            print(f"📩 收到频道 {task_id} 消息: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
        print(f"🔴 前端断开频道连接: {task_id}")



if __name__ == "__main__":
    import uvicorn
    # 生产模式下关闭 reload 以提高性能并防止 CST 频繁写文件导致进程重启
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=not IS_PRODUCTION_MODE
    )