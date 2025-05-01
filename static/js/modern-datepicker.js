/**
 * Modern Datepicker Integration
 * Tích hợp Litepicker để thay thế datepicker hiện tại
 */

document.addEventListener('DOMContentLoaded', function() {
    // Thay thế flatpickr với Litepicker
    integrateModernDatepicker();

    // Hàm khởi tạo Litepicker
    function integrateModernDatepicker() {
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
                reset: 'Đặt lại',
                apply: 'Áp dụng'
            },
            tooltip: {
                day: 'ngày',
                days: 'ngày',
                one_week: 'tuần',
                weeks: 'tuần',
                one_month: 'tháng',
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

        // Tùy chỉnh các tháng và ngày trong tuần
        const monthNames = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6', 'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'];
        const weekdayNames = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];

        // Tìm tất cả các input có class "datepicker"
        const datepickerElements = document.querySelectorAll('.datepicker, input[type="date"]');

        // Áp dụng Litepicker cho mỗi phần tử
        datepickerElements.forEach(function(element) {
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
                lockDaysFormat: 'YYYY-MM-DD',
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

            // Thiết lập tên tháng và ngày trong tuần
            picker.setTooltip(vietnameseLocale.tooltip);
            
            // Đảm bảo datepicker mới có style hiện đại
            element.addEventListener('focus', function() {
                // Thêm class cho Litepicker container để style
                setTimeout(function() {
                    const containers = document.querySelectorAll('.litepicker');
                    containers.forEach(container => {
                        container.classList.add('modern-litepicker');
                    });
                }, 100);
            });
        });

        console.log('Modern datepicker initialized for', datepickerElements.length, 'elements');
    }
});