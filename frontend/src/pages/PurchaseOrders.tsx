import React, { useEffect, useState } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, InputNumber, Select,
  Space, Typography, Divider, message, Row, Col, DatePicker, Tag,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import {
  listPurchaseOrders, createPurchaseOrder, updatePOStatus,
  deletePurchaseOrder, listCompanies, listProducts,
} from '../api';
import { PurchaseOrder, Company, Product } from '../types';
import { POStatusTag, formatAmount } from '../components/StatusTag';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

const PO_STATUSES = [
  { value: 'draft', label: '下書き' },
  { value: 'ordered', label: '発注済' },
  { value: 'confirmed', label: '確認済' },
  { value: 'in_transit', label: '輸送中' },
  { value: 'received', label: '入荷済（在庫自動更新）' },
  { value: 'completed', label: '完了' },
  { value: 'cancelled', label: 'キャンセル' },
];

const PurchaseOrders: React.FC = () => {
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [statusModalVisible, setStatusModalVisible] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrder | null>(null);
  const [suppliers, setSuppliers] = useState<Company[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [form] = Form.useForm();

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [ordersRes, suppliersRes, productsRes] = await Promise.all([
        listPurchaseOrders(filterStatus ? { status: filterStatus } : {}),
        listCompanies({ company_type: 'supplier' }),
        listProducts(),
      ]);
      setOrders(ordersRes.data.items);
      setSuppliers(suppliersRes.data.items);
      setProducts(productsRes.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, [filterStatus]);

  const handleCreate = async (values: any) => {
    try {
      const items = (values.items || []).map((item: any) => ({
        ...item,
        amount: (item.quantity || 0) * (item.unit_price || 0),
      }));
      await createPurchaseOrder({
        ...values,
        order_date: values.order_date ? values.order_date.format('YYYY-MM-DD') : undefined,
        expected_date: values.expected_date ? values.expected_date.format('YYYY-MM-DD') : undefined,
        items,
      });
      message.success('発注書を作成しました');
      setModalVisible(false);
      form.resetFields();
      fetchAll();
    } catch (e: any) {
      message.error('作成に失敗しました: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleStatusUpdate = async (status: string) => {
    if (!selectedOrder) return;
    try {
      await updatePOStatus(selectedOrder.id, status);
      message.success(status === 'received' ? '入荷済に更新しました。在庫が自動更新されました！' : 'ステータスを更新しました');
      setStatusModalVisible(false);
      fetchAll();
    } catch (e) {
      message.error('更新に失敗しました');
    }
  };

  const handleDelete = async (id: string) => {
    await deletePurchaseOrder(id);
    message.success('削除しました');
    fetchAll();
  };

  const expandedRowRender = (record: PurchaseOrder) => (
    <Table
      dataSource={record.items}
      rowKey="id"
      size="small"
      pagination={false}
      columns={[
        { title: '品名', dataIndex: 'product_name', key: 'product_name' },
        { title: 'SKU', dataIndex: 'sku', key: 'sku' },
        { title: '数量', dataIndex: 'quantity', key: 'quantity' },
        { title: '単位', dataIndex: 'unit', key: 'unit' },
        { title: '単価', dataIndex: 'unit_price', key: 'unit_price',
          render: (v: number, r: any) => formatAmount(v, record.currency) },
        { title: '金額', dataIndex: 'amount', key: 'amount',
          render: (v: number) => formatAmount(v, record.currency) },
      ]}
    />
  );

  const columns = [
    { title: '発注番号', dataIndex: 'po_number', key: 'po_number',
      render: (v: string) => <Text strong>{v}</Text> },
    { title: '仕入先', dataIndex: 'supplier_name', key: 'supplier_name' },
    { title: 'ステータス', dataIndex: 'status', key: 'status',
      render: (v: string) => <POStatusTag status={v} /> },
    { title: '発注日', dataIndex: 'order_date', key: 'order_date' },
    { title: '入荷予定日', dataIndex: 'expected_date', key: 'expected_date',
      render: (v: string) => v || '-' },
    { title: '合計金額', dataIndex: 'total_amount', key: 'total_amount',
      render: (v: number, r: any) => <Text strong>{formatAmount(v, r.currency)}</Text> },
    {
      title: '操作', key: 'actions',
      render: (_: any, record: PurchaseOrder) => (
        <Space>
          <Button size="small" icon={<EditOutlined />}
            onClick={() => { setSelectedOrder(record); setStatusModalVisible(true); }}>
            ステータス変更
          </Button>
          <Button size="small" icon={<DeleteOutlined />} danger
            onClick={() => handleDelete(record.id)}>削除</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ color: '#1F3864', marginBottom: 24 }}>📦 発注管理</Title>

      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Text>ステータス絞り込み：</Text>
              <Select value={filterStatus} onChange={setFilterStatus} style={{ width: 160 }} allowClear placeholder="すべて">
                {PO_STATUSES.map(s => <Option key={s.value} value={s.value}>{s.label}</Option>)}
              </Select>
            </Space>
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />}
              onClick={() => setModalVisible(true)}
              style={{ background: '#1F3864' }}>
              新規発注書作成
            </Button>
          </Col>
        </Row>
      </Card>

      <Card title={`発注一覧（${orders.length}件）`}>
        <Table
          dataSource={orders}
          columns={columns}
          rowKey="id"
          loading={loading}
          expandable={{ expandedRowRender }}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* 新規作成モーダル */}
      <Modal
        title="📦 新規発注書作成"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        width={800}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="supplier_id" label="仕入先" rules={[{ required: true, message: '仕入先を選択してください' }]}>
                <Select placeholder="仕入先を選択">
                  {suppliers.map(s => <Option key={s.id} value={s.id}>{s.company_name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="currency" label="通貨" initialValue="JPY">
                <Select>
                  <Option value="JPY">JPY（円）</Option>
                  <Option value="USD">USD（ドル）</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="order_date" label="発注日">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expected_date" label="入荷予定日">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="payment_terms" label="支払条件">
            <Input placeholder="T/T 30 days" />
          </Form.Item>
          <Divider>発注明細</Divider>
          <Form.List name="items" initialValue={[{ product_name: '', quantity: 1, unit_price: 0, unit: '個' }]}>
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...rest }) => (
                  <Row key={key} gutter={8} style={{ marginBottom: 8 }}>
                    <Col span={8}>
                      <Form.Item {...rest} name={[name, 'product_id']} noStyle>
                        <Select placeholder="商品選択（任意）" allowClear style={{ width: '100%' }}
                          onChange={(val) => {
                            const p = products.find(p => p.id === val);
                            if (p) {
                              const items = form.getFieldValue('items');
                              items[name] = { ...items[name], product_name: p.product_name, sku: p.sku, unit_price: p.unit_price, unit: p.unit };
                              form.setFieldsValue({ items });
                            }
                          }}>
                          {products.map(p => <Option key={p.id} value={p.id}>{p.sku} - {p.product_name}</Option>)}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Form.Item {...rest} name={[name, 'product_name']} noStyle>
                        <Input placeholder="品名" />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Form.Item {...rest} name={[name, 'quantity']} noStyle>
                        <InputNumber placeholder="数量" style={{ width: '100%' }} min={1} />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item {...rest} name={[name, 'unit_price']} noStyle>
                        <InputNumber placeholder="単価" style={{ width: '100%' }} min={0} />
                      </Form.Item>
                    </Col>
                    <Col span={3}>
                      <Button danger size="small" onClick={() => remove(name)} block>✕</Button>
                    </Col>
                  </Row>
                ))}
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>明細行を追加</Button>
              </>
            )}
          </Form.List>
          <Form.Item name="notes" label="備考" style={{ marginTop: 16 }}>
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block style={{ background: '#1F3864' }}>
              発注書を作成
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* ステータス変更モーダル */}
      <Modal
        title={`ステータス変更: ${selectedOrder?.po_number}`}
        open={statusModalVisible}
        onCancel={() => setStatusModalVisible(false)}
        footer={null}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          {PO_STATUSES.map(s => (
            <Button key={s.value} block
              type={selectedOrder?.status === s.value ? 'primary' : 'default'}
              onClick={() => handleStatusUpdate(s.value)}
              style={selectedOrder?.status === s.value ? { background: '#1F3864' } : {}}>
              {s.label}
              {s.value === 'received' && <Tag color="green" style={{ marginLeft: 8 }}>在庫自動更新</Tag>}
            </Button>
          ))}
        </Space>
      </Modal>
    </div>
  );
};

export default PurchaseOrders;