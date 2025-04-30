// datatables-config.js - Configuration for DataTables

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all DataTables on the page
  const dataTableElements = document.querySelectorAll('.datatable');
  
  if (dataTableElements.length > 0) {
    dataTableElements.forEach(function(table) {
      const options = {
        language: {
          url: '//cdn.datatables.net/plug-ins/1.13.1/i18n/vi.json'
        },
        pagingType: 'full_numbers',
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, 'Tất cả']],
        responsive: true,
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
             '<"row"<"col-sm-12"tr>>' +
             '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
        order: table.hasAttribute('data-order-column') 
               ? [[parseInt(table.getAttribute('data-order-column')), table.getAttribute('data-order-dir') || 'asc']] 
               : [[0, 'asc']]
      };
      
      // Check for specific options from data attributes
      if (table.hasAttribute('data-paging')) {
        options.paging = table.getAttribute('data-paging') === 'true';
      }
      
      if (table.hasAttribute('data-searching')) {
        options.searching = table.getAttribute('data-searching') === 'true';
      }
      
      if (table.hasAttribute('data-info')) {
        options.info = table.getAttribute('data-info') === 'true';
      }
      
      if (table.hasAttribute('data-ordering')) {
        options.ordering = table.getAttribute('data-ordering') === 'true';
      }
      
      // Initialize DataTable with options
      const dataTable = new DataTable(table, options);
      
      // Add custom search functionality if required
      if (table.hasAttribute('data-custom-search')) {
        const searchInputId = table.getAttribute('data-custom-search');
        const searchInput = document.getElementById(searchInputId);
        
        if (searchInput) {
          searchInput.addEventListener('keyup', function() {
            dataTable.search(this.value).draw();
          });
        }
      }
    });
  }
});
