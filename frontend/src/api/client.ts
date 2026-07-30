import axios from 'axios';

const API_BASE = (import.meta as any).env?.VITE_API_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export default client;