// dashboard.js - JavaScript for dashboard charts and statistics

document.addEventListener('DOMContentLoaded', function() {
  // Fix chart container height problems
  fixChartContainers();
  
  // Initialize department chart if element exists
  const deptChartElement = document.getElementById('departmentChart');
  if (deptChartElement) {
    renderDepartmentChart(deptChartElement);
  }
  
  // Initialize gender chart if element exists
  const genderChartElement = document.getElementById('genderChart');
  if (genderChartElement) {
    renderGenderChart(genderChartElement);
  }
  
  // Initialize attendance chart if element exists
  const attendanceChartElement = document.getElementById('attendanceChart');
  if (attendanceChartElement) {
    renderAttendanceChart(attendanceChartElement);
  }
});

// Fix all chart containers to have consistent height
function fixChartContainers() {
  // Set fixed height for all chart elements to prevent extreme stretching
  const charts = document.querySelectorAll('canvas');
  charts.forEach(chart => {
    // Giữ reference đến canvas cũ
    const oldCanvas = chart;
    
    // Lấy thông tin context từ canvas cũ
    const oldContext = chart.getContext('2d');
    const oldId = chart.id;
    const oldParent = chart.parentElement;
    
    // Tạo canvas mới với id và các thuộc tính của canvas cũ
    const newCanvas = document.createElement('canvas');
    newCanvas.id = oldId;
    newCanvas.height = 280;
    newCanvas.width = oldCanvas.width;
    newCanvas.style.height = '280px';
    newCanvas.style.maxHeight = '280px';
    newCanvas.style.width = 'auto';
    
    // Thay thế canvas cũ bằng canvas mới
    if (oldParent) {
      // Tạo một div container nếu chưa có
      oldParent.style.height = '280px';
      oldParent.style.maxHeight = '280px';
      oldParent.style.overflow = 'hidden';
      
      // Thay thế canvas
      oldParent.replaceChild(newCanvas, oldCanvas);
    }
    
    // Sao chép dữ liệu từ data attributes
    const dataAttributes = oldCanvas.dataset;
    for (const key in dataAttributes) {
      newCanvas.dataset[key] = dataAttributes[key];
    }
  });
}

// Render department distribution chart
function renderDepartmentChart(chartElement) {
  // Get department data from the data attribute
  const deptStatsStr = chartElement.getAttribute('data-departments');
  if (!deptStatsStr) return;
  
  const deptStats = JSON.parse(deptStatsStr);
  
  // Extract labels and data
  const labels = deptStats.map(dept => dept.name);
  const data = deptStats.map(dept => dept.count);
  
  // Create chart
  new Chart(chartElement, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Số nhân viên',
        data: data,
        backgroundColor: [
          'rgba(75, 192, 192, 0.7)',
          'rgba(54, 162, 235, 0.7)',
          'rgba(153, 102, 255, 0.7)',
          'rgba(255, 159, 64, 0.7)',
          'rgba(255, 99, 132, 0.7)',
          'rgba(201, 203, 207, 0.7)'
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(201, 203, 207, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          stepSize: 1
        }
      },
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: 'Phân bố nhân viên theo phòng ban',
          color: '#000000',
          font: {
            size: 16,
            weight: 'bold'
          }
        }
      }
    }
  });
}

// Render gender distribution chart
function renderGenderChart(chartElement) {
  // Get gender data from the data attribute
  const genderStatsStr = chartElement.getAttribute('data-gender');
  if (!genderStatsStr) return;
  
  const genderStats = JSON.parse(genderStatsStr);
  
  // Create chart
  new Chart(chartElement, {
    type: 'doughnut',
    data: {
      labels: ['Nam', 'Nữ', 'Khác'],
      datasets: [{
        label: 'Số nhân viên',
        data: [genderStats.male, genderStats.female, genderStats.other],
        backgroundColor: [
          'rgba(54, 162, 235, 0.7)',
          'rgba(255, 99, 132, 0.7)',
          'rgba(255, 159, 64, 0.7)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(255, 159, 64, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#000000',
            font: {
              weight: 'bold'
            }
          }
        },
        title: {
          display: true,
          text: 'Phân bố giới tính',
          color: '#000000',
          font: {
            size: 16,
            weight: 'bold'
          }
        }
      }
    }
  });
}

// Render attendance chart
function renderAttendanceChart(chartElement) {
  // Get attendance data from the data attribute
  const attendanceStatsStr = chartElement.getAttribute('data-attendance');
  if (!attendanceStatsStr) return;
  
  const attendanceStats = JSON.parse(attendanceStatsStr);
  
  // Create chart
  new Chart(chartElement, {
    type: 'line',
    data: {
      labels: attendanceStats.dates,
      datasets: [{
        label: 'Số nhân viên',
        data: attendanceStats.counts,
        fill: false,
        borderColor: 'rgba(75, 192, 192, 1)',
        tension: 0.1,
        pointBackgroundColor: 'rgba(75, 192, 192, 1)',
        pointRadius: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          stepSize: 1
        }
      },
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: 'Biểu đồ chấm công trong 30 ngày gần đây',
          color: '#000000',
          font: {
            size: 16,
            weight: 'bold'
          }
        }
      }
    }
  });
}
