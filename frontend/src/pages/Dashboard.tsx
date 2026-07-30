import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Typography, Space, Alert, Spin, Tag } from 'antd';
import {
  ShoppingCartOutlined, InboxOutlined, AppstoreOutlined,
  FileTextOutlined, WarningOutlined, ArrowUpOutlined,
} from '@ant-design/icons';
import { getDashboard } from '../api';
import { DashboardData } from '../types';
import { POStatusTag, SOStatusTag, DocStatusTag, DocTypeTag, formatAmount } from '../components/StatusTag';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getDashboard().then(r => setData(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
  if (!data) return <Alert type="error" message="データ取得に失敗しました" />;

  const statCards = [
    {
      title: '発注管理', icon: <ShoppingCartOutlined style={{ color: '#1F3864', fontSize: 28 }} />,
      value: data.purchase_orders.total, suffix: '件',
      sub: `進行中: ${data.purchase_orders.active}件 / 下書き: ${data.purchase_orders.pending}件`,
      color: '#e8f0fe', onClick: () => navigate('/purchase-orders'),
    },
    {
      title: '受注管理', icon: <InboxOutlined style={{ color: '#2E74B5', fontSize: 28 }} />,
      value: data.sales_orders.total, suffix: '件',
      sub: `進行中: ${data.sales_orders.active}件 / 出荷済: ${data.sales_orders.shipped}件`,
      color: '#e3f2fd', onClick: () => navigate('/sales-orders'),
    },
    {
      title: '在庫管理', icon: <AppstoreOutlined style={{ color: data.inventory.low_stock_alerts > 0 ? '#ff4d4f' : '#52c41a', fontSize: 28 }} />,
      value: data.inventory.total_skus, suffix: 'SKU',
      sub: data.inventory.low_stock_alerts > 0
        ? `⚠️ アラート: ${data.inventory.low_stock_alerts}件`
        : '在庫正常',
      color: data.inventory.low_stock_alerts > 0 ? '#fff2f0' : '#f6ffed',
      onClick: () => navigate('/inventory'),
    },
    {
      title: '書類管理', icon: <FileTextOutlined style={{ color: '#722ed1', fontSize: 28 }} />,
      value: data.documents.total, suffix: '件',
      sub: '生成済み書類の総数',
      color: '#f9f0ff', onClick: () => navigate('/documents'),
    },
  ];

  const poColumns = [
    { title: '発注番号', dataIndex: 'po_number', key: 'po_number',
      render: (v: string, r: any) => <a onClick={() => navigate('/purchase-orders')}>{v}</a> },
    { title: '仕入先', dataIndex: 'supplier_name', key: 'supplier_name' },
    { title: 'ステータス', dataIndex: 'status', key: 'status', render: (v: string) => <POStatusTag status={v} /> },
    { title: '金額', dataIndex: 'total_amount', key: 'total_amount',
      render: (v: number, r: any) => formatAmount(v, r.currency) },
    { title: '発注日', dataIndex: 'order_date', key: 'order_date' },
  ];

  const soColumns = [
    { title: '受注番号', dataIndex: 'so_number', key: 'so_number',
      render: (v: string) => <a onClick={() => navigate('/sales-orders')}>{v}</a> },
    { title: '得意先', dataIndex: 'customer_name', key: 'customer_name' },
    { title: 'ステータス', dataIndex: 'status', key: 'status', render: (v: string) => <SOStatusTag status={v} /> },
    { title: '金額', dataIndex: 'total_amount', key: 'total_amount',
      render: (v: number, r: any) => formatAmount(v, r.currency) },
    { title: '受注日', dataIndex: 'order_date', key: 'order_date' },
  ];

  const docColumns = [
    { title: '書類種別', dataIndex: 'doc_type', key: 'doc_type', render: (v: string) => <DocTypeTag type={v} /> },
    { title: 'ファイル名', dataIndex: 'original_filename', key: 'original_filename',
      render: (v: string) => <Text ellipsis style={{ maxWidth: 180 }}>{v}</Text> },
    { title: 'ステータス', dataIndex: 'status', key: 'status', render: (v: string) => <DocStatusTag status={v} /> },
    { title: '作成日時', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleString('ja-JP') : '-' },
  ];

  return (
    <div>
      <Title level={4} style={{ color: '#1F3864', marginBottom: 24 }}>
        📊 ダッシュボード
      </Title>

      {data.inventory.low_stock_alerts > 0 && (
        <Alert
          type="warning"
          icon={<WarningOutlined />}
          message={`在庫アラート: ${data.inventory.low_stock_alerts}件の商品が最低在庫数を下回っています`}
          action={<a onClick={() => navigate('/inventory')}>確認する →</a>}
          style={{ marginBottom: 24 }}
          showIcon
        />
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {statCards.map((card, i) => (
          <Col xs={24} sm={12} lg={6} key={i}>
            <Card
              hoverable
              onClick={card.onClick}
              style={{ background: card.color, border: 'none', cursor: 'pointer' }}
              bodyStyle={{ padding: '20px 24px' }}
            >
              <Space align="start" style={{ width: '100%', justifyContent: 'space-between' }}>
                <div>
                  <Text type="secondary" style={{ fontSize: 13 }}>{card.title}</Text>
                  <div style={{ fontSize: 32, fontWeight: 700, color: '#1F3864', lineHeight: 1.2 }}>
                    {card.value}<span style={{ fontSize: 14, fontWeight: 400, marginLeft: 4 }}>{card.suffix}</span>
                  </div>
                  <Text type="secondary" style={{ fontSize: 12 }}>{card.sub}</Text>
                </div>
                {card.icon}
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="📦 最近の発注" size="small" extra={<a onClick={() => navigate('/purchase-orders')}>すべて見る</a>}>
            <Table
              dataSource={data.recent_purchase_orders}
              columns={poColumns}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="📬 最近の受注" size="small" extra={<a onClick={() => navigate('/sales-orders')}>すべて見る</a>}>
            <Table
              dataSource={data.recent_sales_orders}
              columns={soColumns}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
        <Col xs={24}>
          <Card title="📄 最近の書類" size="small" extra={<a onClick={() => navigate('/documents')}>すべて見る</a>}>
            <Table
              dataSource={data.documents.recent}
              columns={docColumns}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;