import React, { useState } from 'react';
import { Layout, Menu, Badge, Typography, Space } from 'antd';
import {
  DashboardOutlined, FileTextOutlined, ShoppingCartOutlined,
  InboxOutlined, AppstoreOutlined, TeamOutlined, WarningOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

interface AppLayoutProps {
  children: React.ReactNode;
  alertCount?: number;
}

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'ダッシュボード' },
  { key: '/documents', icon: <FileTextOutlined />, label: '書類管理' },
  { key: '/purchase-orders', icon: <ShoppingCartOutlined />, label: '発注管理' },
  { key: '/sales-orders', icon: <InboxOutlined />, label: '受注管理' },
  { key: '/inventory', icon: <AppstoreOutlined />, label: '在庫管理' },
  { key: '/companies', icon: <TeamOutlined />, label: '取引先管理' },
  { key: '/products', icon: <AppstoreOutlined />, label: '商品マスタ' },
];

const AppLayout: React.FC<AppLayoutProps> = ({ children, alertCount = 0 }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={220}
        style={{ background: '#1F3864' }}
        trigger={null}
      >
        <div style={{
          padding: collapsed ? '16px 8px' : '16px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          marginBottom: 8,
        }}>
          {!collapsed && (
            <Title level={5} style={{ color: '#fff', margin: 0, fontSize: 13, lineHeight: '1.4' }}>
              🚢 貿易業務<br />自動化システム
            </Title>
          )}
          {collapsed && <span style={{ color: '#fff', fontSize: 20 }}>🚢</span>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          style={{ background: '#1F3864', borderRight: 0 }}
          onClick={({ key }) => navigate(key)}
          items={menuItems.map(item => ({
            key: item.key,
            icon: item.icon,
            label: item.key === '/inventory' && alertCount > 0
              ? <Badge count={alertCount} size="small" offset={[8, 0]}>{item.label}</Badge>
              : item.label,
          }))}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          height: 56,
        }}>
          <Space>
            {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
              style: { fontSize: 18, cursor: 'pointer', color: '#1F3864' },
              onClick: () => setCollapsed(!collapsed),
            })}
          </Space>
          <Space>
            {alertCount > 0 && (
              <Space style={{ color: '#ff4d4f', fontSize: 13 }}>
                <WarningOutlined />
                在庫アラート {alertCount}件
              </Space>
            )}
            <span style={{ color: '#888', fontSize: 13 }}>管理者</span>
          </Space>
        </Header>
        <Content style={{ margin: '24px', background: '#f5f7fa', minHeight: 'calc(100vh - 56px)' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;