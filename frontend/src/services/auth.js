import api from './api'

export const authService = {
  /**
   * Register a new user
   * @param {string} username
   * @param {string} email
   * @param {string} password
   * @returns {Promise<{user: object}>}
   */
  async register(username, email, password) {
    try {
      const response = await api.post('/auth/register', {
        username,
        email,
        password,
      })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  },

  /**
   * Login user
   * @param {string} email
   * @param {string} password
   * @returns {Promise<{token: string, user: object}>}
   */
  async login(email, password) {
    try {
      const response = await api.post('/auth/login', {
        email,
        password,
      })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  },

  /**
   * Get current user profile
   * @returns {Promise<{user: object}>}
   */
  async getCurrentUser() {
    try {
      const response = await api.get('/auth/me')
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  },

  /**
   * Update current user's username
   * @param {string} username
   * @returns {Promise<{user: object}>}
   */
  async updateUsername(username) {
    try {
      const response = await api.patch('/auth/me', { username })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  },

  /**
   * Logout user
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      // Even if logout fails on server, clear local state
      console.error('Logout error:', error)
    }
  },

  /**
   * Handle API errors
   * @param {Error} error
   * @returns {Error}
   */
  handleError(error) {
    if (error.response?.data?.error) {
      return new Error(error.response.data.error)
    }
    if (error.message) {
      return new Error(error.message)
    }
    return new Error('An unexpected error occurred')
  },
}

