// leave.js - JavaScript for leave request functionality

document.addEventListener('DOMContentLoaded', function() {
  // Initialize leave request form
  const leaveForm = document.getElementById('leave-request-form');
  if (leaveForm) {
    setupLeaveRequestForm(leaveForm);
  }
  
  // Set up leave request actions
  setupLeaveRequestActions();
});

// Set up leave request form validation
function setupLeaveRequestForm(form) {
  const startDateInput = form.querySelector('#start_date');
  const endDateInput = form.querySelector('#end_date');
  
  if (startDateInput && endDateInput) {
    // Validate date range on form submission
    form.addEventListener('submit', function(e) {
      const startDate = new Date(startDateInput.value);
      const endDate = new Date(endDateInput.value);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      // Start date must be in the future
      if (startDate < today) {
        e.preventDefault();
        alert('Ngày bắt đầu không thể trong quá khứ!');
        return false;
      }
      
      // End date must be after start date
      if (startDate > endDate) {
        e.preventDefault();
        alert('Ngày kết thúc phải sau ngày bắt đầu!');
        return false;
      }
      
      return true;
    });
    
    // Update end date min value when start date changes
    startDateInput.addEventListener('change', function() {
      endDateInput.min = this.value;
      
      // If end date is before start date, update it
      if (endDateInput.value && endDateInput.value < this.value) {
        endDateInput.value = this.value;
      }
    });
    
    // Set initial min value for end date
    if (startDateInput.value) {
      endDateInput.min = startDateInput.value;
    }
  }
}

// Set up leave request action buttons
function setupLeaveRequestActions() {
  // Handle approve button
  const approveButtons = document.querySelectorAll('.btn-approve-leave');
  approveButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      if (confirm('Bạn có chắc chắn muốn phê duyệt yêu cầu nghỉ phép này?')) {
        const form = this.closest('form');
        if (form) form.submit();
      }
    });
  });
  
  // Handle reject button
  const rejectButtons = document.querySelectorAll('.btn-reject-leave');
  rejectButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      if (confirm('Bạn có chắc chắn muốn từ chối yêu cầu nghỉ phép này?')) {
        const form = this.closest('form');
        if (form) form.submit();
      }
    });
  });
  
  // Handle cancel button
  const cancelButtons = document.querySelectorAll('.btn-cancel-leave');
  cancelButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      if (confirm('Bạn có chắc chắn muốn hủy yêu cầu nghỉ phép này?')) {
        const form = this.closest('form');
        if (form) form.submit();
      }
    });
  });
}
