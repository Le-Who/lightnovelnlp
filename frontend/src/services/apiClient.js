import axios from 'axios'

// Определяем базовый URL API
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 240000, // 4 minutes for long operations (analysis with multiple Gemini API calls)
  headers: {
    // 'Content-Type': 'application/json', // axios automatically sets this based on data
  },
})

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api
