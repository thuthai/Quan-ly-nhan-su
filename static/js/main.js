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
        flatpickr(element, {
          dateFormat: 'Y-m-d',
          locale: 'vn',
          altInput: true,
          altFormat: 'd/m/Y',
          allowInput: true
        });
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
  
  const searchInput = form.querySelector('input[name="search"]');
  const clearButton = form.querySelector('.btn-clear-search');
  
  if (clearButton && resetBtn) {
    clearButton.addEventListener('click', function(e) {
      e.preventDefault();
      searchInput.value = '';
      form.submit();
    });
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
