import React, { useEffect, useState } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, InputNumber, Select,
  Space, Typography, message, Row, Col, Tag, Progress,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, WarningOutlined } from '@ant-design/icons';
import { listProducts, createProduct, updateProduct, deleteProduct, listCompanies } from '../api';
import { Product, Company } from '../types';
import { formatAmount } from '../components/StatusTag';

const { Title, Text } = Typography;
const { Option } = Select;

const Products: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [suppliers, setSuppliers] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [prodRes, supRes] = await Promise.all([
        listProducts(),
        listCompanies({ company_type: 'supplier' }),
      ]);
      setProducts(prodRes.data.items);
      setSuppliers(supRes.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleOpenCreate = () => {
    setEditingProduct(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleOpenEdit = (product: Product) => {
    setEditingProduct(product);
    form.setFieldsValue(product);
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingProduct) {
        await updateProduct(editingProduct.id, values);
        message.success('商品を更新しました');
      } else {
        await createProduct(values);
        message.success('商品を登録しました');
      }
      setModalVisible(false);
      form.resetFields();
      fetchAll();
    } catch (e: any) {
      message.error('保存に失敗しました: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteProduct(id);
      message.success('削除しました');
      fetchAll();
    } catch (e) {
      message.error('削除に失敗しました');
    }
  };

  const filtered = products.filter(p =>
    p.product_name.includes(searchText) || p.sku.includes(searchText)
  );

  const columns = [
    { title: 'SKU', dataIndex: 'sku', key: 'sku',
      render: (v: string) => <Text code>{v}</Text> },
    { title: '商品名', dataIndex: 'product_name', key: 'product_name',
      render: (v: string, r: Product) => (
        <Space direction="vertical" size={0}>
          <Text strong>{v}</Text>
          {r.product_name_en && <Text type="secondary" style={{ fontSize: 12 }}>{r.product_name_en}</Text>}
        </Space>
      )
    },
    { title: 'HSコード', dataIndex: 'hs_code', key: 'hs_code',
      render: (v: string) => v ? <Text code>{v}</Text> : '-' },
    { title: '単価', dataIndex: 'unit_price', key: 'unit_price',
      render: (v: number, r: Product) => <Text strong>{formatAmount(v, r.currency)}</Text> },
    { title: '単位', dataIndex: 'unit', key: 'unit' },
    {
      title: '在庫状況', key: 'stock',
      render: (_: any, r: Product) => (
        <Space direction="vertical" size={0} style={{ width: 120 }}>
          <Space>
            <Text strong style={{ color: r.is_low_stock ? '#ff4d4f' : '#52c41a' }}>
              {r.current_stock}
            </Text>
            <Text type="secondary">/ 最低{r.min_stock_qty}</Text>
            {r.is_low_stock && <WarningOutlined style={{ color: '#ff4d4f' }} />}
          </Space>
          <Progress
            percent={Math.min(100, Math.round((r.current_stock / Math.max(r.min_stock_qty, 1)) * 100))}
            size="small"
            status={r.is_low_stock ? 'exception' : 'normal'}
            showInfo={false}
          />
        </Space>
      )
    },
    {
      title: '操作', key: 'actions',
      render: (_: any, record: Product) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenEdit(record)}>編集</Button>
          <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>削除</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ color: '#1F3864', marginBottom: 24 }}>📋 商品マスタ</Title>

      <Card
        title={`商品一覧（${filtered.length}件）`}
        extra={
          <Space>
            <Input.Search
              placeholder="SKU・商品名で検索"
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              style={{ width: 200 }}
              allowClear
            />
            <Button type="primary" icon={<PlusOutlined />}
              onClick={handleOpenCreate}
              style={{ background: '#1F3864' }}>
              商品を追加
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editingProduct ? '商品を編集' : '商品を登録'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={640}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={10}>
              <Form.Item name="sku" label="SKUコード" rules={[{ required: true }]}>
                <Input placeholder="SKU-001" />
              </Form.Item>
            </Col>
            <Col span={14}>
              <Form.Item name="product_name" label="商品名（日本語）" rules={[{ required: true }]}>
                <Input placeholder="電子部品A" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="product_name_en" label="商品名（英語）">
            <Input placeholder="Electronic Component A" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="hs_code" label="HSコード">
                <Input placeholder="8532.21" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="supplier_id" label="主仕入先">
                <Select allowClear placeholder="仕入先を選択">
                  {suppliers.map(s => <Option key={s.id} value={s.id}>{s.company_name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="unit_price" label="単価" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="currency" label="通貨" initialValue="JPY">
                <Select>
                  <Option value="JPY">JPY</Option>
                  <Option value="USD">USD</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="unit" label="単位" initialValue="個">
                <Input placeholder="個 / 枚 / 本" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="min_stock_qty" label="最低在庫数（アラート閾値）" initialValue={0}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            {!editingProduct && (
              <Col span={12}>
                <Form.Item name="initial_stock" label="初期在庫数" initialValue={0}>
                  <InputNumber min={0} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            )}
          </Row>
          <Form.Item name="description" label="説明">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block style={{ background: '#1F3864' }}>
              {editingProduct ? '更新する' : '登録する'}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Products;