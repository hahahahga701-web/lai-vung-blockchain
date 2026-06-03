import uvicorn
import os
import sys
import io
from app.git_helper import setup_git_config

# Safe encoding for console output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Fallback for older Python versions
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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
