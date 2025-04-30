// main.js - General JavaScript functions for the application

// Enable tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
  // Initialize all tooltips
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Initialize all popovers
  var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
  
  // Auto-hide flash messages after 5 seconds
  setTimeout(function() {
    var flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(function(element) {
      var alert = new bootstrap.Alert(element);
      alert.close();
    });
  }, 5000);
  
  // Initialize date pickers
  const datepickers = document.querySelectorAll('.datepicker');
  if (datepickers.length > 0) {
    datepickers.forEach(function(element) {
      // Ensure we have flatpickr loaded
      if (typeof flatpickr === 'function') {
        // Khởi tạo bảng chọn ngày tháng với cấu hình cải tiến
        flatpickr(element, {
          dateFormat: 'Y-m-d',
          locale: 'vn',
          altInput: true,
          altFormat: 'd/m/Y',
          allowInput: true,
          disableMobile: "true", // Đặt thành string để tránh lỗi trên mobile
          monthSelectorType: 'dropdown',
          animate: true,
          showMonths: 1,
          position: "auto center",
          nextArrow: '<i class="bi bi-arrow-right-circle-fill"></i>',
          prevArrow: '<i class="bi bi-arrow-left-circle-fill"></i>'
        });
        
        // Đảm bảo rằng các input có giá trị ban đầu được hiển thị chính xác
        if (element.value) {
          const date = new Date(element.value);
          if (!isNaN(date.getTime())) {
            // Cập nhật lại giá trị để đảm bảo hiển thị hợp lệ
            element._flatpickr.setDate(date);
          }
        }
      }
    });
  }
  
  // Handle navbar active state
  const currentLocation = location.pathname;
  const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
  
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentLocation || (href !== '/' && currentLocation.startsWith(href))) {
      link.classList.add('active');
    }
  });
});

// Form validation helper
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return true;
  
  // Add bootstrap validation classes
  form.classList.add('was-validated');
  
  return form.checkValidity();
}

// Confirm delete dialog
function confirmDelete(message, formId) {
  if (confirm(message || 'Bạn có chắc chắn muốn xóa không?')) {
    document.getElementById(formId).submit();
  }
  return false;
}

// Format date for display
function formatDate(dateString) {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('vi-VN', { 
    day: '2-digit', 
    month: '2-digit', 
    year: 'numeric' 
  });
}

// Format datetime for display
function formatDateTime(dateTimeString) {
  if (!dateTimeString) return '';
  
  const date = new Date(dateTimeString);
  return date.toLocaleDateString('vi-VN', { 
    day: '2-digit', 
    month: '2-digit', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Function to handle search form
function handleSearch(formId, resetBtn = true) {
  const form = document.getElementById(formId);
  if (!form) return;
  
  // Handle clear search button
  if (resetBtn) {
    const clearBtn = form.querySelector('.btn-clear-search');
    if (clearBtn) {
      clearBtn.addEventListener('click', function(e) {
        e.preventDefault();
        // Clear all input fields except submit buttons
        form.querySelectorAll('input, select').forEach(input => {
          if (input.type !== 'submit' && input.type !== 'button') {
            if (input.type === 'checkbox' || input.type === 'radio') {
              input.checked = false;
            } else {
              input.value = '';
            }
          }
        });
        
        // Submit the form
        form.submit();
      });
    }
  }
  
  // Auto-expand advanced filter if any advanced filter is set
  const advancedFilterContainer = document.getElementById('advancedFilterForm');
  if (advancedFilterContainer) {
    let hasAdvancedFilter = false;
    
    // Check if any advanced filters are set
    ['gender', 'home_town', 'education_level', 'age_min', 'age_max', 'join_date_from', 'join_date_to'].forEach(filterName => {
      const input = form.querySelector(`[name="${filterName}"]`);
      if (input && input.value) {
        hasAdvancedFilter = true;
      }
    });
    
    // If any advanced filter is set, expand the section
    if (hasAdvancedFilter) {
      advancedFilterContainer.classList.add('show');
    }
  }
}

// Function to toggle password visibility
function togglePasswordVisibility(inputId, toggleBtnId) {
  const passwordInput = document.getElementById(inputId);
  const toggleBtn = document.getElementById(toggleBtnId);
  
  if (!passwordInput || !toggleBtn) return;
  
  toggleBtn.addEventListener('click', function() {
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>';
    } else {
      passwordInput.type = 'password';
      toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
    }
  });
}
