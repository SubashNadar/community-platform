// Main JavaScript file for Community Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });

    // Image lazy loading fallback for older browsers
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDark);
            
            // Update icon
            const icon = this.querySelector('i');
            icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        });

        // Load saved dark mode preference
        const savedDarkMode = localStorage.getItem('darkMode') === 'true';
        if (savedDarkMode) {
            document.body.classList.add('dark-mode');
            const icon = darkModeToggle.querySelector('i');
            if (icon) icon.className = 'fas fa-sun';
        }
    }

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    }

    // File upload drag and drop
    const uploadAreas = document.querySelectorAll('.upload-area');
    uploadAreas.forEach(function(uploadArea) {
        const fileInput = uploadArea.querySelector('input[type="file"]');
        
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            
            if (fileInput && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                fileInput.dispatchEvent(new Event('change'));
            }
        });

        uploadArea.addEventListener('click', function() {
            if (fileInput) fileInput.click();
        });
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const text = this.dataset.copy;
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!', 'success');
            }).catch(() => {
                showToast('Failed to copy to clipboard', 'error');
            });
        });
    });

    // Infinite scroll for feeds
    const infiniteScrollContainer = document.querySelector('[data-infinite-scroll]');
    if (infiniteScrollContainer) {
        let loading = false;
        let page = 1;

        window.addEventListener('scroll', function() {
            if (loading) return;

            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
                loading = true;
                loadMoreContent(++page);
            }
        });
    }

    // Real-time character count for textareas
    const textareasWithCount = document.querySelectorAll('textarea[data-max-length]');
    textareasWithCount.forEach(function(textarea) {
        const maxLength = parseInt(textarea.dataset.maxLength);
        const counter = document.createElement('div');
        counter.className = 'text-muted small mt-1';
        textarea.parentNode.appendChild(counter);

        function updateCounter() {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = `${remaining} characters remaining`;
            counter.className = remaining < 0 ? 'text-danger small mt-1' : 'text-muted small mt-1';
        }

        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });
});

// Utility Functions

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

function performSearch(query) {
    if (query.length < 2) return;
    
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
        });
}

function displaySearchResults(results) {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = '';
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted">No results found</p>';
        return;
    }
    
    results.forEach(result => {
        const resultElement = document.createElement('div');
        resultElement.className = 'search-result p-2 border-bottom';
        resultElement.innerHTML = `
            <h6><a href="${result.url}" class="text-decoration-none">${result.title}</a></h6>
            <p class="small text-muted mb-0">${result.excerpt}</p>
        `;
        resultsContainer.appendChild(resultElement);
    });
}

function loadMoreContent(page) {
    const container = document.querySelector('[data-infinite-scroll]');
    const url = container.dataset.infiniteScroll;
    
    fetch(`${url}?page=${page}`)
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                container.insertAdjacentHTML('beforeend', data.html);
            }
            
            if (!data.has_more) {
                window.removeEventListener('scroll', arguments.callee);
            }
        })
        .catch(error => {
            console.error('Load more error:', error);
        })
        .finally(() => {
            loading = false;
        });
}

function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function timeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    
    for (const [unit, seconds] of Object.entries(intervals)) {
        const interval = Math.floor(diffInSeconds / seconds);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }
    
    return 'Just now';
}

// Update relative timestamps
function updateTimestamps() {
    const timestamps = document.querySelectorAll('[data-timestamp]');
    timestamps.forEach(function(element) {
        const timestamp = new Date(element.dataset.timestamp);
        element.textContent = timeAgo(timestamp);
    });
}

// Update timestamps every minute
setInterval(updateTimestamps, 60000);

// Service Worker registration for PWA support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed');
            });
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            if (modal) modal.hide();
        }
    }
});

// Export functions for use in other scripts
window.CommunityPlatform = {
    showToast,
    performSearch,
    confirmDelete,
    formatFileSize,
    timeAgo,
    updateTimestamps
};