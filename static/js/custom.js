// Custom JavaScript for Carnaval da Beira

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize voting functionality
    initVotingSystem();
    
    // Initialize category filters
    initCategoryFilters();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize image lazy loading
    initLazyLoading();
    
    // Initialize smooth scrolling
    initSmoothScrolling();
    
    // Auto-dismiss alerts after 5 seconds
    dismissAlertsAutomatically();
});

// Voting System
function initVotingSystem() {
    const votingCards = document.querySelectorAll('.voting-card');
    const voteForm = document.getElementById('vote-form');
    
    if (!votingCards.length || !voteForm) return;
    
    let selectedGroup = null;
    
    votingCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove previous selection
            votingCards.forEach(c => c.classList.remove('selected'));
            
            // Add selection to clicked card
            this.classList.add('selected');
            
            // Store selected group
            selectedGroup = this.dataset.grupoId;
            
            // Update hidden form field
            const hiddenInput = voteForm.querySelector('input[name="grupo_id"]');
            if (hiddenInput) {
                hiddenInput.value = selectedGroup;
            }
            
            // Enable submit button
            const submitBtn = voteForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('btn-secondary');
                submitBtn.classList.add('btn-success');
                submitBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Confirmar Voto';
            }
            
            // Add visual feedback
            this.style.transform = 'scale(1.05)';
            setTimeout(() => {
                this.style.transform = '';
            }, 200);
        });
        
        // Add keyboard navigation
        card.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
        
        // Make cards focusable
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'button');
        card.setAttribute('aria-label', `Votar no grupo ${card.querySelector('.card-title').textContent}`);
    });
    
    // Form submission with loading state
    voteForm.addEventListener('submit', function(e) {
        if (!selectedGroup) {
            e.preventDefault();
            showMessage('Por favor, selecione um grupo para votar.', 'warning');
            return;
        }
        
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>Enviando voto...';
        }
    });
}

// Category Filters
function initCategoryFilters() {
    const filterButtons = document.querySelectorAll('.category-filter .btn');
    const cards = document.querySelectorAll('.filterable-card');
    
    if (!filterButtons.length || !cards.length) return;
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.dataset.category;
            
            // Update button states
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter cards
            cards.forEach(card => {
                const cardCategory = card.dataset.category;
                
                if (category === 'all' || cardCategory === category) {
                    card.style.display = 'block';
                    card.style.opacity = '0';
                    setTimeout(() => {
                        card.style.opacity = '1';
                    }, 100);
                } else {
                    card.style.opacity = '0';
                    setTimeout(() => {
                        card.style.display = 'none';
                    }, 300);
                }
            });
            
            // Update URL without page reload
            const url = new URL(window.location);
            if (category === 'all') {
                url.searchParams.delete('categoria');
            } else {
                url.searchParams.set('categoria', category);
            }
            window.history.pushState({}, '', url);
        });
    });
}

// Form Validation
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
        
        // Real-time validation feedback
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
        });
    });
}

// Lazy Loading for Images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for older browsers
        images.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
}

// Smooth Scrolling
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                
                const offsetTop = targetElement.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Update focus for accessibility
                targetElement.setAttribute('tabindex', '-1');
                targetElement.focus();
            }
        });
    });
}

// Auto-dismiss Alerts
function dismissAlertsAutomatically() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// Utility Functions
function showMessage(message, type = 'info') {
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <strong>
                <i class="bi bi-${getIconForAlertType(type)}"></i>
                ${getAlertTitle(type)}
            </strong>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
        </div>
    `;
    
    const container = document.querySelector('.container:first-of-type') || document.body;
    container.insertAdjacentHTML('afterbegin', alertHTML);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const newAlert = container.querySelector('.alert:first-child');
        if (newAlert) {
            const bsAlert = new bootstrap.Alert(newAlert);
            bsAlert.close();
        }
    }, 5000);
}

function getIconForAlertType(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle',
        'danger': 'exclamation-triangle'
    };
    return icons[type] || 'info-circle';
}

function getAlertTitle(type) {
    const titles = {
        'success': 'Sucesso!',
        'error': 'Erro!',
        'warning': 'Atenção!',
        'info': 'Informação:',
        'danger': 'Erro!'
    };
    return titles[type] || 'Informação:';
}

// Results Page - Auto Refresh
function initResultsAutoRefresh() {
    const resultsContainer = document.querySelector('.results-container');
    
    if (resultsContainer && window.location.pathname.includes('resultados')) {
        setInterval(() => {
            fetch(window.location.href, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newResults = doc.querySelector('.results-container');
                
                if (newResults) {
                    resultsContainer.innerHTML = newResults.innerHTML;
                    
                    // Animate progress bars
                    const progressBars = resultsContainer.querySelectorAll('.progress-bar');
                    progressBars.forEach(bar => {
                        const width = bar.style.width;
                        bar.style.width = '0%';
                        setTimeout(() => {
                            bar.style.width = width;
                        }, 100);
                    });
                }
            })
            .catch(error => console.error('Error refreshing results:', error));
        }, 30000); // Refresh every 30 seconds
    }
}

// Copy to Clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showMessage('Copiado para a área de transferência!', 'success');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showMessage('Copiado para a área de transferência!', 'success');
    }
}

// Share functionality
function shareResults() {
    if (navigator.share) {
        navigator.share({
            title: 'Resultados do Carnaval da Beira',
            text: 'Confira os resultados da votação popular do Carnaval da Beira!',
            url: window.location.href
        });
    } else {
        copyToClipboard(window.location.href);
    }
}

// Initialize results page functionality
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initResultsAutoRefresh);
} else {
    initResultsAutoRefresh();
}

// Service Worker Registration (for offline functionality)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('SW registered: ', registration);
            })
            .catch(function(registrationError) {
                console.log('SW registration failed: ', registrationError);
            });
    });
}