/**
 * Modern Datepicker Integration với Litepicker
 * Hỗ trợ hiển thị tốt hơn, màu sắc tương phản cao, và giao diện thân thiện
 */

document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo modern datepicker
    initializeModernDatepicker();

    // Hàm khởi tạo Litepicker
    function initializeModernDatepicker() {
        console.log('Initializing modern datepicker...');
        
        // Kiểm tra xem thư viện đã được load chưa
        if (typeof Litepicker === 'undefined') {
            console.error('Litepicker chưa được load. Đang sử dụng datepicker mặc định.');
            return;
        }

        // Thiết lập ngôn ngữ tiếng Việt
        const vietnameseLocale = {
            buttons: {
                previousMonth: 'Tháng trước',
                nextMonth: 'Tháng sau',
                reset: 'Xóa',
                apply: 'Đồng ý',
                cancel: 'Hủy'
            },
            tooltip: {
                day: 'ngày',
                days: 'ngày',
                week: 'tuần',
                weeks: 'tuần',
                month: 'tháng',
                months: 'tháng'
            },
            tooltipText: {
                one_day: '{0} ngày',
                other_day: '{0} ngày',
                one_week: '{0} tuần',
                other_week: '{0} tuần',
                one_month: '{0} tháng',
                other_month: '{0} tháng'
            },
            pluralSelector: function(i) {
                return 'other';
            }
        };

        // Tùy chỉnh tên tháng và ngày trong tuần
        const monthNames = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6', 'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'];
        const weekdayNames = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

        // Tìm tất cả các input ngày
        const datepickerElements = document.querySelectorAll('.datepicker, input[type="date"]');
        console.log('Found', datepickerElements.length, 'datepicker elements');

        // Áp dụng Litepicker cho mỗi phần tử
        datepickerElements.forEach(function(element, index) {
            try {
                // Tạo Litepicker mới
                const picker = new Litepicker({
                    element: element,
                    format: 'DD/MM/YYYY',
                    lang: 'vi-VN',
                    autoApply: true,
                    showTooltip: true,
                    singleMode: true,
                    numberOfMonths: 1,
                    numberOfColumns: 1,
                    dropdowns: {
                        minYear: 1950,
                        maxYear: 2050,
                        months: true,
                        years: true
                    },
                    tooltipText: vietnameseLocale.tooltipText,
                    buttonText: vietnameseLocale.buttons,
                    switchingMonths: 1,
                    resetButton: true,
                    resetBtnCallback: () => {
                        picker.clearSelection();
                    },
                    setup: (picker) => {
                        picker.on('selected', (date) => {
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                        });
                    }
                });
                
                // Cập nhật các tên ngày và tháng 
                picker.options.dropdowns.months = monthNames;
                picker.options.weekdaysList = weekdayNames;
                
                // Fix cho vấn đề UI
                element.addEventListener('focus', function() {
                    requestAnimationFrame(() => {
                        const containers = document.querySelectorAll('.litepicker');
                        containers.forEach(container => {
                            container.style.backgroundColor = '#ffffff';
                            container.style.color = '#333333';
                            container.style.fontWeight = 'bold';
                            
                            // Đảm bảo header hiển thị đúng
                            const headers = container.querySelectorAll('.month-item-header');
                            headers.forEach(header => {
                                header.style.backgroundColor = '#3f51b5';
                                header.style.color = '#ffffff';
                                header.style.padding = '15px';
                                header.style.fontWeight = 'bold';
                                header.style.borderRadius = '12px 12px 0 0';
                            });
                            
                            // Làm cho nút tháng trước/sau rõ ràng hơn
                            const navigationButtons = container.querySelectorAll('.button-previous-month, .button-next-month');
                            navigationButtons.forEach(btn => {
                                btn.style.color = '#ffffff';
                                btn.style.fontSize = '1.5rem';
                                btn.style.padding = '0 10px';
                            });
                            
                            // Định dạng tên tháng và năm
                            const monthYearElements = container.querySelectorAll('.month-item-name, .month-item-year');
                            monthYearElements.forEach(el => {
                                el.style.color = '#ffffff';
                                el.style.fontWeight = 'bold';
                                el.style.fontSize = '1.2rem';
                                el.style.cursor = 'pointer';
                            });
                        });
                    });
                });
                
                console.log('Initialized datepicker for element', index);
            } catch (error) {
                console.error('Error initializing datepicker:', error);
            }
        });
    }
});