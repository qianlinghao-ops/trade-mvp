import React, { useEffect, useState } from 'react';
import {
  Card, Table, Button, Modal, Form, InputNumber, Select,
  Space, Typography, message, Row, Col, Alert, Progress, Tag, Input,
} from 'antd';
import { WarningOutlined, PlusOutlined, MinusOutlined, EditOutlined } from '@ant-design/icons';
import { listInventory, getInventoryAlerts, adjustInventory, getInventoryLogs } from '../api';
import { InventoryItem } from '../types';

const { Title, Text } = Typography;
const { Option } = Select;

const Inventory: React.FC = () => {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [adjustVisible, setAdjustVisible] = useState(false);
  const [logsVisible, setLogsVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [invRes, alertRes] = await Promise.all([listInventory(), getInventoryAlerts()]);
      setInventory(invRes.data.items);
      setAlerts(alertRes.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleAdjust = async (values: any) => {
    if (!selectedItem) return;
    try {
      const change = values.log_type === 'out' ? -Math.abs(values.quantity_change) : Math.abs(values.quantity_change);
      await adjustInventory(selectedItem.product_id, {
        log_type: values.log_type,
        quantity_change: change,
        notes: values.notes,
      });
      message.success('在庫を更新しました');
      setAdjustVisible(false);
      form.resetFields();
      fetchAll();
    } catch (e: any) {
      message.error('更新に失敗しました: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleShowLogs = async (item: InventoryItem) => {
    setSelectedItem(item);
    const res = await getInventoryLogs(item.product_id);
    setLogs(res.data.items);
    setLogsVisible(true);
  };

  const filtered = inventory.filter(item =>
    item.product_name.includes(searchText) || item.sku.includes(searchText)
  );

  const columns = [
    { title: 'SKU', dataIndex: 'sku', key: 'sku',
      render: (v: string) => <Text code>{v}</Text> },
    { title: '商品名', dataIndex: 'product_name', key: 'product_name' },
    {
      title: '在庫数', dataIndex: 'quantity', key: 'quantity',
      render: (v: number, r: InventoryItem) => (
        <Space>
          <Text strong style={{ color: r.is_low_stock ? '#ff4d4f' : '#52c41a', fontSize: 16 }}>{v}</Text>
          <Text type="secondary">{r.unit}</Text>
          {r.is_low_stock && <Tag color="error" icon={<WarningOutlined />}>アラート</Tag>}
        </Space>
      ),
    },
    {
      title: '最低在庫数', dataIndex: 'min_stock_qty', key: 'min_stock_qty',
      render: (v: number, r: InventoryItem) => (
        <Space direction="vertical" size={0} style={{ width: 120 }}>
          <Text type="secondary">{v} {r.unit}</Text>
          <Progress
            percent={Math.min(100, Math.round((r.quantity / Math.max(v, 1)) * 100))}
            size="small"
            status={r.is_low_stock ? 'exception' : 'normal'}
            showInfo={false}
          />
        </Space>
      ),
    },
    { title: '最終更新', dataIndex: 'updated_at', key: 'updated_at',
      render: (v: string) => v ? new Date(v).toLocaleString('ja-JP') : '-' },
    {
      title: '操作', key: 'actions',
      render: (_: any, record: InventoryItem) => (
        <Space>
          <Button size="small" icon={<EditOutlined />}
            onClick={() => { setSelectedItem(record); setAdjustVisible(true); }}>
            在庫調整
          </Button>
          <Button size="small" onClick={() => handleShowLogs(record)}>
            履歴
          </Button>
        </Space>
      ),
    },
  ];

  const logColumns = [
    { title: '種別', dataIndex: 'log_type', key: 'log_type',
      render: (v: string) => {
        const map: Record<string, { label: string; color: string }> = {
          in: { label: '入荷', color: 'green' },
          out: { label: '出荷', color: 'orange' },
          adjust: { label: '調整', color: 'blue' },
        };
        const s = map[v] || { label: v, color: 'default' };
        return <Tag color={s.color}>{s.label}</Tag>;
      }
    },
    { title: '変動数', dataIndex: 'quantity_change', key: 'quantity_change',
      render: (v: number) => (
        <Text style={{ color: v > 0 ? '#52c41a' : '#ff4d4f' }}>
          {v > 0 ? `+${v}` : v}
        </Text>
      )
    },
    { title: '変動後在庫', dataIndex: 'quantity_after', key: 'quantity_after' },
    { title: '備考', dataIndex: 'notes', key: 'notes', render: (v: string) => v || '-' },
    { title: '日時', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleString('ja-JP') : '-' },
  ];

  return (
    <div>
      <Title level={4} style={{ color: '#1F3864', marginBottom: 24 }}>📦 在庫管理</Title>

      {alerts.length > 0 && (
        <Alert
          type="warning"
          icon={<WarningOutlined />}
          message={`在庫アラート: ${alerts.length}件の商品が最低在庫数を下回っています`}
          description={
            <ul style={{ margin: '8px 0 0', paddingLeft: 20 }}>
              {alerts.slice(0, 5).map(a => (
                <li key={a.product_id}>
                  {a.sku} - {a.product_name}: 現在 {a.current_qty} / 最低 {a.min_stock_qty}（不足: {a.shortage}）
                </li>
              ))}
              {alerts.length > 5 && <li>他 {alerts.length - 5}件...</li>}
            </ul>
          }
          style={{ marginBottom: 24 }}
          showIcon
        />
      )}

      <Card
        title={`在庫一覧（${filtered.length}件）`}
        extra={
          <Input.Search
            placeholder="SKU・商品名で検索"
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            style={{ width: 220 }}
            allowClear
          />
        }
      >
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="product_id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          rowClassName={(r) => r.is_low_stock ? 'ant-table-row-danger' : ''}
        />
      </Card>

      {/* 在庫調整モーダル */}
      <Modal
        title={`在庫調整: ${selectedItem?.product_name}`}
        open={adjustVisible}
        onCancel={() => setAdjustVisible(false)}
        footer={null}
      >
        <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
          現在の在庫数: <Text strong style={{ fontSize: 18 }}>{selectedItem?.quantity} {selectedItem?.unit}</Text>
        </Text>
        <Form form={form} layout="vertical" onFinish={handleAdjust}>
          <Form.Item name="log_type" label="調整種別" initialValue="adjust" rules={[{ required: true }]}>
            <Select>
              <Option value="in">入荷（在庫増加）</Option>
              <Option value="out">出荷（在庫減少）</Option>
              <Option value="adjust">棚卸調整</Option>
            </Select>
          </Form.Item>
          <Form.Item name="quantity_change" label="数量" rules={[{ required: true, message: '数量を入力してください' }]}>
            <InputNumber min={1} style={{ width: '100%' }} placeholder="調整数量（正の数で入力）" />
          </Form.Item>
          <Form.Item name="notes" label="備考">
            <Input.TextArea rows={2} placeholder="調整理由など" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block style={{ background: '#1F3864' }}>
              在庫を更新
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* 履歴モーダル */}
      <Modal
        title={`入出庫履歴: ${selectedItem?.product_name}`}
        open={logsVisible}
        onCancel={() => setLogsVisible(false)}
        footer={null}
        width={700}
      >
        <Table
          dataSource={logs}
          columns={logColumns}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 10 }}
        />
      </Modal>
    </div>
  );
};

export default Inventory;