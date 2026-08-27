import os
import sys
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from excel_manager import ExcelManager
from search_engine import search_company_phone_deep
from ai_analyst import analyze_company_ai
from find_service import lookup_company_on_find

app = FastAPI(title="10K Phone Finder Agent Local Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScannerState:
    def __init__(self):
        self.current_file: Optional[str] = None
        self.excel_manager: Optional[ExcelManager] = None
        self.is_scanning: bool = False
        self.stop_requested: bool = False

state = ScannerState()

frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
frontend_assets = os.path.join(frontend_dist, "assets")

if os.path.exists(frontend_assets):
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")

os.makedirs("static", exist_ok=True)

class CellUpdateRequest(BaseModel):
    row_index: int
    column_name: str
    new_value: str

class AIInfoRequest(BaseModel):
    company_name: str
    location: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

class FindLookupRequest(BaseModel):
    company_name: str
    location: Optional[str] = None

@app.get("/api/files")
async def list_files():
    files = [
        f for f in os.listdir('.') 
        if f.endswith(('.xlsx', '.xls', '.csv')) 
        and not f.endswith(('_telefon_sonuclari.xlsx', '_telefon_sonuclari.csv'))
    ]
    return {"files": files}

def _parse_file_worker(file_path: str):
    state.current_file = file_path
    state.excel_manager = ExcelManager(file_path)
    mgr = state.excel_manager
    
    company_col = mgr.detect_company_column()
    location_col = mgr.detect_location_column()
    officer_col = mgr.detect_officer_column()
    
    pending = mgr.get_pending_indices()
    unfound = mgr.get_unfound_indices()
    total = len(mgr.df)
    completed = total - len(pending)
    found = len(mgr.df[mgr.df['Durum'] == 'Tamamlandı'])
    not_found = len(mgr.df[mgr.df['Durum'] == 'Bulunamadı'])
    preview = mgr.df.head(100).to_dict(orient="records")
    
    return {
        "filename": os.path.basename(file_path),
        "filepath": file_path,
        "columns": list(mgr.df.columns),
        "detected_column": company_col,
        "detected_location_column": location_col,
        "detected_officer_column": officer_col,
        "total_rows": total,
        "completed_rows": completed,
        "found_count": found,
        "not_found_count": not_found,
        "pending_count": len(pending),
        "unfound_count": len(unfound),
        "preview": preview,
        "output_file": os.path.basename(mgr.output_file)
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(os.getcwd(), file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _parse_file_worker, file_path)
    return result

@app.post("/api/select_file")
async def select_file(filename: str):
    file_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _parse_file_worker, file_path)
    return result

@app.get("/api/table")
async def get_table_data(
    page: int = 1, 
    page_size: int = 50, 
    search: str = "", 
    filter_status: str = "all", 
    sort_by: str = "found_first"
):
    if not state.excel_manager or state.excel_manager.df is None:
        return {"rows": [], "total_rows": 0, "columns": []}
        
    df = state.excel_manager.df.copy()
    df['_row_idx'] = df.index
    
    if filter_status == "found":
        df = df[df['Durum'] == 'Tamamlandı']
    elif filter_status == "not_found":
        df = df[df['Durum'] == 'Bulunamadı']
    elif filter_status == "pending":
        df = df[df['Durum'] == 'Bekliyor']
        
    if search and search.strip():
        mask = df.astype(str).apply(lambda row: row.str.contains(search, case=False, na=False).any(), axis=1)
        df = df[mask]
        
    if sort_by == "found_first":
        def sort_key(status):
            if status == 'Tamamlandı':
                return 0
            elif status == 'Bekliyor':
                return 1
            return 2
        df['_sort_rank'] = df['Durum'].apply(sort_key)
        df = df.sort_values(by=['_sort_rank', '_row_idx'], ascending=[True, True])
        df = df.drop(columns=['_sort_rank'])

    total = len(df)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paged_df = df.iloc[start_idx:end_idx]
    
    all_cols = list(state.excel_manager.df.columns)
    priority_cols = ['Bulunan_Telefon', 'Durum', 'Neden_Bulunamadi', 'Telefon_Kaynak_URL']
    other_cols = [c for c in all_cols if c not in priority_cols and c != '_row_idx']
    ordered_cols = other_cols + priority_cols
    
    rows = paged_df.to_dict(orient="records")
        
    return {
        "rows": rows,
        "total_rows": total,
        "total_unfiltered": len(state.excel_manager.df),
        "found_total": len(state.excel_manager.df[state.excel_manager.df['Durum'] == 'Tamamlandı']),
        "not_found_total": len(state.excel_manager.df[state.excel_manager.df['Durum'] == 'Bulunamadı']),
        "pending_total": len(state.excel_manager.df[state.excel_manager.df['Durum'] == 'Bekliyor']),
        "columns": ordered_cols,
        "company_col": state.excel_manager.company_col,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 1
    }

@app.post("/api/update_cell")
async def update_cell(req: CellUpdateRequest):
    if not state.excel_manager or state.excel_manager.df is None:
        raise HTTPException(status_code=400, detail="Dosya yüklü değil")
        
    mgr = state.excel_manager
    if req.row_index < 0 or req.row_index >= len(mgr.df):
        raise HTTPException(status_code=400, detail="Geçersiz satır indeksi")
        
    if req.column_name not in mgr.df.columns:
        raise HTTPException(status_code=400, detail="Geçersiz sütun adı")
        
    mgr.df.at[req.row_index, req.column_name] = req.new_value
    
    if req.column_name == 'Bulunan_Telefon':
        if req.new_value.strip():
            mgr.df.at[req.row_index, 'Durum'] = "Tamamlandı"
            mgr.df.at[req.row_index, 'Neden_Bulunamadi'] = "Doğrulandı (Kullanıcı Tarafından)"
        else:
            mgr.df.at[req.row_index, 'Durum'] = "Bekliyor"
            mgr.df.at[req.row_index, 'Neden_Bulunamadi'] = ""
            
    mgr.save()
    return {"status": "success", "message": "Hücre güncellendi ve kaydedildi"}

@app.post("/api/find_lookup")
async def find_lookup(req: FindLookupRequest):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lookup_company_on_find, req.company_name, req.location)
    return result

@app.post("/api/delete_row")
async def delete_row(row_index: int = Query(...)):
    if not state.excel_manager or state.excel_manager.df is None:
        raise HTTPException(status_code=400, detail="Dosya yüklü değil")
        
    mgr = state.excel_manager
    if row_index < 0 or row_index >= len(mgr.df):
        raise HTTPException(status_code=400, detail="Geçersiz satır indeksi")
        
    mgr.df = mgr.df.drop(index=row_index).reset_index(drop=True)
    mgr.save()
    return {"status": "success", "total_rows": len(mgr.df)}

@app.post("/api/ai_company_info")
async def get_ai_company_info(req: AIInfoRequest):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, 
        analyze_company_ai, 
        req.company_name, 
        req.location, 
        req.phone, 
        req.website
    )
    return result

@app.get("/api/download")
async def download_results():
    if not state.excel_manager or not os.path.exists(state.excel_manager.output_file):
        raise HTTPException(status_code=404, detail="Henüz sonuç dosyası oluşturulmadı")
    return FileResponse(
        state.excel_manager.output_file,
        filename=os.path.basename(state.excel_manager.output_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "stop":
                state.stop_requested = True
                await websocket.send_json({"type": "status", "message": "Durduruldu"})
                continue
                
            if action == "start":
                if not state.excel_manager:
                    await websocket.send_json({"type": "error", "message": "Lütfen önce bir dosya yükleyin"})
                    continue
                    
                concurrency = int(data.get("concurrency", 15))
                deep_scan = bool(data.get("deep_scan", False))
                company_col = data.get("company_col", state.excel_manager.company_col)
                location_col = data.get("location_col")
                officer_col = data.get("officer_col", state.excel_manager.officer_col)
                mode = data.get("mode", "all")
                
                mgr = state.excel_manager
                mgr.company_col = company_col
                
                if mode == "reset_all":
                    mgr.reset_all_rows()
                    target_indices = list(range(len(mgr.df)))
                elif mode == "unfound":
                    target_indices = mgr.get_unfound_indices()
                else:
                    target_indices = mgr.get_pending_indices()
                    
                total_rows = len(mgr.df)
                
                if not target_indices:
                    await websocket.send_json({"type": "done", "message": "Taranacak satır kalmadı!", "output_file": os.path.basename(mgr.output_file)})
                    continue
                    
                state.is_scanning = True
                state.stop_requested = False
                
                done_count = 0
                start_time = time.time()
                save_batch = 15
                
                current_found = len(mgr.df[mgr.df['Durum'] == 'Tamamlandı'])
                current_not_found = len(mgr.df[mgr.df['Durum'] == 'Bulunamadı'])
                initial_completed = total_rows - len(mgr.get_pending_indices()) if mode != "unfound" else 0

                loop = asyncio.get_running_loop()

                def search_worker(idx):
                    if state.stop_requested:
                        return idx, None, None, "Durduruldu"
                    company_name = str(mgr.df.at[idx, company_col])
                    location_val = str(mgr.df.at[idx, location_col]) if location_col and location_col in mgr.df.columns else None
                    officer_val = str(mgr.df.at[idx, officer_col]) if officer_col and officer_col in mgr.df.columns else None
                    
                    phone, url, reason = search_company_phone_deep(
                        company_name, 
                        location=location_val, 
                        officer=officer_val,
                        deep_scan_sites=deep_scan
                    )
                    return idx, phone, url, reason

                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    tasks = [loop.run_in_executor(executor, search_worker, idx) for idx in target_indices]
                    
                    for completed_task in asyncio.as_completed(tasks):
                        if state.stop_requested:
                            break
                            
                        idx, phone, url, reason = await completed_task
                        prev_status = mgr.df.at[idx, 'Durum']
                        mgr.update_row(idx, phone, url, reason)
                        done_count += 1
                        
                        if phone:
                            if prev_status != 'Tamamlandı':
                                current_found += 1
                                if prev_status == 'Bulunamadı':
                                    current_not_found -= 1
                        else:
                            if prev_status != 'Bulunamadı' and prev_status != 'Tamamlandı':
                                current_not_found += 1
                                
                        if done_count % save_batch == 0 or done_count == len(target_indices):
                            mgr.save()
                            
                        elapsed = time.time() - start_time
                        speed = done_count / elapsed if elapsed > 0 else 0
                        tot_done = current_found + current_not_found
                        rate = (current_found / tot_done * 100) if tot_done > 0 else 0
                        
                        company_name = str(mgr.df.at[idx, company_col])
                        await websocket.send_json({
                            "type": "progress",
                            "done_count": done_count,
                            "target_count": len(target_indices),
                            "total_rows": total_rows,
                            "completed_rows": initial_completed + done_count if mode != "unfound" else total_rows - len(mgr.get_pending_indices()),
                            "found_count": current_found,
                            "not_found_count": max(0, current_not_found),
                            "success_rate": round(rate, 1),
                            "speed": round(speed, 1),
                            "latest_item": {
                                "index": idx,
                                "company": company_name,
                                "phone": phone or "—",
                                "url": url or "—",
                                "reason": reason,
                                "status": "Tamamlandı" if phone else "Bulunamadı"
                            }
                        })

                mgr.save()
                state.is_scanning = False
                await websocket.send_json({
                    "type": "done",
                    "message": "İşlem tamamlandı!",
                    "output_file": os.path.basename(mgr.output_file),
                    "found_count": current_found,
                    "not_found_count": max(0, current_not_found)
                })
                
    except WebSocketDisconnect:
        state.is_scanning = False
    except Exception as e:
        state.is_scanning = False

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    dist_index = os.path.join(frontend_dist, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False, access_log=False)
