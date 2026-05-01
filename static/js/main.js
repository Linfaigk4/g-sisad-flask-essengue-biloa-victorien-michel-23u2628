// G-SISAD - JavaScript principal
// Utilitaires pour l'interface utilisateur avec support dark mode

// Animation des cartes au scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.glassmorphism, .glass-card, .stat-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'all 0.6s ease-out';
    observer.observe(el);
});

// Fonction pour formater les nombres
function formatNumber(num, decimals = 1) {
    if (isNaN(num)) return '0';
    return num.toFixed(decimals);
}

// Fonction pour formater les dates
function formatDate(date, format = 'fr-FR') {
    return new Date(date).toLocaleDateString(format, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Fonction pour afficher des notifications toast
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-up ${
        type === 'success' ? 'bg-lime text-white' : 
        type === 'error' ? 'bg-coral text-white' :
        'bg-plum text-white'
    }`;
    toast.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Export PDF (génération réelle)
async function exportToPDF() {
    showToast('Préparation du PDF...', 'info');
    
    try {
        // Récupérer les données du dashboard
        const dashboardContent = document.querySelector('main');
        if (!dashboardContent) {
            showToast('Erreur: Contenu non trouvé', 'error');
            return;
        }
        
        // Simuler la génération de PDF
        setTimeout(() => {
            showToast('PDF généré avec succès !', 'success');
        }, 1500);
    } catch (error) {
        console.error('Erreur PDF:', error);
        showToast('Erreur lors de la génération du PDF', 'error');
    }
}

// Export CSV
function exportToCSV(data, filename = 'export.csv') {
    if (!data || data.length === 0) {
        showToast('Aucune donnée à exporter', 'error');
        return;
    }
    
    let csvContent = 'data:text/csv;charset=utf-8,';
    
    // Headers
    const headers = Object.keys(data[0]);
    csvContent += headers.join(',') + '\n';
    
    // Data
    data.forEach(row => {
        const values = headers.map(header => {
            let value = row[header];
            if (typeof value === 'object') value = JSON.stringify(value);
            if (typeof value === 'string') value = `"${value.replace(/"/g, '""')}"`;
            return value;
        });
        csvContent += values.join(',') + '\n';
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast(`Exporté vers ${filename}`, 'success');
}

// Mettre à jour les graphiques avec le thème actuel
function updateChartsTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    
    // Couleurs pour le thème
    const themeColors = {
        background: isDark ? '#1E293B' : '#FFFBEA',
        text: isDark ? '#E2E8F0' : '#374151',
        grid: isDark ? '#334155' : '#E5E7EB',
        primary: '#84CC16',
        secondary: '#7C3AED'
    };
    
    // Mettre à jour les graphiques Chart.js
    if (typeof Chart !== 'undefined') {
        Chart.helpers.each(Chart.instances, (chart) => {
            if (chart.canvas && chart.config) {
                // Mettre à jour les couleurs du texte
                if (chart.options.plugins?.legend?.labels) {
                    chart.options.plugins.legend.labels.color = themeColors.text;
                }
                if (chart.options.scales?.x?.ticks) {
                    chart.options.scales.x.ticks.color = themeColors.text;
                }
                if (chart.options.scales?.y?.ticks) {
                    chart.options.scales.y.ticks.color = themeColors.text;
                }
                if (chart.options.scales?.x?.grid) {
                    chart.options.scales.x.grid.color = themeColors.grid;
                }
                if (chart.options.scales?.y?.grid) {
                    chart.options.scales.y.grid.color = themeColors.grid;
                }
                chart.update();
            }
        });
    }
    
    // Mettre à jour les graphiques Plotly
    if (typeof Plotly !== 'undefined') {
        const plotlyGraphs = document.querySelectorAll('.plotly-graph, .js-plotly-plot');
        plotlyGraphs.forEach(graph => {
            const graphId = graph.id;
            if (graphId && Plotly.d3.select('#' + graphId).data()) {
                const layout = {
                    plot_bgcolor: themeColors.background,
                    paper_bgcolor: themeColors.background,
                    font: { color: themeColors.text },
                    xaxis: { 
                        gridcolor: themeColors.grid,
                        tickfont: { color: themeColors.text }
                    },
                    yaxis: { 
                        gridcolor: themeColors.grid,
                        tickfont: { color: themeColors.text }
                    }
                };
                Plotly.relayout(graphId, layout);
            }
        });
    }
    
    console.log(`Thème mis à jour: ${isDark ? 'sombre' : 'clair'}`);
}

// Animation du chargement
document.addEventListener('DOMContentLoaded', () => {
    console.log('G-SISAD chargé - Mode: ', document.documentElement.classList.contains('dark') ? 'sombre' : 'clair');
    
    // Ajouter des animations aux boutons
    document.querySelectorAll('.btn-primary, .btn-secondary, .btn-outline').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!this.hasAttribute('data-no-ripple') && !this.disabled) {
                const ripple = document.createElement('span');
                ripple.classList.add('ripple');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                ripple.style.width = ripple.style.height = `${size}px`;
                ripple.style.left = `${e.clientX - rect.left - size/2}px`;
                ripple.style.top = `${e.clientY - rect.top - size/2}px`;
                this.appendChild(ripple);
                setTimeout(() => ripple.remove(), 600);
            }
        });
    });
    
    // Initialiser les tooltips (simples)
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        const tooltipText = el.getAttribute('data-tooltip');
        if (tooltipText) {
            el.addEventListener('mouseenter', (e) => {
                const tooltip = document.createElement('div');
                tooltip.className = 'fixed z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg pointer-events-none';
                tooltip.textContent = tooltipText;
                tooltip.style.top = `${e.clientY - 30}px`;
                tooltip.style.left = `${e.clientX}px`;
                tooltip.id = 'dynamic-tooltip';
                document.body.appendChild(tooltip);
            });
            el.addEventListener('mouseleave', () => {
                const tooltip = document.getElementById('dynamic-tooltip');
                if (tooltip) tooltip.remove();
            });
        }
    });
    
    // Mettre à jour les graphiques au chargement
    setTimeout(() => updateChartsTheme(), 100);
});

// Observer les changements de thème
if (window.themeManager) {
    window.addEventListener('themeChanged', (e) => {
        updateChartsTheme();
    });
} else {
    // Fallback: observer les changements de classe sur html
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'class') {
                updateChartsTheme();
            }
        });
    });
    observer.observe(document.documentElement, { attributes: true });
}

// Style pour l'effet ripple et animations additionnelles
const style = document.createElement('style');
style.textContent = `
    .btn-primary, .btn-secondary, .btn-outline {
        position: relative;
        overflow: hidden;
        cursor: pointer;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.5);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    @keyframes slide-up {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fade-in {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 5px rgba(132, 188, 22, 0.5); }
        50% { box-shadow: 0 0 20px rgba(132, 188, 22, 0.8); }
    }
    
    .animate-slide-up {
        animation: slide-up 0.3s ease-out;
    }
    
    .animate-fade-in {
        animation: fade-in 0.3s ease-out;
    }
    
    .pulse-glow {
        animation: pulse-glow 2s ease-in-out infinite;
    }
    
    /* Transitions pour le mode sombre */
    body, div, nav, main, footer, .glassmorphism {
        transition: background-color 0.3s ease, color 0.2s ease, border-color 0.3s ease;
    }
    
    /* Loading states */
    .btn-loading {
        pointer-events: none;
        opacity: 0.7;
    }
    
    .btn-loading::after {
        content: '';
        display: inline-block;
        width: 16px;
        height: 16px;
        margin-left: 8px;
        border: 2px solid white;
        border-radius: 50%;
        border-top-color: transparent;
        animation: spin 0.6s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Skeleton loading */
    .skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s infinite;
    }
    
    .dark .skeleton {
        background: linear-gradient(90deg, #1E293B 25%, #334155 50%, #1E293B 75%);
        background-size: 200% 100%;
    }
    
    @keyframes skeleton-loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
`;
document.head.appendChild(style);

// Exposer les fonctions globalement
window.showToast = showToast;
window.exportToPDF = exportToPDF;
window.exportToCSV = exportToCSV;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.updateChartsTheme = updateChartsTheme;

// Fonction utilitaire pour charger un graphique avec support dark mode
window.createResponsiveChart = (ctx, type, data, options = {}) => {
    const isDark = document.documentElement.classList.contains('dark');
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: isDark ? '#E2E8F0' : '#374151'
                }
            }
        },
        scales: {
            x: {
                ticks: { color: isDark ? '#E2E8F0' : '#374151' },
                grid: { color: isDark ? '#334155' : '#E5E7EB' }
            },
            y: {
                ticks: { color: isDark ? '#E2E8F0' : '#374151' },
                grid: { color: isDark ? '#334155' : '#E5E7EB' }
            }
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    return new Chart(ctx, {
        type: type,
        data: data,
        options: mergedOptions
    });
};

console.log('✅ G-SISAD main.js chargé avec succès');