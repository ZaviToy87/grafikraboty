
// ===== Resizable columns for revision table =====
document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('revisions-table');
    if (!table) return;
    const thead = table.querySelector('thead tr');
    if (!thead) return;

    thead.querySelectorAll('th').forEach(th => {
        // Skip checkbox column (first)
        if (th.classList && th.classList.contains('rev-col-check')) return;

        const handle = document.createElement('div');
        handle.className = 'resize-handle';
        th.appendChild(handle);

        let startX = 0, startWidth = 0;

        handle.addEventListener('mousedown', function(e) {
            e.preventDefault();
            e.stopPropagation();
            startX = e.clientX;
            startWidth = th.getBoundingClientRect().width;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });

        function onMouseMove(e) {
            const diff = e.clientX - startX;
            const newWidth = Math.max(40, startWidth + diff);
            th.style.width = newWidth + 'px';
            const colIndex = Array.from(thead.children).indexOf(th);
            table.querySelectorAll('tr').forEach(tr => {
                const cell = tr.children[colIndex];
                if (cell) {
                    cell.style.width = newWidth + 'px';
                    cell.style.minWidth = '40px';
                }
            });
        }

        function onMouseUp() {
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }
    });
});
