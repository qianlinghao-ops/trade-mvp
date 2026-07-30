import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import AppLayout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import PurchaseOrders from './pages/PurchaseOrders';
import SalesOrders from './pages/SalesOrders';
import Inventory from './pages/Inventory';
import Companies from './pages/Companies';
import Products from './pages/Products';
import ForecastOrders from './pages/ForecastOrders';
import { getInventoryAlerts } from './api';
import 'antd/dist/reset.css';

const App: React.FC = () => {
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    getInventoryAlerts().then(r => setAlertCount(r.data.total)).catch(() => {});
    const interval = setInterval(() => {
      getInventoryAlerts().then(r => setAlertCount(r.data.total)).catch(() => {});
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <ConfigProvider locale={jaJP} theme={{
      token: {
        colorPrimary: '#1F3864',
        borderRadius: 6,
        fontFamily: "'Noto Sans JP', 'Helvetica Neue', Arial, sans-serif",
      }
    }}>
      <BrowserRouter>
        <AppLayout alertCount={alertCount}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/purchase-orders" element={<PurchaseOrders />} />
            <Route path="/sales-orders" element={<SalesOrders />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/products" element={<Products />} />
            <Route path="/forecast" element={<ForecastOrders />} />
          </Routes>
        </AppLayout>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;