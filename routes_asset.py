from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import Asset, AssetAssignment, AssetMaintenance, AssetStatus, AssetCategory, MaintenanceType, MaintenanceStatus, Employee
from forms_asset import AssetForm, AssetEditForm, AssetAssignmentForm, AssetReturnForm, AssetMaintenanceForm, AssetFilterForm
from werkzeug.utils import secure_filename
from datetime import datetime
import os

asset_bp = Blueprint('asset', __name__, url_prefix='/asset')


@asset_bp.route('/')
@login_required
def index():
    form = AssetFilterForm(request.args)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Asset.query
    
    # Áp dụng các bộ lọc
    if form.keyword.data:
        query = query.filter(
            (Asset.asset_code.ilike(f'%{form.keyword.data}%')) |
            (Asset.name.ilike(f'%{form.keyword.data}%')) |
            (Asset.serial_number.ilike(f'%{form.keyword.data}%'))
        )
    
    if form.category.data:
        query = query.filter(Asset.category == form.category.data)
    
    if form.status.data:
        query = query.filter(Asset.status == form.status.data)
    
    if form.purchase_date_from.data:
        query = query.filter(Asset.purchase_date >= form.purchase_date_from.data)
    
    if form.purchase_date_to.data:
        query = query.filter(Asset.purchase_date <= form.purchase_date_to.data)
    
    if form.price_min.data is not None:
        query = query.filter(Asset.purchase_price >= form.price_min.data)
    
    if form.price_max.data is not None:
        query = query.filter(Asset.purchase_price <= form.price_max.data)
    
    pagination = query.order_by(Asset.asset_code).paginate(page=page, per_page=per_page)
    assets = pagination.items
    
    return render_template('assets/index.html', 
                          assets=assets, 
                          pagination=pagination,
                          form=form,
                          title='Quản lý tài sản')


@asset_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = AssetForm()
    
    if form.validate_on_submit():
        asset = Asset(
            asset_code=form.asset_code.data,
            name=form.name.data,
            category=form.category.data,
            status=form.status.data,
            serial_number=form.serial_number.data,
            purchase_date=form.purchase_date.data,
            purchase_price=form.purchase_price.data,
            warranty_expiry=form.warranty_expiry.data,
            description=form.description.data,
            notes=form.notes.data
        )
        
        # Xử lý upload ảnh nếu có
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"asset_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/assets')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            image_path = os.path.join(uploads_dir, new_filename)
            form.image.data.save(image_path)
            asset.image_path = f"uploads/assets/{new_filename}"
        
        db.session.add(asset)
        db.session.commit()
        
        flash('Tài sản mới đã được tạo thành công!', 'success')
        return redirect(url_for('asset.index'))
    
    return render_template('assets/create.html', 
                          form=form, 
                          title='Thêm tài sản mới')


@asset_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    asset = Asset.query.get_or_404(id)
    form = AssetEditForm(obj=asset)
    form.asset_id.data = asset.id
    
    if form.validate_on_submit():
        asset.asset_code = form.asset_code.data
        asset.name = form.name.data
        asset.category = form.category.data
        asset.status = form.status.data
        asset.serial_number = form.serial_number.data
        asset.purchase_date = form.purchase_date.data
        asset.purchase_price = form.purchase_price.data
        asset.warranty_expiry = form.warranty_expiry.data
        asset.description = form.description.data
        asset.notes = form.notes.data
        
        # Xử lý upload ảnh mới nếu có
        if form.image.data:
            # Xóa ảnh cũ nếu có
            if asset.image_path:
                old_image_path = os.path.join(current_app.root_path, 'static', asset.image_path)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            filename = secure_filename(form.image.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"asset_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/assets')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            image_path = os.path.join(uploads_dir, new_filename)
            form.image.data.save(image_path)
            asset.image_path = f"uploads/assets/{new_filename}"
        
        db.session.commit()
        
        flash('Thông tin tài sản đã được cập nhật!', 'success')
        return redirect(url_for('asset.view', id=asset.id))
    
    return render_template('assets/edit.html', 
                          form=form, 
                          asset=asset,
                          title='Chỉnh sửa tài sản')


@asset_bp.route('/<int:id>')
@login_required
def view(id):
    asset = Asset.query.get_or_404(id)
    assignments = AssetAssignment.query.filter_by(asset_id=id).order_by(AssetAssignment.assigned_date.desc()).all()
    maintenance_records = AssetMaintenance.query.filter_by(asset_id=id).order_by(AssetMaintenance.maintenance_date.desc()).all()
    
    return render_template('assets/view.html', 
                          asset=asset, 
                          assignments=assignments,
                          maintenance_records=maintenance_records,
                          title=f'Chi tiết tài sản: {asset.name}')


@asset_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    asset = Asset.query.get_or_404(id)
    
    # Kiểm tra xem tài sản có đang được sử dụng không
    if asset.status == AssetStatus.ASSIGNED:
        flash('Không thể xóa tài sản đang được bàn giao!', 'danger')
        return redirect(url_for('asset.view', id=id))
    
    # Xóa ảnh nếu có
    if asset.image_path:
        image_path = os.path.join(current_app.root_path, 'static', asset.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Xóa các bản ghi liên quan
    AssetAssignment.query.filter_by(asset_id=id).delete()
    AssetMaintenance.query.filter_by(asset_id=id).delete()
    
    db.session.delete(asset)
    db.session.commit()
    
    flash('Tài sản đã được xóa thành công!', 'success')
    return redirect(url_for('asset.index'))


@asset_bp.route('/assign', methods=['GET', 'POST'])
@login_required
def assign():
    form = AssetAssignmentForm()
    
    if form.validate_on_submit():
        asset = Asset.query.get(form.asset_id.data)
        
        if asset.status != AssetStatus.AVAILABLE:
            flash('Tài sản này không khả dụng để bàn giao!', 'danger')
            return redirect(url_for('asset.assign'))
        
        assignment = AssetAssignment(
            asset_id=form.asset_id.data,
            employee_id=form.employee_id.data,
            assigned_date=form.assigned_date.data,
            condition_on_assignment=form.condition_on_assignment.data,
            notes=form.notes.data,
            assigned_by_id=current_user.id,
            is_returned=False
        )
        
        # Cập nhật trạng thái tài sản
        asset.status = AssetStatus.ASSIGNED
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Tài sản đã được bàn giao thành công!', 'success')
        return redirect(url_for('asset.view', id=form.asset_id.data))
    
    return render_template('assets/assign.html', 
                          form=form, 
                          title='Bàn giao tài sản')


@asset_bp.route('/assignments/<int:id>/return', methods=['GET', 'POST'])
@login_required
def return_asset(id):
    assignment = AssetAssignment.query.get_or_404(id)
    
    if assignment.is_returned:
        flash('Tài sản này đã được trả trước đó!', 'warning')
        return redirect(url_for('asset.view', id=assignment.asset_id))
    
    form = AssetReturnForm(obj=assignment)
    form.assignment_id.data = assignment.id
    
    if form.validate_on_submit():
        assignment.return_date = form.return_date.data
        assignment.condition_on_return = form.condition_on_return.data
        assignment.notes = form.notes.data if form.notes.data else assignment.notes
        assignment.is_returned = True
        
        # Cập nhật trạng thái tài sản
        asset = Asset.query.get(assignment.asset_id)
        asset.status = AssetStatus.AVAILABLE
        
        db.session.commit()
        
        flash('Tài sản đã được trả thành công!', 'success')
        return redirect(url_for('asset.view', id=assignment.asset_id))
    
    return render_template('assets/return.html', 
                          form=form, 
                          assignment=assignment,
                          title='Trả tài sản')


@asset_bp.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintenance():
    form = AssetMaintenanceForm()
    
    if form.validate_on_submit():
        maintenance = AssetMaintenance(
            asset_id=form.asset_id.data,
            maintenance_date=form.maintenance_date.data,
            maintenance_type=form.maintenance_type.data,
            performed_by=form.performed_by.data,
            cost=form.cost.data,
            description=form.description.data,
            status=form.status.data
        )
        
        # Cập nhật trạng thái tài sản nếu đang bảo trì
        if form.status.data == MaintenanceStatus.IN_PROGRESS.name:
            asset = Asset.query.get(form.asset_id.data)
            asset.status = AssetStatus.UNDER_MAINTENANCE
        
        db.session.add(maintenance)
        db.session.commit()
        
        flash('Bản ghi bảo trì đã được tạo thành công!', 'success')
        return redirect(url_for('asset.view', id=form.asset_id.data))
    
    return render_template('assets/maintenance.html', 
                          form=form, 
                          title='Thêm bảo trì tài sản')


@asset_bp.route('/maintenance/<int:id>/complete', methods=['POST'])
@login_required
def complete_maintenance(id):
    maintenance = AssetMaintenance.query.get_or_404(id)
    
    if maintenance.status == MaintenanceStatus.COMPLETED.name:
        flash('Bảo trì này đã được hoàn thành!', 'warning')
        return redirect(url_for('asset.view', id=maintenance.asset_id))
    
    maintenance.status = MaintenanceStatus.COMPLETED.name
    
    # Kiểm tra xem còn bảo trì đang thực hiện nào không
    ongoing_maintenance = AssetMaintenance.query.filter_by(
        asset_id=maintenance.asset_id, 
        status=MaintenanceStatus.IN_PROGRESS.name
    ).first()
    
    # Nếu không còn bảo trì nào đang thực hiện, cập nhật trạng thái tài sản
    if not ongoing_maintenance:
        asset = Asset.query.get(maintenance.asset_id)
        
        # Kiểm tra xem tài sản có đang được bàn giao không
        active_assignment = AssetAssignment.query.filter_by(
            asset_id=maintenance.asset_id, 
            is_returned=False
        ).first()
        
        if active_assignment:
            asset.status = AssetStatus.ASSIGNED
        else:
            asset.status = AssetStatus.AVAILABLE
    
    db.session.commit()
    
    flash('Bảo trì đã được hoàn thành!', 'success')
    return redirect(url_for('asset.view', id=maintenance.asset_id))


@asset_bp.route('/assignments')
@login_required
def assignment_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = AssetAssignment.query
    
    # Lọc theo nhân viên
    employee_id = request.args.get('employee_id', type=int)
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    # Lọc theo trạng thái (đã trả hay chưa)
    returned = request.args.get('returned')
    if returned is not None:
        is_returned = returned == 'true'
        query = query.filter_by(is_returned=is_returned)
    
    pagination = query.order_by(AssetAssignment.assigned_date.desc()).paginate(page=page, per_page=per_page)
    assignments = pagination.items
    
    employees = Employee.query.all()
    
    return render_template('assets/assignments.html', 
                          assignments=assignments, 
                          pagination=pagination,
                          employees=employees,
                          title='Danh sách bàn giao tài sản')


@asset_bp.route('/maintenance-list')
@login_required
def maintenance_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = AssetMaintenance.query
    
    # Lọc theo tài sản
    asset_id = request.args.get('asset_id', type=int)
    if asset_id:
        query = query.filter_by(asset_id=asset_id)
    
    # Lọc theo loại bảo trì
    maintenance_type = request.args.get('maintenance_type')
    if maintenance_type:
        query = query.filter_by(maintenance_type=maintenance_type)
    
    # Lọc theo trạng thái
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(AssetMaintenance.maintenance_date.desc()).paginate(page=page, per_page=per_page)
    maintenance_records = pagination.items
    
    assets = Asset.query.all()
    
    return render_template('assets/maintenance_list.html', 
                          maintenance_records=maintenance_records, 
                          pagination=pagination,
                          assets=assets,
                          maintenance_types=MaintenanceType,
                          maintenance_statuses=MaintenanceStatus,
                          title='Danh sách bảo trì tài sản')


# Route cho API lấy danh sách tài sản theo loại và trạng thái
@asset_bp.route('/api/assets')
@login_required
def get_assets():
    category = request.args.get('category')
    status = request.args.get('status')
    
    query = Asset.query
    
    if category:
        query = query.filter_by(category=category)
    
    if status:
        query = query.filter_by(status=status)
    
    assets = query.all()
    
    return jsonify([{
        'id': asset.id,
        'asset_code': asset.asset_code,
        'name': asset.name,
        'category': asset.category.value,
        'status': asset.status.value,
        'serial_number': asset.serial_number
    } for asset in assets])