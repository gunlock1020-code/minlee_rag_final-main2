# 📚 minlee_rag_final-main2

一個以 Python 實作的 **RAG（Retrieval‑Augmented Generation）應用專案**，透過文件檢索（Retrieval）結合大型語言模型（LLM），實現可根據既有資料回答問題的智慧系統。

---

## 🚀 專案簡介

本專案示範如何將結構化或半結構化資料（如 Excel、JSON）轉換為可搜尋的知識來源，並結合語言模型生成高品質回答，適合用於：

- 內部文件問答系統  
- BOM / 製造資料查詢  
- 企業知識庫輔助決策  
- RAG 架構學習與展示  

---

## 🧱 專案結構

```
minlee_rag_final-main2/
├── 123.xlsx                  # 範例原始資料
├── extract_bom_data.py       # Excel / BOM 資料擷取與轉換
├── extracted_data.json       # 轉換後的結構化資料
├── upload_to_mongodb.py      # 資料上傳至 MongoDB
├── query_and_generate.py     # 查詢 + 生成（RAG 核心邏輯）
├── gcp_api.py                # Google Cloud API 相關工具
├── utils.py                  # 共用工具函式
├── main.py                   # 專案主程式入口
├── index.html                # 簡易前端頁面（如有使用）
├── requirements.txt          # Python 套件需求
└── README.md                 # 專案說明文件
```

---

## ⚙️ 安裝與環境設定

### 1️⃣ 下載專案

```bash
git clone https://github.com/gunlock1020-code/minlee_rag_final-main2.git
cd minlee_rag_final-main2
```

### 2️⃣ 建立虛擬環境並安裝套件

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔑 環境變數設定

若使用外部服務（如 OpenAI、GCP、MongoDB），請設定環境變數：

```bash
OPENAI_API_KEY=你的_API_KEY
MONGODB_URI=你的_MongoDB_連線字串
```

（可放在 `.env` 檔或系統環境變數中）

---

## 🧠 使用流程說明

### Step 1：資料處理

將 Excel 或原始資料轉換為 JSON：

```bash
python extract_bom_data.py
```

### Step 2：上傳資料至資料庫

```bash
python upload_to_mongodb.py
```

### Step 3：執行 RAG 查詢與生成

```bash
python main.py
```

或單獨測試查詢模組：

```bash
python query_and_generate.py
```

---

## 🧩 RAG 架構說明（簡化）

1. 使用者輸入問題  
2. 問題轉換為向量（Embedding）  
3. 從資料庫檢索最相關資料  
4. 將檢索結果作為 Context  
5. 交由 LLM 生成最終回答  

---

## 🛠️ 技術堆疊

- Python  
- Retrieval‑Augmented Generation (RAG)  
- MongoDB（資料儲存 / 向量搜尋）  
- Large Language Model（OpenAI / GCP / Local LLM）  

---

## 📌 注意事項

- 請勿將 API Key 上傳至 GitHub  
- 大型資料請注意向量建立與查詢效能  
- 可依需求替換不同 LLM 或向量資料庫  

---

## 📄 License

此專案目前未指定 License，可依需求新增（如 MIT License）。

---

## 🙌 作者

專案維護者：**鈞揚 郭**

歡迎 Issue、PR 與交流 🙌
