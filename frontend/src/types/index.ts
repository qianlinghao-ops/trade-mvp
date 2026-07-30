export type DocType = 'po' | 'invoice' | 'packing_list' | 'bl' | 'coo' | 'customs' | 'other';
export type DocStatus = 'uploading' | 'processing' | 'review' | 'completed' | 'error';
export type CompanyType = 'supplier' | 'customer';
export type POStatus = 'draft' | 'ordered' | 'confirmed' | 'in_transit' | 'received' | 'completed' | 'cancelled';
export type SOStatus = 'draft' | 'received' | 'confirmed' | 'preparing' | 'shipped' | 'completed' | 'cancelled';

export interface Company {
  id: string;
  company_name: string;
  company_type: CompanyType;
  country?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  created_at?: string;
}

export interface Product {
  id: string;
  sku: string;
  product_name: string;
  product_name_en?: string;
  hs_code?: string;
  unit_price: number;
  currency: string;
  unit: string;
  min_stock_qty: number;
  current_stock: number;
  is_low_stock: boolean;
  supplier_id?: string;
}

export interface OrderItem {
  id?: string;
  product_id?: string;
  product_name: string;
  sku?: string;
  quantity: number;
  unit_price: number;
  amount: number;
  unit?: string;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  supplier_id: string;
  supplier_name?: string;
  status: POStatus;
  order_date?: string;
  expected_date?: string;
  total_amount: number;
  currency: string;
  payment_terms?: string;
  notes?: string;
  created_at?: string;
  items: OrderItem[];
}

export interface SalesOrder {
  id: string;
  so_number: string;
  customer_id: string;
  customer_name?: string;
  status: SOStatus;
  order_date?: string;
  delivery_date?: string;
  total_amount: number;
  currency: string;
  payment_terms?: string;
  destination?: string;
  notes?: string;
  created_at?: string;
  items: OrderItem[];
}

export interface Document {
  id: string;
  doc_type: DocType;
  status: DocStatus;
  original_filename?: string;
  confidence_score?: number;
  has_generated?: boolean;
  created_at?: string;
  extracted_data?: any;
  generated_filename?: string;
}

export interface InventoryItem {
  id: string;
  product_id: string;
  sku: string;
  product_name: string;
  quantity: number;
  min_stock_qty: number;
  is_low_stock: boolean;
  unit: string;
  updated_at?: string;
}

export interface DashboardData {
  purchase_orders: { total: number; active: number; pending: number };
  sales_orders: { total: number; active: number; shipped: number };
  inventory: { total_skus: number; low_stock_alerts: number };
  documents: { total: number; recent: Document[] };
  recent_purchase_orders: PurchaseOrder[];
  recent_sales_orders: SalesOrder[];
}