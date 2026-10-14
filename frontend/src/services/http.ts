import axios from 'axios'

/** Single axios client for every REST call (/api/v1, proxied by Vite / nginx). */
export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000, // agent processing can take minutes
})
