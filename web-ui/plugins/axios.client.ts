import axios from 'axios'

export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  
  const baseURL = `${config.public.apiBase || 'http://localhost:8080'}/api`

  console.log(`[Axios] BaseURL set to: ${baseURL}`)

  const apiClient = axios.create({
    baseURL,
    timeout: 30000,
    withCredentials: true
  })

  apiClient.interceptors.request.use(
    request => {
      console.log(`[API Request] Sending: ${request.method?.toUpperCase()} ${request.url}`)
      return request
    },
    error => {
      console.error('[API Request Error] Request failed before sending:', error)
      return Promise.reject(error)
    }
  )

  apiClient.interceptors.response.use(
    response => {
      console.log(`[API Response] Received from: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data
      })
      return response.data
    },
    error => {
      let message = 'Network error'
      if (error.response) {
        message = `[${error.response.status}] ${error.response.data?.detail || error.response.data?.message || error.response.statusText}`
      } else if (error.request) {
        message = 'No response from server. Check backend logs and network connection.'
      }
      console.error('[API Response Error]', message, error)
      return Promise.reject(new Error(message))
    }
  )

  nuxtApp.provide('api', apiClient)
})