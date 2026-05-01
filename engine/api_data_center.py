import os
import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import text

from database import SessionLocal, Task, Individual, Generation, Waveform, NnOnlineLog, DB_PATH

router = APIRouter(prefix="/api", tags=["DataCenter"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.created_at.desc()).all()


@router.get("/tasks/{task_id}/individuals")
def get_task_individuals(task_id: str, db: Session = Depends(get_db)):
    individuals = db.query(Individual).filter(Individual.task_id == task_id).order_by(Individual.gen_index,
                                                                                      Individual.ind_index).all()
    total_inds = len(individuals)
    max_gen = db.query(func.max(Individual.gen_index)).filter(Individual.task_id == task_id).scalar() or 0
    db_size_mb = round(os.path.getsize(DB_PATH) / (1024 * 1024), 2) if os.path.exists(DB_PATH) else 0

    return {
        "individuals": individuals,
        "stats": {"totalGens": max_gen, "totalInds": total_inds, "storage": db_size_mb}
    }


@router.get("/individuals/{individual_id}/waveform")
def get_individual_waveform(individual_id: int, db: Session = Depends(get_db)):
    wave = db.query(Waveform).filter(Waveform.individual_id == individual_id).first()
    if not wave or not wave.waves_json:
        raise HTTPException(status_code=404, detail="该个体由于报错等原因，未能生成波形数据")

    return {
        "status": "success",
        "waveforms": wave.waves_json
    }


@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.query(Waveform).filter(Waveform.task_id == task_id).delete(synchronize_session=False)
    db.query(Individual).filter(Individual.task_id == task_id).delete(synchronize_session=False)
    db.query(Generation).filter(Generation.task_id == task_id).delete(synchronize_session=False)
    db.delete(task)
    db.commit()
    db.execute(text("VACUUM"))
    db.commit()
    return {"status": "success"}


@router.get("/tasks/{task_id}/export")
def export_to_excel(task_id: str, db: Session = Depends(get_db)):
    inds = db.query(Individual).filter(Individual.task_id == task_id).order_by(Individual.gen_index,
                                                                               Individual.ind_index).all()
    if not inds:
        raise HTTPException(status_code=404, detail="无数据可导出")

    data_list = []
    for ind in inds:
        row = {
            "代数(Gen)": ind.gen_index, "个体编号(No.)": ind.ind_index,
            "综合得分": ind.score, "是否有效(起振)": ind.is_valid
        }
        if ind.params_json:
            for k, v in ind.params_json.items():
                row[f"参数_{k}"] = v
        if ind.metrics_json:
            for k, v in ind.metrics_json.items():
                row[f"指标_{k}"] = v

        data_list.append(row)

    df = pd.DataFrame(data_list)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='CST_Opt_Data')

    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={'Content-Disposition': f'attachment; filename="SAEA_Task_{task_id}.xlsx"'}
    )

@router.get("/tasks/{task_id}/nn_logs")
def get_nn_logs(task_id: str, db: Session = Depends(get_db)):
    """获取神经网络在线微调曲线数据"""
    logs = db.query(NnOnlineLog).filter(NnOnlineLog.task_id == task_id).order_by(NnOnlineLog.gen_index).all()
    if not logs:
        raise HTTPException(status_code=404, detail="未找到微调日志")
    return [{"gen_index": log.gen_index, "loss": log.loss, "error": log.error} for log in logs]