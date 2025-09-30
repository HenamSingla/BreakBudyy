# BreakBudyy

<img width="943" height="957" alt="BreakBuddy Screen" src="https://github.com/user-attachments/assets/f7114993-4ec6-4958-bd78-2ba5d1ef57d0" />


SmartPTO is a **hackathon demo app** that helps employees plan their paid time off (PTO) more effectively.  
It combines a **FastAPI backend** and a **Streamlit frontend**, with sliders for PTO preferences and a simple recommendation engine.  

---

## Features
- ✅ **FastAPI backend** serving:
  - `/health` — health check  
  - `/balance` — PTO accrual balance lookup  
  - `/recommend` — suggested PTO windows  
- ✅ **Streamlit frontend** for employees to:
  - View their current PTO balance  
  - Adjust sliders for **desired PTO length**, **planning horizon**, and **coverage ratio**  
  - See recommended leave windows  
  - Export PTO to calendar (`.ics` file)  
- ✅ **Fallback recommendations** if API is down  
- ✅ Demo employees hardcoded (`Henam` etc.)  

---

## 📦 Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-repo/breakbudyy.git
cd breakbudyy
```

### 2. Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

### 3. Frontend (Streamlit)
```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 🎯 Demo Flow

1. Launch backend (FastAPI)  
2. Launch frontend (Streamlit)  
3. Select an employee from the dropdown  
4. Adjust PTO sliders (desired days, coverage ratio, etc.)  
5. See recommended PTO windows  
6. Export as `.ics` calendar invite  

