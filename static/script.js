// Theme Management
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.theme);
        this.bindEvents();
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.theme);
    }

    bindEvents() {
        const toggleButtons = document.querySelectorAll('#themeToggle, #themeToggleFooter');
        toggleButtons.forEach(button => {
            button.addEventListener('click', () => this.toggleTheme());
        });
    }
}

// News Ticker
class NewsTicker {
    constructor() {
        this.tickerContent = document.querySelector('.ticker-content');
        this.init();
    }

    init() {
        if (this.tickerContent) {
            this.duplicateItems();
        }
    }

    duplicateItems() {
        const items = this.tickerContent.innerHTML;
        this.tickerContent.innerHTML += items;
    }
}

// Animated Background
class BackgroundAnimator {
    constructor() {
        this.init();
    }

    init() {
        this.createStars();
        this.createFloatingElements();
    }

    createStars() {
        const starsContainer = document.querySelector('.stars');
        if (!starsContainer) return;

        for (let i = 0; i < 50; i++) {
            const star = document.createElement('div');
            star.style.cssText = `
                position: absolute;
                width: ${Math.random() * 3}px;
                height: ${Math.random() * 3}px;
                background: white;
                border-radius: 50%;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                animation: twinkle ${2 + Math.random() * 3}s infinite alternate;
            `;
            starsContainer.appendChild(star);
        }
    }

    createFloatingElements() {
        const background = document.querySelector('.background');
        const elements = ['📚', '🎓', '📖', '✏️', '🔬', '💻'];

        elements.forEach((emoji, index) => {
            const element = document.createElement('div');
            element.textContent = emoji;
            element.style.cssText = `
                position: absolute;
                font-size: ${20 + Math.random() * 30}px;
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                opacity: ${0.1 + Math.random() * 0.2};
                animation: float ${15 + Math.random() * 20}s infinite linear;
                animation-delay: -${Math.random() * 20}s;
                z-index: 1;
            `;
            background.appendChild(element);
        });
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme manager
    new ThemeManager();
    
    // Initialize news ticker
    new NewsTicker();
    
    // Initialize background animations
    new BackgroundAnimator();

    // Add floating animation to cards
    const cards = document.querySelectorAll('.subject-card, .pdf-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(-5px) scale(1)';
        });
    });

    // Add loading animation
    const main = document.querySelector('main');
    if (main) {
        main.style.opacity = '0';
        main.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            main.style.transition = 'all 0.5s ease';
            main.style.opacity = '1';
            main.style.transform = 'translateY(0)';
        }, 100);
    }
});

// Add CSS for floating animation
const style = document.createElement('style');
style.textContent = `
    @keyframes twinkle {
        0% { opacity: 0.2; }
        100% { opacity: 1; }
    }
    
    @keyframes float {
        0% {
            transform: translate(0, 0) rotate(0deg);
        }
        25% {
            transform: translate(100px, 100px) rotate(90deg);
        }
        50% {
            transform: translate(200px, 0) rotate(180deg);
        }
        75% {
            transform: translate(100px, -100px) rotate(270deg);
        }
        100% {
            transform: translate(0, 0) rotate(360deg);
        }
    }
    
    .subject-card, .pdf-card {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
`;
document.head.appendChild(style);