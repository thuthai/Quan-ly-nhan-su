from app import app  # noqa: F401
import routes  # noqa: F401
import logging
from datetime import datetime
import threading
import time
from app import app, db
from notifications import check_expiring_contracts

# Cấu hình logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_expiring_contracts_task():
    """Task kiểm tra hợp đồng sắp hết hạn và gửi thông báo"""
    # Chờ 60 giây trước khi bắt đầu kiểm tra (đảm bảo ứng dụng đã khởi động hoàn toàn)
    time.sleep(60)
    
    while True:
        try:
            with app.app_context():
                logger.info("Đang kiểm tra hợp đồng sắp hết hạn...")
                check_expiring_contracts(days_threshold=30)
                logger.info("Đã hoàn thành kiểm tra hợp đồng sắp hết hạn.")
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra hợp đồng sắp hết hạn: {e}")

        # Chờ 24 giờ trước khi kiểm tra lần tiếp theo
        time.sleep(24 * 60 * 60)  # 24 giờ

if __name__ == "__main__":
    # Khởi tạo task kiểm tra hợp đồng sắp hết hạn
    contracts_checker_thread = threading.Thread(
        target=check_expiring_contracts_task,
        daemon=True  # Daemon thread sẽ tự động kết thúc khi ứng dụng chính kết thúc
    )
    contracts_checker_thread.start()
    
    app.run(host="0.0.0.0", port=5000, debug=True)
