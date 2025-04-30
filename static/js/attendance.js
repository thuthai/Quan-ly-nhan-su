// attendance.js - JavaScript for attendance functionality

document.addEventListener('DOMContentLoaded', function() {
  // Initialize check-in/check-out time display
  updateCurrentTime();
  
  // Set up clock update interval
  setInterval(updateCurrentTime, 1000);
  
  // Set up attendance form handler
  setupAttendanceForm();
});

// Update current time display
function updateCurrentTime() {
  const clockElement = document.getElementById('current-time');
  if (!clockElement) return;
  
  const now = new Date();
  const timeString = now.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  
  clockElement.textContent = timeString;
}

// Set up attendance form functionality
function setupAttendanceForm() {
  const checkInBtn = document.getElementById('check-in-btn');
  const checkOutBtn = document.getElementById('check-out-btn');
  
  // Handle check-in button
  if (checkInBtn) {
    checkInBtn.addEventListener('click', function() {
      const form = document.getElementById('check-in-form');
      if (form) {
        // Confirm check-in
        if (confirm('Bạn có chắc chắn muốn check-in?')) {
          form.submit();
        }
      }
    });
  }
  
  // Handle check-out button
  if (checkOutBtn) {
    checkOutBtn.addEventListener('click', function() {
      const form = document.getElementById('check-out-form');
      if (form) {
        // Confirm check-out
        if (confirm('Bạn có chắc chắn muốn check-out?')) {
          form.submit();
        }
      }
    });
  }
  
  // Set up attendance report form
  const reportForm = document.getElementById('attendance-report-form');
  if (reportForm) {
    const employeeSelect = document.getElementById('employee_id');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    // Validate date range
    reportForm.addEventListener('submit', function(e) {
      if (startDateInput && endDateInput) {
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        
        if (startDate > endDate) {
          e.preventDefault();
          alert('Ngày kết thúc phải sau ngày bắt đầu!');
        }
      }
    });
  }
}

// Format time for display (HH:MM:SS)
function formatTime(dateTimeStr) {
  if (!dateTimeStr) return '';
  
  const date = new Date(dateTimeStr);
  return date.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}
