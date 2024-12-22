document.querySelector("#crawlerForm").addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent default form submission

    const baseUrl = document.querySelector("#base_url").value;
    const depth = document.querySelector("#depth").value;

    // Hide the form and show the loading spinner
    document.querySelector("#loading").style.display = "flex"; // Make the loading spinner visible

    // Send the POST request using Fetch API
    fetch("/crawl", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            base_url: baseUrl,
            depth: depth
        })
    })
    .then(response => response.text())
    .then(html => {
        // Replace the current content with the response HTML
        document.body.innerHTML = html;
    })
    .catch(error => {
        console.error("Error:", error);
        alert("An error occurred while crawling the website.");
        // Show the form again and hide the loading spinner
        document.querySelector("#crawlerForm").style.display = "block";
        document.querySelector("#loading").style.display = "none";
    });
});
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