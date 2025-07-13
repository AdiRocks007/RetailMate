// Frontend API Client for RetailMate
// This module handles all communication with the FastAPI backend

class RetailMateAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.conversationId = null;
        this.userId = this.getUserId();
    }

    // Get or create user ID (stored in localStorage)
    getUserId() {
        let userId = localStorage.getItem('retailmate_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('retailmate_user_id', userId);
        }
        return userId;
    }

    // Generic fetch wrapper with error handling
    async makeRequest(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        return await this.makeRequest('/health');
    }

    // Chat endpoints
    async sendMessage(message, conversationId = null) {
        const response = await this.makeRequest('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message,
                conversation_id: conversationId || this.conversationId,
                user_id: this.userId
            })
        });

        // Update conversation ID
        this.conversationId = response.conversation_id;
        return response;
    }

    // Shopping recommendations
    async getShoppingRecommendations(query) {
        return await this.makeRequest('/shopping/recommend', {
            method: 'POST',
            body: JSON.stringify({
                query,
                user_id: this.userId
            })
        });
    }

    // Cart-aware shopping
    async getCartAwareRecommendations(query) {
        return await this.makeRequest('/shopping/cart-aware', {
            method: 'POST',
            body: JSON.stringify({
                query,
                user_id: this.userId
            })
        });
    }

    // Event shopping advice
    async getEventShoppingAdvice(eventId) {
        return await this.makeRequest(`/events/${eventId}/shopping-advice`, {
            method: 'POST'
        });
    }

    // Cart management
    async getCart() {
        return await this.makeRequest(`/cart/${this.userId}`);
    }

    async getCartSummary() {
        return await this.makeRequest(`/cart/${this.userId}/summary`);
    }

    async addToCart(productId, quantity = 1) {
        return await this.makeRequest(`/cart/${this.userId}/add`, {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                quantity
            })
        });
    }

    async removeFromCart(productId, quantity = 1) {
        return await this.makeRequest(`/cart/${this.userId}/remove`, {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                quantity
            })
        });
    }

    async clearCart() {
        return await this.makeRequest(`/cart/${this.userId}/clear`, {
            method: 'DELETE'
        });
    }

    async getCartSuggestions() {
        return await this.makeRequest(`/cart/${this.userId}/suggestions`);
    }

    // Calendar
    async getUpcomingEvents() {
        return await this.makeRequest('/calendar/events');
    }

    async getEventDetails(eventId) {
        return await this.makeRequest(`/calendar/events/${eventId}`);
    }

    // Conversation management
    async getConversationHistory(conversationId = null) {
        const id = conversationId || this.conversationId;
        if (!id) throw new Error('No conversation ID available');
        return await this.makeRequest(`/conversations/${id}`);
    }

    async clearConversation(conversationId = null) {
        const id = conversationId || this.conversationId;
        if (!id) throw new Error('No conversation ID available');
        return await this.makeRequest(`/conversations/${id}`, {
            method: 'DELETE'
        });
    }
}

// Export for use in other modules
window.RetailMateAPI = RetailMateAPI;

// Create global instance
window.retailMateAPI = new RetailMateAPI();