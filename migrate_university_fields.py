from app import app, db
from sqlalchemy import text

def migrate_university_fields():
    """
    Script để thêm các trường thông tin đại học (university_name, university_major) vào bảng employee
    """
    with app.app_context():
        # Thêm trường university_name vào bảng employee
        try:
            print("Đang thêm trường university_name vào bảng employee...")
            db.session.execute(text("ALTER TABLE employee ADD COLUMN IF NOT EXISTS university_name VARCHAR(200)"))
            db.session.commit()
            print("Đã thêm trường university_name thành công!")
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi thêm trường university_name: {str(e)}")
        
        # Thêm trường university_major vào bảng employee
        try:
            print("Đang thêm trường university_major vào bảng employee...")
            db.session.execute(text("ALTER TABLE employee ADD COLUMN IF NOT EXISTS university_major VARCHAR(200)"))
            db.session.commit()
            print("Đã thêm trường university_major thành công!")
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi khi thêm trường university_major: {str(e)}")
        
        print("Đã hoàn thành cập nhật cấu trúc bảng employee!")
        print("Bạn có thể truy cập trang web bình thường bây giờ.")

if __name__ == "__main__":
    migrate_university_fields()