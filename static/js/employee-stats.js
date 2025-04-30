// employee-stats.js - Tạo các biểu đồ thống kê nhân viên

document.addEventListener('DOMContentLoaded', function() {
    // Lấy dữ liệu thống kê từ template
    const genderStatsElement = document.getElementById('gender-stats-data');
    const ageGroupsElement = document.getElementById('age-groups-data');
    const educationStatsElement = document.getElementById('education-stats-data');
    
    if (genderStatsElement && ageGroupsElement && educationStatsElement) {
        const genderStats = JSON.parse(genderStatsElement.textContent);
        const ageGroups = JSON.parse(ageGroupsElement.textContent);
        const educationStats = JSON.parse(educationStatsElement.textContent);
        
        // Tạo các biểu đồ
        createGenderChart(genderStats);
        createAgeChart(ageGroups);
        createEducationChart(educationStats);
    }
});

// Biểu đồ phân bố giới tính
function createGenderChart(genderStats) {
    const ctx = document.getElementById('genderChart');
    if (!ctx) return;
    
    // Chuẩn bị dữ liệu
    const labels = Object.keys(genderStats);
    const data = Object.values(genderStats);
    
    // Tạo màu sắc
    const colors = ['#4e73df', '#e74a3b', '#36b9cc'];
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                hoverBackgroundColor: colors.map(color => adjustBrightness(color, -20)),
                hoverBorderColor: "rgba(234, 236, 244, 1)",
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${value} người (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Biểu đồ phân bố độ tuổi
function createAgeChart(ageGroups) {
    const ctx = document.getElementById('ageChart');
    if (!ctx) return;
    
    // Chuẩn bị dữ liệu
    const labels = Object.keys(ageGroups);
    const data = Object.values(ageGroups);
    
    // Tạo màu sắc
    const colors = ['#36b9cc', '#1cc88a', '#f6c23e', '#fd7e14'];
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Số lượng',
                data: data,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y} người`;
                        }
                    }
                }
            }
        }
    });
}

// Biểu đồ trình độ học vấn
function createEducationChart(educationStats) {
    const ctx = document.getElementById('educationChart');
    if (!ctx) return;
    
    // Chuẩn bị dữ liệu
    const labels = Object.keys(educationStats);
    const data = Object.values(educationStats);
    
    // Tạo màu sắc ngẫu nhiên cho các trình độ học vấn
    const colors = generateColors(labels.length);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                hoverBackgroundColor: colors.map(color => adjustBrightness(color, -20)),
                hoverBorderColor: "rgba(234, 236, 244, 1)",
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 10,
                        font: {
                            size: 10
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${value} người (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Hàm điều chỉnh độ sáng của màu
function adjustBrightness(color, amount) {
    return color;
}

// Tạo mảng màu từ danh sách các màu cơ bản
function generateColors(count) {
    const baseColors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', 
        '#6f42c1', '#5a5c69', '#fd7e14', '#20c9a6', '#858796'
    ];
    
    if (count <= baseColors.length) {
        return baseColors.slice(0, count);
    }
    
    const result = [...baseColors];
    for (let i = baseColors.length; i < count; i++) {
        result.push(baseColors[i % baseColors.length]);
    }
    
    return result;
}