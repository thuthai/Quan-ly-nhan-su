from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from app import db
from models import Contract, ContractType, ContractStatus, ContractAmendment, Document, DocumentType, Employee, Department
from forms_contract import (
    ContractForm, ContractEditForm, ContractTerminationForm,
    ContractAmendmentForm, ContractAmendmentEditForm,
    DocumentForm, DocumentEditForm, ContractFilterForm
)
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import logging
# Import module thông báo
from notifications import send_contract_notification

contract_bp = Blueprint('contract', __name__, url_prefix='/contract')


@contract_bp.route('/')
@login_required
def index():
    form = ContractFilterForm(request.args)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Contract.query
    
    # Áp dụng các bộ lọc
    if form.keyword.data:
        query = query.filter(
            (Contract.contract_number.ilike(f'%{form.keyword.data}%')) |
            (Contract.job_title.ilike(f'%{form.keyword.data}%'))
        )
    
    if form.employee_id.data and form.employee_id.data != 0:
        query = query.filter_by(employee_id=form.employee_id.data)
    
    if form.department_id.data and form.department_id.data != 0:
        query = query.filter_by(department_id=form.department_id.data)
    
    if form.contract_type.data:
        query = query.filter_by(contract_type=form.contract_type.data)
    
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    
    if form.start_date_from.data:
        query = query.filter(Contract.start_date >= form.start_date_from.data)
    
    if form.start_date_to.data:
        query = query.filter(Contract.start_date <= form.start_date_to.data)
    
    if form.end_date_from.data:
        query = query.filter(Contract.end_date >= form.end_date_from.data)
    
    if form.end_date_to.data:
        query = query.filter(Contract.end_date <= form.end_date_to.data)
    
    pagination = query.order_by(Contract.start_date.desc()).paginate(page=page, per_page=per_page)
    contracts = pagination.items
    
    return render_template('contracts/index.html',
                          contracts=contracts,
                          pagination=pagination,
                          form=form,
                          title='Quản lý hợp đồng')


@contract_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ContractForm()
    
    # Chỉ điền thông tin nhân viên nếu được cung cấp rõ ràng qua tham số URL
    employee_id = request.args.get('employee_id', type=int)
    from_employee_profile = request.args.get('from_profile', type=int)
    
    # Chỉ điền sẵn thông tin nếu tham số from_profile được cung cấp
    if employee_id and from_employee_profile and request.method == 'GET':
        form.employee_id.data = employee_id
        employee = Employee.query.get(employee_id)
        if employee:
            form.department_id.data = employee.department_id
            form.job_title.data = employee.position if employee.position else ""
    
    if form.validate_on_submit():
        if not form.validate_dates():
            return render_template('contracts/create.html',
                                  form=form,
                                  title='Thêm hợp đồng mới')
        
        contract = Contract(
            contract_number=form.contract_number.data,
            employee_id=form.employee_id.data,
            contract_type=form.contract_type.data,
            status=form.status.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            job_title=form.job_title.data,
            department_id=form.department_id.data,
            base_salary=form.base_salary.data,
            working_hours=form.working_hours.data,
            signed_date=form.signed_date.data,
            notes=form.notes.data,
            created_by_id=current_user.id
        )
        
        # Xử lý upload file hợp đồng nếu có
        if form.contract_file.data:
            filename = secure_filename(form.contract_file.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"contract_{form.contract_number.data.replace('/', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/contracts')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            file_path = os.path.join(uploads_dir, new_filename)
            form.contract_file.data.save(file_path)
            contract.contract_file = f"uploads/contracts/{new_filename}"
        
        db.session.add(contract)
        db.session.commit()
        
        # Cập nhật thông tin hợp đồng cho nhân viên nếu cần
        employee = Employee.query.get(form.employee_id.data)
        if employee:
            employee.contract_start_date = form.start_date.data
            employee.contract_end_date = form.end_date.data
            db.session.commit()
        
        # Gửi thông báo về hợp đồng mới
        try:
            send_contract_notification(contract.id, 'new')
            logging.info(f"Đã gửi thông báo cho hợp đồng mới {contract.contract_number}")
        except Exception as e:
            logging.error(f"Lỗi khi gửi thông báo: {e}")
        
        flash('Hợp đồng mới đã được tạo thành công!', 'success')
        return redirect(url_for('contract.view', id=contract.id))
    
    return render_template('contracts/create.html',
                          form=form,
                          title='Thêm hợp đồng mới')


@contract_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    contract = Contract.query.get_or_404(id)
    form = ContractEditForm(obj=contract)
    form.contract_id.data = contract.id
    
    if form.validate_on_submit():
        if not form.validate_dates():
            return render_template('contracts/edit.html',
                                  form=form,
                                  contract=contract,
                                  title='Chỉnh sửa hợp đồng')
        
        contract.contract_number = form.contract_number.data
        contract.employee_id = form.employee_id.data
        contract.contract_type = form.contract_type.data
        contract.status = form.status.data
        contract.start_date = form.start_date.data
        contract.end_date = form.end_date.data
        contract.job_title = form.job_title.data
        contract.department_id = form.department_id.data
        contract.base_salary = form.base_salary.data
        contract.working_hours = form.working_hours.data
        contract.signed_date = form.signed_date.data
        contract.notes = form.notes.data
        
        # Xử lý upload file hợp đồng mới nếu có
        if form.contract_file.data:
            # Xóa file cũ nếu có
            if contract.contract_file:
                old_file_path = os.path.join(current_app.root_path, 'static', contract.contract_file)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            filename = secure_filename(form.contract_file.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"contract_{form.contract_number.data.replace('/', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/contracts')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            file_path = os.path.join(uploads_dir, new_filename)
            form.contract_file.data.save(file_path)
            contract.contract_file = f"uploads/contracts/{new_filename}"
        
        db.session.commit()
        
        # Cập nhật thông tin hợp đồng cho nhân viên nếu cần
        employee = Employee.query.get(form.employee_id.data)
        if employee:
            employee.contract_start_date = form.start_date.data
            employee.contract_end_date = form.end_date.data
            db.session.commit()
        
        # Gửi thông báo về cập nhật hợp đồng
        try:
            send_contract_notification(contract.id, 'updated')
            logging.info(f"Đã gửi thông báo cập nhật hợp đồng {contract.contract_number}")
        except Exception as e:
            logging.error(f"Lỗi khi gửi thông báo: {e}")
        
        flash('Hợp đồng đã được cập nhật thành công!', 'success')
        return redirect(url_for('contract.view', id=contract.id))
    
    return render_template('contracts/edit.html',
                          form=form,
                          contract=contract,
                          title='Chỉnh sửa hợp đồng')


@contract_bp.route('/<int:id>/delete_file', methods=['POST'])
@login_required
def delete_contract_file(id):
    """Xóa file đính kèm của hợp đồng"""
    contract = Contract.query.get_or_404(id)
    
    # Kiểm tra nếu có file
    if not contract.contract_file:
        flash('Không có file đính kèm để xóa!', 'warning')
        return redirect(url_for('contract.edit', id=id))
    
    # Xóa file khỏi hệ thống
    file_path = os.path.join(current_app.root_path, 'static', contract.contract_file)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Cập nhật thông tin hợp đồng
    contract.contract_file = None
    db.session.commit()
    
    flash('Đã xóa file đính kèm hợp đồng thành công!', 'success')
    return redirect(url_for('contract.edit', id=id))


@contract_bp.route('/<int:id>')
@login_required
def view(id):
    contract = Contract.query.get_or_404(id)
    amendments = ContractAmendment.query.filter_by(contract_id=id).order_by(ContractAmendment.amendment_date.desc()).all()
    documents = Document.query.filter_by(employee_id=contract.employee_id).all()
    
    from utils import today_date
    
    return render_template('contracts/view.html',
                          contract=contract,
                          amendments=amendments,
                          documents=documents,
                          now=today_date(),
                          title=f'Chi tiết hợp đồng: {contract.contract_number}')


@contract_bp.route('/<int:id>/terminate', methods=['GET', 'POST'])
@login_required
def terminate(id):
    contract = Contract.query.get_or_404(id)
    
    if contract.status == ContractStatus.TERMINATED.name:
        flash('Hợp đồng này đã được chấm dứt trước đó!', 'warning')
        return redirect(url_for('contract.view', id=id))
    
    form = ContractTerminationForm()
    form.contract_id.data = contract.id
    
    if form.validate_on_submit():
        contract.status = ContractStatus.TERMINATED.name
        contract.terminated_date = form.terminated_date.data
        contract.termination_reason = form.termination_reason.data
        
        # Cập nhật thông tin nhân viên
        employee = contract.employee
        if employee:
            employee.status = 'LEAVE'  # Chuyển trạng thái nhân viên sang nghỉ việc
            employee.contract_end_date = form.terminated_date.data
        
        db.session.commit()
        
        # Gửi thông báo về việc chấm dứt hợp đồng
        try:
            send_contract_notification(contract.id, 'terminated')
            logging.info(f"Đã gửi thông báo chấm dứt hợp đồng {contract.contract_number}")
        except Exception as e:
            logging.error(f"Lỗi khi gửi thông báo: {e}")
        
        flash('Hợp đồng đã được chấm dứt thành công!', 'success')
        return redirect(url_for('contract.view', id=id))
    
    return render_template('contracts/terminate.html',
                          form=form,
                          contract=contract,
                          title='Chấm dứt hợp đồng')


@contract_bp.route('/amendments')
@login_required
def amendment_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = ContractAmendment.query
    
    # Lọc theo hợp đồng
    contract_id = request.args.get('contract_id', type=int)
    if contract_id:
        query = query.filter_by(contract_id=contract_id)
    
    # Lọc theo nhân viên
    employee_id = request.args.get('employee_id', type=int)
    if employee_id:
        query = query.join(Contract).filter(Contract.employee_id == employee_id)
    
    pagination = query.order_by(ContractAmendment.amendment_date.desc()).paginate(page=page, per_page=per_page)
    amendments = pagination.items
    
    contracts = Contract.query.filter_by(status=ContractStatus.ACTIVE.name).all()
    
    return render_template('contracts/amendments/index.html',
                          amendments=amendments,
                          pagination=pagination,
                          contracts=contracts,
                          title='Danh sách phụ lục hợp đồng')


@contract_bp.route('/amendments/create', methods=['GET', 'POST'])
@login_required
def amendment_create():
    form = ContractAmendmentForm()
    
    # Pre-fill contract_id from URL parameter
    contract_id = request.args.get('contract_id', type=int)
    if contract_id and request.method == 'GET':
        form.contract_id.data = contract_id
    
    if form.validate_on_submit():
        if not form.validate_dates():
            return render_template('contracts/amendments/create.html',
                                  form=form,
                                  title='Thêm phụ lục hợp đồng')
        
        amendment = ContractAmendment(
            contract_id=form.contract_id.data,
            amendment_number=form.amendment_number.data,
            amendment_date=form.amendment_date.data,
            effective_date=form.effective_date.data,
            description=form.description.data,
            changes=form.changes.data,
            created_by_id=current_user.id
        )
        
        # Xử lý upload file phụ lục nếu có
        if form.amendment_file.data:
            filename = secure_filename(form.amendment_file.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"amendment_{form.amendment_number.data.replace('/', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/contracts/amendments')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            file_path = os.path.join(uploads_dir, new_filename)
            form.amendment_file.data.save(file_path)
            amendment.amendment_file = f"uploads/contracts/amendments/{new_filename}"
        
        db.session.add(amendment)
        db.session.commit()
        
        flash('Phụ lục hợp đồng đã được tạo thành công!', 'success')
        return redirect(url_for('contract.amendment_view', id=amendment.id))
    
    return render_template('contracts/amendments/create.html',
                          form=form,
                          title='Thêm phụ lục hợp đồng')


@contract_bp.route('/amendments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def amendment_edit(id):
    amendment = ContractAmendment.query.get_or_404(id)
    form = ContractAmendmentEditForm(obj=amendment)
    form.amendment_id.data = amendment.id
    
    if form.validate_on_submit():
        if not form.validate_dates():
            return render_template('contracts/amendments/edit.html',
                                  form=form,
                                  amendment=amendment,
                                  title='Chỉnh sửa phụ lục hợp đồng')
        
        amendment.contract_id = form.contract_id.data
        amendment.amendment_number = form.amendment_number.data
        amendment.amendment_date = form.amendment_date.data
        amendment.effective_date = form.effective_date.data
        amendment.description = form.description.data
        amendment.changes = form.changes.data
        
        # Xử lý upload file phụ lục mới nếu có
        if form.amendment_file.data:
            # Xóa file cũ nếu có
            if amendment.amendment_file:
                old_file_path = os.path.join(current_app.root_path, 'static', amendment.amendment_file)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            filename = secure_filename(form.amendment_file.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"amendment_{form.amendment_number.data.replace('/', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/contracts/amendments')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            file_path = os.path.join(uploads_dir, new_filename)
            form.amendment_file.data.save(file_path)
            amendment.amendment_file = f"uploads/contracts/amendments/{new_filename}"
        
        db.session.commit()
        
        flash('Phụ lục hợp đồng đã được cập nhật thành công!', 'success')
        return redirect(url_for('contract.amendment_view', id=amendment.id))
    
    return render_template('contracts/amendments/edit.html',
                          form=form,
                          amendment=amendment,
                          title='Chỉnh sửa phụ lục hợp đồng')


@contract_bp.route('/amendments/<int:id>/delete_file', methods=['POST'])
@login_required
def delete_amendment_file(id):
    """Xóa file đính kèm của phụ lục hợp đồng"""
    amendment = ContractAmendment.query.get_or_404(id)
    
    # Kiểm tra nếu có file
    if not amendment.amendment_file:
        flash('Không có file đính kèm để xóa!', 'warning')
        return redirect(url_for('contract.amendment_edit', id=id))
    
    # Xóa file khỏi hệ thống
    file_path = os.path.join(current_app.root_path, 'static', amendment.amendment_file)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Cập nhật thông tin phụ lục
    amendment.amendment_file = None
    db.session.commit()
    
    flash('Đã xóa file đính kèm phụ lục hợp đồng thành công!', 'success')
    return redirect(url_for('contract.amendment_edit', id=id))


@contract_bp.route('/amendments/<int:id>')
@login_required
def amendment_view(id):
    amendment = ContractAmendment.query.get_or_404(id)
    
    return render_template('contracts/amendments/view.html',
                          amendment=amendment,
                          title=f'Chi tiết phụ lục: {amendment.amendment_number}')


@contract_bp.route('/documents')
@login_required
def document_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Document.query
    
    # Lọc theo nhân viên
    employee_id = request.args.get('employee_id', type=int)
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    # Lọc theo loại tài liệu
    document_type = request.args.get('document_type')
    if document_type:
        query = query.filter_by(document_type=document_type)
    
    # Lọc theo trạng thái xác minh
    is_verified = request.args.get('is_verified')
    if is_verified is not None:
        is_verified_bool = is_verified == 'true'
        query = query.filter_by(is_verified=is_verified_bool)
    
    pagination = query.order_by(Document.created_at.desc()).paginate(page=page, per_page=per_page)
    documents = pagination.items
    
    employees = Employee.query.all()
    
    return render_template('contracts/documents/index.html',
                          documents=documents,
                          pagination=pagination,
                          employees=employees,
                          document_types=DocumentType,
                          title='Danh sách tài liệu')


@contract_bp.route('/documents/create', methods=['GET', 'POST'])
@login_required
def document_create():
    form = DocumentForm()
    
    # Pre-fill employee_id from URL parameter
    employee_id = request.args.get('employee_id', type=int)
    if employee_id and request.method == 'GET':
        form.employee_id.data = employee_id
    
    if form.validate_on_submit():
        if not form.validate_dates():
            return render_template('contracts/documents/create.html',
                                 form=form,
                                 title='Thêm tài liệu mới')
        
        document = Document(
            employee_id=form.employee_id.data,
            document_type=form.document_type.data,
            document_number=form.document_number.data,
            issue_date=form.issue_date.data,
            expiry_date=form.expiry_date.data,
            issue_place=form.issue_place.data,
            description=form.description.data,
            is_verified=form.is_verified.data == 'True'
        )
        
        if form.is_verified.data == 'True':
            document.verified_by_id = current_user.id
            document.verified_date = datetime.now()
        
        # Xử lý upload file
        if form.file_upload.data:
            filename = secure_filename(form.file_upload.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"doc_{document.document_type.name}_{document.employee_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/documents')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            file_path = os.path.join(uploads_dir, new_filename)
            form.file_upload.data.save(file_path)
            document.file_path = f"uploads/documents/{new_filename}"
        
        db.session.add(document)
        db.session.commit()
        
        flash('Tài liệu mới đã được tạo thành công!', 'success')
        return redirect(url_for('contract.document_view', id=document.id))
    
    return render_template('contracts/documents/create.html',
                          form=form,
                          title='Thêm tài liệu mới')


@contract_bp.route('/documents/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def document_edit(id):
    document = Document.query.get_or_404(id)
    form = DocumentEditForm(obj=document)
    form.document_id.data = document.id
    
    # Gán giá trị cho trường is_verified
    if request.method == 'GET':
        form.is_verified.data = 'True' if document.is_verified else 'False'
    
    if form.validate_on_submit():
        if not form.validate_dates():
            return render_template('contracts/documents/edit.html',
                                 form=form,
                                 document=document,
                                 title='Chỉnh sửa tài liệu')
        
        document.employee_id = form.employee_id.data
        document.document_type = form.document_type.data
        document.document_number = form.document_number.data
        document.issue_date = form.issue_date.data
        document.expiry_date = form.expiry_date.data
        document.issue_place = form.issue_place.data
        document.description = form.description.data
        
        # Xử lý trạng thái xác minh
        was_verified = document.is_verified
        is_verified_now = form.is_verified.data == 'True'
        
        if not was_verified and is_verified_now:
            # Mới được xác minh
            document.verified_by_id = current_user.id
            document.verified_date = datetime.now()
        elif was_verified and not is_verified_now:
            # Hủy xác minh
            document.verified_by_id = None
            document.verified_date = None
        
        document.is_verified = is_verified_now
        
        # Xử lý upload file mới nếu có
        if form.file_upload.data:
            # Xóa file cũ nếu có
            if document.file_path:
                old_file_path = os.path.join(current_app.root_path, 'static', document.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            filename = secure_filename(form.file_upload.data.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"doc_{document.document_type.name}_{document.employee_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
            
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads/documents')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                
            file_path = os.path.join(uploads_dir, new_filename)
            form.file_upload.data.save(file_path)
            document.file_path = f"uploads/documents/{new_filename}"
        
        db.session.commit()
        
        flash('Tài liệu đã được cập nhật thành công!', 'success')
        return redirect(url_for('contract.document_view', id=document.id))
    
    return render_template('contracts/documents/edit.html',
                          form=form,
                          document=document,
                          title='Chỉnh sửa tài liệu')


@contract_bp.route('/documents/<int:id>')
@login_required
def document_view(id):
    document = Document.query.get_or_404(id)
    
    return render_template('contracts/documents/view.html',
                          document=document,
                          title=f'Chi tiết tài liệu: {document.document_type.value}')


@contract_bp.route('/documents/<int:id>/verify', methods=['POST'])
@login_required
def document_verify(id):
    document = Document.query.get_or_404(id)
    
    if document.is_verified:
        flash('Tài liệu này đã được xác minh trước đó!', 'warning')
    else:
        document.is_verified = True
        document.verified_by_id = current_user.id
        document.verified_date = datetime.now()
        db.session.commit()
        flash('Tài liệu đã được xác minh thành công!', 'success')
    
    return redirect(url_for('contract.document_view', id=id))


@contract_bp.route('/documents/<int:id>/unverify', methods=['POST'])
@login_required
def document_unverify(id):
    document = Document.query.get_or_404(id)
    
    if not document.is_verified:
        flash('Tài liệu này chưa được xác minh!', 'warning')
    else:
        document.is_verified = False
        document.verified_by_id = None
        document.verified_date = None
        db.session.commit()
        flash('Đã hủy xác minh tài liệu!', 'success')
    
    return redirect(url_for('contract.document_view', id=id))


# Tải file tài liệu
@contract_bp.route('/download/<int:id>')
@login_required
def download_contract(id):
    contract = Contract.query.get_or_404(id)
    
    if not contract.contract_file:
        flash('Không có file hợp đồng!', 'warning')
        return redirect(url_for('contract.view', id=id))
    
    file_path = contract.contract_file.split('/')
    filename = file_path[-1]
    directory = os.path.join(current_app.root_path, 'static', os.path.dirname(contract.contract_file))
    
    return send_from_directory(directory, filename, as_attachment=True)


@contract_bp.route('/amendments/download/<int:id>')
@login_required
def download_amendment(id):
    amendment = ContractAmendment.query.get_or_404(id)
    
    if not amendment.amendment_file:
        flash('Không có file phụ lục!', 'warning')
        return redirect(url_for('contract.amendment_view', id=id))
    
    file_path = amendment.amendment_file.split('/')
    filename = file_path[-1]
    directory = os.path.join(current_app.root_path, 'static', os.path.dirname(amendment.amendment_file))
    
    return send_from_directory(directory, filename, as_attachment=True)


@contract_bp.route('/documents/download/<int:id>')
@login_required
def download_document(id):
    document = Document.query.get_or_404(id)
    
    file_path = document.file_path.split('/')
    filename = file_path[-1]
    directory = os.path.join(current_app.root_path, 'static', os.path.dirname(document.file_path))
    
    return send_from_directory(directory, filename, as_attachment=True)


# API endpoints
@contract_bp.route('/api/contracts/<int:employee_id>')
@login_required
def api_employee_contracts(employee_id):
    contracts = Contract.query.filter_by(employee_id=employee_id).order_by(Contract.start_date.desc()).all()
    
    return jsonify([{
        'id': contract.id,
        'contract_number': contract.contract_number,
        'contract_type': contract.contract_type.value,
        'status': contract.status.value,
        'start_date': contract.start_date.strftime('%Y-%m-%d'),
        'end_date': contract.end_date.strftime('%Y-%m-%d') if contract.end_date else None,
        'job_title': contract.job_title
    } for contract in contracts])


@contract_bp.route('/api/documents/<int:employee_id>')
@login_required
def api_employee_documents(employee_id):
    documents = Document.query.filter_by(employee_id=employee_id).all()
    
    return jsonify([{
        'id': document.id,
        'document_type': document.document_type.value,
        'document_number': document.document_number,
        'issue_date': document.issue_date.strftime('%Y-%m-%d') if document.issue_date else None,
        'expiry_date': document.expiry_date.strftime('%Y-%m-%d') if document.expiry_date else None,
        'is_verified': document.is_verified
    } for document in documents])