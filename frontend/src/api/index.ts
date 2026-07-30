import client from './client';

// ─── Dashboard ───────────────────────────────────────────────────────
export const getDashboard = () => client.get('/dashboard');

// ─── Documents ───────────────────────────────────────────────────────
export const uploadDocument = (formData: FormData) =>
  client.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
export const generateDocument = (docId: string, data?: any) =>
  client.post(`/documents/${docId}/generate`, data);
export const generateManual = (body: any) =>
  client.post('/documents/generate-manual', body);
export const listDocuments = (params?: any) =>
  client.get('/documents', { params });
export const getDocument = (id: string) =>
  client.get(`/documents/${id}`);
export const deleteDocument = (id: string) =>
  client.delete(`/documents/${id}`);
export const getDownloadUrl = (id: string) =>
  `${client.defaults.baseURL}/documents/${id}/download`;

// ─── Companies ───────────────────────────────────────────────────────
export const listCompanies = (params?: any) =>
  client.get('/companies', { params });
export const createCompany = (data: any) =>
  client.post('/companies', data);
export const updateCompany = (id: string, data: any) =>
  client.put(`/companies/${id}`, data);
export const deleteCompany = (id: string) =>
  client.delete(`/companies/${id}`);

// ─── Products ────────────────────────────────────────────────────────
export const listProducts = () => client.get('/products');
export const createProduct = (data: any) => client.post('/products', data);
export const updateProduct = (id: string, data: any) => client.put(`/products/${id}`, data);
export const deleteProduct = (id: string) => client.delete(`/products/${id}`);

// ─── Inventory ───────────────────────────────────────────────────────
export const listInventory = () => client.get('/inventory');
export const getInventoryAlerts = () => client.get('/inventory/alerts');
export const adjustInventory = (productId: string, data: any) =>
  client.post(`/inventory/${productId}/adjust`, data);
export const getInventoryLogs = (productId: string) =>
  client.get(`/inventory/${productId}/logs`);

// ─── Purchase Orders ─────────────────────────────────────────────────
export const listPurchaseOrders = (params?: any) =>
  client.get('/purchase-orders', { params });
export const createPurchaseOrder = (data: any) =>
  client.post('/purchase-orders', data);
export const getPurchaseOrder = (id: string) =>
  client.get(`/purchase-orders/${id}`);
export const updatePOStatus = (id: string, status: string) =>
  client.put(`/purchase-orders/${id}/status`, { status });
export const deletePurchaseOrder = (id: string) =>
  client.delete(`/purchase-orders/${id}`);

// ─── Sales Orders ────────────────────────────────────────────────────
export const listSalesOrders = (params?: any) =>
  client.get('/sales-orders', { params });
export const createSalesOrder = (data: any) =>
  client.post('/sales-orders', data);
export const getSalesOrder = (id: string) =>
  client.get(`/sales-orders/${id}`);
export const updateSOStatus = (id: string, status: string) =>
  client.put(`/sales-orders/${id}/status`, { status });
export const deleteSalesOrder = (id: string) =>
  client.delete(`/sales-orders/${id}`);