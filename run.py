import uvicorn
import os
from app.git_helper import setup_git_config

# Version: 1.1.0 - QR Code fix deployed
if __name__ == "__main__":
    print("==================================================================")
    print("Starting Lai Vung Mandarin Traceability Network...")
    
    print("Cau hinh Git auto-commit cho blockchain...")
    setup_git_config()
    print("Git config ready")
    
    port = int(os.getenv("PORT", "8000"))
    print(f"API & Web Portal running at: http://localhost:{port}")
    print("==================================================================")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
