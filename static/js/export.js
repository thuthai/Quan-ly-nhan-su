// export.js - JavaScript for export functionality

document.addEventListener('DOMContentLoaded', function() {
  // Set up export buttons
  setupExportButtons();
});

// Set up export buttons functionality
function setupExportButtons() {
  const exportButtons = document.querySelectorAll('.btn-export');
  
  exportButtons.forEach(function(button) {
    button.addEventListener('click', function(e) {
      const target = this.getAttribute('data-export-target');
      if (target === 'employees') {
        exportEmployees();
      } else if (target === 'attendance') {
        exportAttendance();
      }
    });
  });
}

// Export employees data
function exportEmployees() {
  // Show loading state
  const exportBtn = document.querySelector('[data-export-target="employees"]');
  if (exportBtn) {
    const originalText = exportBtn.innerHTML;
    exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Đang xuất...';
    exportBtn.disabled = true;
    
    // Submit the export form
    const form = document.getElementById('export-employees-form');
    if (form) {
      form.submit();
      
      // Restore button state after a delay
      setTimeout(function() {
        exportBtn.innerHTML = originalText;
        exportBtn.disabled = false;
      }, 3000);
    }
  }
}

// Export attendance data
function exportAttendance() {
  // Show loading state
  const exportBtn = document.querySelector('[data-export-target="attendance"]');
  if (exportBtn) {
    const originalText = exportBtn.innerHTML;
    exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Đang xuất...';
    exportBtn.disabled = true;
    
    // Submit the export form
    const form = document.getElementById('export-attendance-form');
    if (form) {
      form.submit();
      
      // Restore button state after a delay
      setTimeout(function() {
        exportBtn.innerHTML = originalText;
        exportBtn.disabled = false;
      }, 3000);
    }
  }
}
