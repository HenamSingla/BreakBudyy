# BreakBudyy

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

