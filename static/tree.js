// static/tree.js

function toggleDirectory(element) {
    const content = element.nextElementSibling;
    if (content && content.classList.contains('directory-content')) {
        content.classList.toggle('active');
        const icon = element.querySelector('.directory-icon');
        if (icon) {
            icon.textContent = content.classList.contains('active') ? '▾' : '▸';
        }
    }
}

function expandAll() {
    document.querySelectorAll('.directory-content').forEach(content => {
        content.classList.add('active');
        const icon = content.previousElementSibling.querySelector('.directory-icon');
        if (icon && icon.textContent === '▸') {
            icon.textContent = '▾';
        }
    });
}

function collapseAll() {
    document.querySelectorAll('.directory-content').forEach(content => {
        content.classList.remove('active');
        const icon = content.previousElementSibling.querySelector('.directory-icon');
        if (icon && icon.textContent === '▾') {
            icon.textContent = '▸';
        }
    });
}