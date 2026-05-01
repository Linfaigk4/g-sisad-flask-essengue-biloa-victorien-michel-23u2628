// Gestion du thème sombre/clair
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }
    
    init() {
        // Appliquer le thème sauvegardé
        if (this.theme === 'dark') {
            document.documentElement.classList.add('dark');
            document.body.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
            document.body.classList.remove('dark');
        }
        
        // Créer et ajouter le bouton de toggle
        this.createToggleButton();
        
        // Écouter les changements de thème système
        this.watchSystemTheme();
    }
    
    createToggleButton() {
        const toggleHtml = `
            <button id="theme-toggle" class="relative inline-flex items-center p-2 rounded-lg 
                hover:bg-gray-100 dark:hover:bg-dark-surface-lighter transition-all duration-300
                group focus:outline-none focus:ring-2 focus:ring-lime">
                <i id="theme-icon-sun" class="fas fa-sun text-yellow-500 text-xl 
                    ${this.theme === 'dark' ? 'hidden' : 'block'} 
                    group-hover:rotate-12 transition-transform"></i>
                <i id="theme-icon-moon" class="fas fa-moon text-gray-400 text-xl 
                    ${this.theme === 'dark' ? 'block' : 'hidden'} 
                    group-hover:-rotate-12 transition-transform"></i>
                <span class="sr-only">Changer le thème</span>
            </button>
        `;
        
        // Insérer le bouton dans la navigation
        const nav = document.querySelector('nav .flex.justify-between');
        if (nav) {
            const existingButton = document.getElementById('theme-toggle');
            if (existingButton) existingButton.remove();
            
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = toggleHtml;
            const toggleButton = tempDiv.firstElementChild;
            
            // Trouver l'endroit où insérer (à côté du menu utilisateur)
            const menuDiv = nav.querySelector('.flex.items-center.space-x-6');
            if (menuDiv) {
                menuDiv.insertBefore(toggleButton, menuDiv.children[menuDiv.children.length - 1]);
            } else {
                nav.appendChild(toggleButton);
            }
            
            // Ajouter l'événement
            toggleButton.addEventListener('click', () => this.toggleTheme());
        }
    }
    
    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        
        if (this.theme === 'dark') {
            document.documentElement.classList.add('dark');
            document.body.classList.add('dark');
            document.getElementById('theme-icon-sun')?.classList.add('hidden');
            document.getElementById('theme-icon-moon')?.classList.remove('hidden');
        } else {
            document.documentElement.classList.remove('dark');
            document.body.classList.remove('dark');
            document.getElementById('theme-icon-sun')?.classList.remove('hidden');
            document.getElementById('theme-icon-moon')?.classList.add('hidden');
        }
        
        // Déclencher un événement personnalisé pour les autres composants
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: this.theme } }));
        
        // Animation de transition
        this.animateThemeTransition();
    }
    
    animateThemeTransition() {
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 bg-white dark:bg-dark-bg pointer-events-none z-50 opacity-0 transition-opacity duration-300';
        document.body.appendChild(overlay);
        
        setTimeout(() => overlay.classList.add('opacity-100'), 10);
        setTimeout(() => {
            overlay.classList.remove('opacity-100');
            setTimeout(() => overlay.remove(), 300);
        }, 300);
    }
    
    watchSystemTheme() {
        // Écouter les changements de thème système (préfère mode sombre)
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.theme = e.matches ? 'dark' : 'light';
                this.toggleTheme();
            }
        });
    }
    
    getCurrentTheme() {
        return this.theme;
    }
    
    // Méthode utilitaire pour les graphiques
    getChartTheme() {
        if (this.theme === 'dark') {
            return {
                background: '#1E293B',
                textColor: '#E2E8F0',
                gridColor: '#334155',
                axisColor: '#475569'
            };
        }
        return {
            background: '#FFFBEA',
            textColor: '#374151',
            gridColor: '#E5E7EB',
            axisColor: '#9CA3AF'
        };
    }
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Exporter pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}