/**
 * UrgentCountManager - Client-Side Count Management
 * Properly manages urgent email counts and prevents drift
 */

class UrgentCountManager {
    constructor() {
        this.currentCounts = {};
        this.countElements = new Map();
        this.initialized = false;
        this.debug = true;
    }

    async init() {
        if (this.initialized) return;
        
        try {
            await this.fetchCurrentCounts();
            this.mapCountElements();
            this.updateAllDisplays();
            this.setupEventListeners();
            this.initialized = true;
            console.log('✅ UrgentCountManager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize UrgentCountManager:', error);
        }
    }

    async fetchCurrentCounts() {
        try {
            const response = await fetch('/api/urgent_counts');
            if (response.ok) {
                this.currentCounts = await response.json();
                console.log('📊 Current counts:', this.currentCounts);
            } else {
                throw new Error('Failed to fetch counts');
            }
        } catch (error) {
            console.error('Error fetching counts:', error);
            this.calculateCountsFromDOM();
        }
    }

    mapCountElements() {
        this.countElements.clear();
        
        // Look for elements with data-count-type attributes
        const mappings = [
            { selector: '[data-count-type="critical"]', type: 'critical' },
            { selector: '[data-count-type="high"]', type: 'high' },
            { selector: '[data-count-type="unread"]', type: 'unread' },
            { selector: '[data-count-type="requires_action"]', type: 'requires_action' }
        ];

        mappings.forEach(mapping => {
            const elements = document.querySelectorAll(mapping.selector);
            elements.forEach(el => {
                this.countElements.set(el, mapping.type);
                console.log(`🎯 Mapped ${mapping.type}:`, el.textContent.trim(), el);
            });
        });

        console.log(`📍 Mapped ${this.countElements.size} count elements`);
    }

    updateAllDisplays() {
        this.countElements.forEach((countType, element) => {
            const currentCount = this.currentCounts[countType] || 0;
            this.updateElementDisplay(element, currentCount);
        });
    }

    updateElementDisplay(element, newValue) {
        const oldValue = element.textContent.trim();
        
        if (oldValue !== newValue.toString()) {
            element.textContent = newValue;
            this.animateCountChange(element);
            console.log(`🔄 Updated count from ${oldValue} to ${newValue}`);
        }
    }

    animateCountChange(element) {
        element.style.transition = 'all 0.5s ease';
        element.style.backgroundColor = '#28a745';
        element.style.color = 'white';
        element.style.padding = '2px 6px';
        element.style.borderRadius = '4px';
        element.style.transform = 'scale(1.1)';

        setTimeout(() => {
            element.style.backgroundColor = '';
            element.style.color = '';
            element.style.padding = '';
            element.style.transform = '';
        }, 2000);
    }

    async markAsRead(emailId, priority) {
        try {
            const response = await fetch(`/api/mark_read/${emailId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const result = await response.json();
                if (result.status === 'success') {
                    this.currentCounts = result.counts;
                    this.updateAllDisplays();
                    this.showSuccessMessage('Email marked as read');
                    return true;
                }
            }
            throw new Error('Failed to mark as read');
        } catch (error) {
            console.error('Error marking as read:', error);
            return false;
        }
    }

    async markAsReplied(emailId) {
        try {
            const response = await fetch(`/api/mark_replied/${emailId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const result = await response.json();
                if (result.status === 'success') {
                    this.currentCounts = result.counts;
                    this.updateAllDisplays();
                    this.showSuccessMessage('Email reply sent and counts updated');
                    return true;
                }
            }
            throw new Error('Failed to mark as replied');
        } catch (error) {
            console.error('Error marking as replied:', error);
            return false;
        }
    }

    showSuccessMessage(message) {
        const alertDiv = document.createElement('div');
        alertDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 16px 20px;
            border-radius: 8px;
            z-index: 9999;
            max-width: 350px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
        `;
        
        alertDiv.innerHTML = `
            <div style="display: flex; align-items: center;">
                <div style="font-size: 20px; margin-right: 10px;">✅</div>
                <div>
                    <strong>${message}</strong>
                    <br><small>Counts updated automatically</small>
                </div>
            </div>
        `;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => alertDiv.remove(), 300);
        }, 3000);
    }

    calculateCountsFromDOM() {
        console.log('📊 Calculating counts from DOM as fallback');
        this.currentCounts = { critical: 0, high: 0, unread: 0, requires_action: 0 };
    }

    setupEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="mark-read"]')) {
                const emailId = e.target.dataset.emailId;
                const priority = e.target.dataset.priority;
                if (emailId) {
                    this.markAsRead(parseInt(emailId), priority);
                }
            }
        });
    }
}

// CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(100%); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideOut {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(100%); }
    }
`;
document.head.appendChild(style);

// Global instance
window.urgentCountManager = new UrgentCountManager();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing UrgentCountManager...');
    await window.urgentCountManager.init();
});

// Debug functions
window.testCounts = () => window.urgentCountManager.updateAllDisplays();
window.getCountDiagnostics = () => ({
    currentCounts: window.urgentCountManager.currentCounts,
    mappedElements: window.urgentCountManager.countElements.size
});
