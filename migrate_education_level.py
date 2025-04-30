from app import app, db
from models import Employee, EducationLevel
from sqlalchemy import text

def migrate_education_levels():
    """
    Script để di chuyển dữ liệu education_level từ định dạng chuỗi sang enum
    """
    with app.app_context():
        # Lấy tất cả các bản ghi nhân viên
        print("Đang cập nhật trình độ học vấn...")
        
        # Tiếp cận mới - Đặt trường education_level thành NULL trước, 
        # sau đó cập nhật thành giá trị enum
        db.session.execute(text("UPDATE employee SET education_level = NULL"))
        db.session.commit()
        
        # Lấy tất cả các nhân viên
        employees = Employee.query.all()
        print(f"Đã tìm thấy {len(employees)} nhân viên")
        
        # Cập nhật từng nhân viên
        for emp in employees:
            emp.education_level = EducationLevel.UNIVERSITY  # Giá trị mặc định
            db.session.add(emp)
        
        db.session.commit()
        print("Đã cập nhật tất cả nhân viên sang trình độ học vấn mặc định (Đại học)")
        
        print("Hoàn thành cập nhật trình độ học vấn!")
        print("Bạn có thể truy cập trang web bình thường.")

if __name__ == "__main__":
    migrate_education_levels()