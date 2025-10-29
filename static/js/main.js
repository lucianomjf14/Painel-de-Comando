// Main JavaScript for Painel de Comando

// Global variables
let currentPage = 'home';
let refreshIntervals = {};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkApiStatus();
});

// Initialize the application
function initializeApp() {
    console.log('Painel de Comando inicializado');
    
    // Add loading states to buttons
    addLoadingStates();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Setup auto-refresh for certain pages
    setupAutoRefresh();
}

// Setup event listeners
function setupEventListeners() {
    // Navbar navigation
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href.startsWith('#')) {
                e.preventDefault();
                handleNavigation(href.substring(1));
            }
        });
    });
    
    // Search functionality
    document.querySelectorAll('input[type="text"]').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const searchButton = this.parentNode.querySelector('button');
                if (searchButton) {
                    searchButton.click();
                }
            }
        });
    });
    
    // File upload
    const fileUpload = document.getElementById('file-upload');
    if (fileUpload) {
        fileUpload.addEventListener('change', function() {
            if (this.files.length > 0) {
                uploadFile();
            }
        });
    }
}

// Check API status
function checkApiStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateStatusIndicator(data);
        })
        .catch(error => {
            console.error('Error checking API status:', error);
            updateStatusIndicator({ status: 'error', authenticated: false });
        });
}

// Update status indicator
function updateStatusIndicator(data) {
    const statusIndicator = document.getElementById('status-indicator');
    if (!statusIndicator) return;
    
    if (data.status === 'success' && data.authenticated) {
        statusIndicator.textContent = 'Conectado';
        statusIndicator.className = 'navbar-text text-success';
    } else {
        statusIndicator.textContent = 'Erro de conexão';
        statusIndicator.className = 'navbar-text text-danger';
    }
}

// Handle navigation
function handleNavigation(page) {
    currentPage = page;
    console.log('Navigating to:', page);
}

// Add loading states to buttons
function addLoadingStates() {
    document.querySelectorAll('button[onclick]').forEach(button => {
        const originalOnclick = button.getAttribute('onclick');
        button.addEventListener('click', function() {
            if (!this.classList.contains('loading')) {
                this.classList.add('loading');
                this.disabled = true;
                
                // Re-enable after 2 seconds or when operation completes
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.disabled = false;
                }, 2000);
            }
        });
    });
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Setup auto-refresh
function setupAutoRefresh() {
    // Auto-refresh every 30 seconds for certain pages
    const pagesWithAutoRefresh = ['gmail', 'sheets', 'drive'];
    
    pagesWithAutoRefresh.forEach(page => {
        if (window.location.pathname.includes(page)) {
            refreshIntervals[page] = setInterval(() => {
                if (typeof window.refreshData === 'function') {
                    window.refreshData();
                }
            }, 30000);
        }
    });
}

// Show alert/notification
function showAlert(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    const icon = getAlertIcon(type);
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            ${icon}
            <span class="ms-2">${message}</span>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Get alert icon based on type
function getAlertIcon(type) {
    const icons = {
        'success': '<i class="fas fa-check-circle text-success"></i>',
        'danger': '<i class="fas fa-exclamation-circle text-danger"></i>',
        'warning': '<i class="fas fa-exclamation-triangle text-warning"></i>',
        'info': '<i class="fas fa-info-circle text-info"></i>'
    };
    return icons[type] || icons['info'];
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format file size
function formatFileSize(bytes) {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

// Truncate text
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copiado para a área de transferência!', 'success');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showAlert('Copiado para a área de transferência!', 'success');
    }
}

// Download file
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Validate email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validate URL
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Get file extension
function getFileExtension(filename) {
    return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
}

// Get file type from MIME type
function getFileTypeFromMime(mimeType) {
    const mimeTypes = {
        'application/pdf': 'PDF',
        'application/vnd.google-apps.spreadsheet': 'Planilha',
        'application/vnd.google-apps.document': 'Documento',
        'application/vnd.google-apps.presentation': 'Apresentação',
        'image/jpeg': 'Imagem JPEG',
        'image/png': 'Imagem PNG',
        'image/gif': 'Imagem GIF',
        'video/mp4': 'Vídeo MP4',
        'audio/mp3': 'Áudio MP3',
        'text/plain': 'Texto',
        'application/zip': 'Arquivo ZIP'
    };
    return mimeTypes[mimeType] || 'Arquivo';
}

// Get file icon from MIME type
function getFileIconFromMime(mimeType) {
    if (mimeType.includes('folder')) {
        return '<i class="fas fa-folder text-warning"></i>';
    } else if (mimeType.includes('spreadsheet')) {
        return '<i class="fas fa-table text-success"></i>';
    } else if (mimeType.includes('document')) {
        return '<i class="fas fa-file-alt text-primary"></i>';
    } else if (mimeType.includes('presentation')) {
        return '<i class="fas fa-presentation text-danger"></i>';
    } else if (mimeType.includes('pdf')) {
        return '<i class="fas fa-file-pdf text-danger"></i>';
    } else if (mimeType.includes('image')) {
        return '<i class="fas fa-image text-info"></i>';
    } else if (mimeType.includes('video')) {
        return '<i class="fas fa-video text-purple"></i>';
    } else if (mimeType.includes('audio')) {
        return '<i class="fas fa-music text-success"></i>';
    } else {
        return '<i class="fas fa-file text-secondary"></i>';
    }
}

// Show loading spinner
function showLoading(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (element) {
        element.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>';
    }
}

// Hide loading spinner
function hideLoading(element, content = '') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (element) {
        element.innerHTML = content;
    }
}

// Confirm dialog
function confirmDialog(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Show modal
function showModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

// Hide modal
function hideModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}

// Export functions to global scope
window.showAlert = showAlert;
window.formatDate = formatDate;
window.formatFileSize = formatFileSize;
window.truncateText = truncateText;
window.copyToClipboard = copyToClipboard;
window.downloadFile = downloadFile;
window.isValidEmail = isValidEmail;
window.isValidUrl = isValidUrl;
window.getFileExtension = getFileExtension;
window.getFileTypeFromMime = getFileTypeFromMime;
window.getFileIconFromMime = getFileIconFromMime;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.confirmDialog = confirmDialog;
window.showModal = showModal;
window.hideModal = hideModal;
