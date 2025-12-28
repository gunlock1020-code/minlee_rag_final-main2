import os
import shutil
import uuid
import subprocess
import logging
import urllib.parse
import sys
import glob
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles  # ✅ 關鍵修正：引入 StaticFiles
from utils import load_config

# 1. 設定日誌紀錄 (Logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BOM-RAG-API")

app = FastAPI(title="BOM RAG API")

# 2. 設定跨域資源共享 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 初始化路徑與設定
config = load_config()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 暫存上傳目錄
UPLOAD_DIR = os.path.join(BASE_DIR, "temp_uploads")

# 產出目錄處理
output_folder_config = config['PATHS'].get('output_folder', 'output')
if os.path.isabs(output_folder_config):
    OUTPUT_DIR = output_folder_config
else:
    rel_path = output_folder_config.replace('./', '').replace('.\\', '')
    OUTPUT_DIR = os.path.join(BASE_DIR, rel_path)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================
#  ✅ 新增：網頁與靜態檔案路由 (解決 Not Found 問題)
# ==========================================

# 1. 輔助函式：取得 index.html
async def get_index():
    file_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    # 如果找不到網頁，才回傳原本的 API 狀態 JSON
    return JSONResponse(content={
        "status": "BOM RAG API is running", 
        "output_dir": OUTPUT_DIR,
        "warning": "index.html not found in server root"
    })

# 2. 根目錄路由 -> 優先顯示網頁
@app.get("/")
async def read_root():
    return await get_index()

# 3. 明確的 index.html 路由
@app.get("/index.html")
async def read_index_explicit():
    return await get_index()

# 4. (選用) 掛載 static 資料夾 (若您的網頁有引用 css/js)
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"已掛載靜態目錄: {static_dir}")

# ==========================================
#  核心邏輯
# ==========================================

@app.post("/generate-sop")
async def generate_sop(file: UploadFile = File(...)):
    """
    接收檔案並呼叫 RAG 程序
    """
    file_id = str(uuid.uuid4())
    original_filename = file.filename
    # 修正：處理沒有副檔名的情況
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower() if ext else ""
    
    if ext not in ['.xlsx', '.xls', '.pdf']:
        # 允許上傳但給予警告
        logger.warning(f"收到非標準格式檔案: {original_filename}")

    temp_input_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    
    try:
        # 儲存上傳的檔案
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"檔案已接收: {original_filename} -> {temp_input_path}")
        
        # 4. 執行子程序 (強制 UTF-8 環境)
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        
        logger.info(f"啟動子程序處理: {temp_input_path}")
        
        # 紀錄執行前的輸出目錄狀態
        files_before = set(os.listdir(OUTPUT_DIR))

        # Windows 下使用 subprocess 捕捉輸出，若 stdout 仍是亂碼，嘗試強制解碼
        process = subprocess.run(
            [sys.executable, 'query_and_generate.py', temp_input_path],
            capture_output=True,
            text=True,
            errors='replace', 
            env=my_env,
            cwd=BASE_DIR
        )

        # 改進：將子程序輸出以 UTF-8 重新處理並印出，解決終端機顯示問題
        if process.stdout:
            print("\n--- [AI 子程序輸出內容] ---")
            print(process.stdout)
            print("---------------------------\n")

        if process.returncode != 0:
            logger.error(f"子程序執行崩潰 (Code: {process.returncode})")
            if process.stderr: print(f"--- [錯誤訊息] ---\n{process.stderr}")
            return {
                "success": False, 
                "error": "AI 程序執行失敗", 
                "stdout": process.stdout, 
                "stderr": process.stderr
            }

        # 5. 尋找新生成的檔案 (動態偵測)
        files_after = set(os.listdir(OUTPUT_DIR))
        new_files = files_after - files_before
        
        # 優先尋找符合模式的新檔案
        sop_files = [f for f in new_files if f.startswith('SOP_') and f.endswith('.xlsx')]
        
        actual_output_filename = None
        if sop_files:
            actual_output_filename = sorted(sop_files, key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)[0]
        elif new_files:
            xlsx_files = [f for f in new_files if f.endswith('.xlsx')]
            if xlsx_files:
                actual_output_filename = sorted(xlsx_files, key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)[0]

        if actual_output_filename:
            logger.info(f"成功偵測到新產出的檔案: {actual_output_filename}")
            # 使用 URL 安全的編碼方式
            encoded_filename = urllib.parse.quote(actual_output_filename)
            return {
                "success": True,
                "filename": actual_output_filename,
                "download_url": f"/download/{encoded_filename}"
            }
        else:
            logger.error("找不到任何新生成的 Excel 檔案")
            return {
                "success": False, 
                "error": "找不到生成的產出檔案",
                "stdout": process.stdout
            }
            
    except Exception as e:
        logger.exception("API 伺服器異常")
        return {"success": False, "error": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    decoded_filename = urllib.parse.unquote(filename)
    safe_filename = os.path.basename(decoded_filename)
    file_path = os.path.join(OUTPUT_DIR, safe_filename)
    
    if not os.path.exists(file_path):
        logger.error(f"下載失敗: 檔案不存在於 {file_path}")
        raise HTTPException(status_code=404, detail="檔案不存在")

    # 返回 FileResponse 並強制指定下載名
    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == "__main__":
    import uvicorn
    # 這裡設定跑在 8000 port
    uvicorn.run(app, host="0.0.0.0", port=8000)