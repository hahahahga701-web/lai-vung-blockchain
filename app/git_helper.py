import subprocess
import os
from datetime import datetime

def git_command(cmd_list, cwd=None):
    """
    Thực thi lệnh git và trả về kết quả.
    
    Args:
        cmd_list: Danh sách lệnh (ví dụ: ["git", "add", "."])
        cwd: Thư mục làm việc (mặc định là current directory)
    
    Returns:
        Tuple (success, output)
    """
    try:
        result = subprocess.run(
            cmd_list,
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output
    except Exception as e:
        return False, str(e)

def setup_git_config(cwd=None):
    """
    Cấu hình git toàn cục nếu chưa có (cho Render deployment).
    """
    # Cấu hình git user
    git_command(["git", "config", "user.email", "blockchain@example.com"], cwd=cwd)
    git_command(["git", "config", "user.name", "Blockchain Bot"], cwd=cwd)
    return True

def auto_commit_blockchain(filename="blockchain_ledger.json", cwd=None):
    """
    Tự động commit thay đổi blockchain vào git.
    
    Args:
        filename: Tên file cần commit (mặc định: blockchain_ledger.json)
        cwd: Thư mục làm việc
    
    Returns:
        Tuple (success, message)
    """
    if cwd is None:
        cwd = os.getcwd()
    
    # Kiểm tra nếu không phải git repo
    is_git_repo, _ = git_command(["git", "rev-parse", "--git-dir"], cwd=cwd)
    if not is_git_repo:
        return False, "Không phải git repository"
    
    # Cấu hình git nếu cần
    setup_git_config(cwd=cwd)
    
    # Thêm file vào staging area
    success, output = git_command(["git", "add", filename], cwd=cwd)
    if not success:
        return False, f"Lỗi thêm file: {output}"
    
    # Kiểm tra xem có thay đổi gì không
    status_success, status_output = git_command(["git", "status", "--porcelain"], cwd=cwd)
    if not status_output.strip():
        return True, "Không có thay đổi"
    
    # Commit thay đổi
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"🔗 Auto-commit blockchain update: {timestamp}"
    
    success, output = git_command(
        ["git", "commit", "-m", commit_msg],
        cwd=cwd
    )
    
    if not success:
        return False, f"Lỗi commit: {output}"
    
    # Push lên remote (nếu có)
    push_success, push_output = git_command(["git", "push"], cwd=cwd)
    
    if push_success:
        return True, f"✅ Commit và push thành công: {commit_msg}"
    else:
        # Nếu push thất bại, vẫn trả về thành công vì commit đã được thực hiện cục bộ
        return True, f"✅ Commit thành công (push thất bại: {push_output})"

def get_blockchain_history(filename="blockchain_ledger.json", max_commits=10, cwd=None):
    """
    Lấy lịch sử các commit liên quan đến blockchain.
    
    Returns:
        Danh sách các commit messages
    """
    if cwd is None:
        cwd = os.getcwd()
    
    success, output = git_command(
        ["git", "log", f"--max-count={max_commits}", "--oneline", "--", filename],
        cwd=cwd
    )
    
    if success:
        return [line.strip() for line in output.strip().split('\n') if line.strip()]
    return []
