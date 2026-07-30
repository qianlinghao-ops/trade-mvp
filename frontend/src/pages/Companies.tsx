import React, { useEffect, useState } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select,
  Space, Typography, message, Row, Col, Tabs, Tag,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, GlobalOutlined } from '@ant-design/icons';
import { listCompanies, createCompany, updateCompany, deleteCompany } from '../api';
import { Company } from '../types';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const Companies: React.FC = () => {
  const [suppliers, setSuppliers] = useState<Company[]>([]);
  const [customers, setCustomers] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [defaultType, setDefaultType] = useState<'supplier' | 'customer'>('supplier');
  const [form] = Form.useForm();

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [supRes, cusRes] = await Promise.all([
        listCompanies({ company_type: 'supplier' }),
        listCompanies({ company_type: 'customer' }),
      ]);
      setSuppliers(supRes.data.items);
      setCustomers(cusRes.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleOpenCreate = (type: 'supplier' | 'customer') => {
    setEditingCompany(null);
    setDefaultType(type);
    form.resetFields();
    form.setFieldsValue({ company_type: type });
    setModalVisible(true);
  };

  const handleOpenEdit = (company: Company) => {
    setEditingCompany(company);
    form.setFieldsValue(company);
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingCompany) {
        await updateCompany(editingCompany.id, values);
        message.success('取引先を更新しました');
      } else {
        await createCompany(values);
        message.success('取引先を登録しました');
      }
      setModalVisible(false);
      form.resetFields();
      fetchAll();
    } catch (e) {
      message.error('保存に失敗しました');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteCompany(id);
      message.success('削除しました');
      fetchAll();
    } catch (e) {
      message.error('削除に失敗しました');
    }
  };

  const columns = [
    { title: '会社名', dataIndex: 'company_name', key: 'company_name',
      render: (v: string) => <Text strong>{v}</Text> },
    { title: '国', dataIndex: 'country', key: 'country',
      render: (v: string) => v ? <Space><GlobalOutlined />{v}</Space> : '-' },
    { title: '担当者', dataIndex: 'contact_name', key: 'contact_name',
      render: (v: string) => v || '-' },
    { title: 'メール', dataIndex: 'contact_email', key: 'contact_email',
      render: (v: string) => v ? <a href={`mailto:${v}`}>{v}</a> : '-' },
    { title: '電話', dataIndex: 'contact_phone', key: 'contact_phone',
      render: (v: string) => v || '-' },
    {
      title: '操作', key: 'actions',
      render: (_: any, record: Company) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleOpenEdit(record)}>編集</Button>
          <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>削除</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ color: '#1F3864', marginBottom: 24 }}>🏢 取引先管理</Title>

      <Tabs defaultActiveKey="supplier" onChange={k => setDefaultType(k as any)}>
        <TabPane tab={`仕入先（${suppliers.length}社）`} key="supplier">
          <Card extra={
            <Button type="primary" icon={<PlusOutlined />}
              onClick={() => handleOpenCreate('supplier')}
              style={{ background: '#1F3864' }}>
              仕入先を追加
            </Button>
          }>
            <Table dataSource={suppliers} columns={columns} rowKey="id" loading={loading} pagination={false} />
          </Card>
        </TabPane>
        <TabPane tab={`得意先（${customers.length}社）`} key="customer">
          <Card extra={
            <Button type="primary" icon={<PlusOutlined />}
              onClick={() => handleOpenCreate('customer')}
              style={{ background: '#1F3864' }}>
              得意先を追加
            </Button>
          }>
            <Table dataSource={customers} columns={columns} rowKey="id" loading={loading} pagination={false} />
          </Card>
        </TabPane>
      </Tabs>

      <Modal
        title={editingCompany ? '取引先を編集' : '取引先を登録'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={16}>
              <Form.Item name="company_name" label="会社名" rules={[{ required: true }]}>
                <Input placeholder="株式会社〇〇" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="company_type" label="区分" initialValue={defaultType} rules={[{ required: true }]}>
                <Select>
                  <Option value="supplier">仕入先</Option>
                  <Option value="customer">得意先</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="country" label="国">
                <Input placeholder="日本" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="contact_name" label="担当者名">
                <Input placeholder="山田 太郎" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="contact_email" label="メールアドレス">
                <Input placeholder="contact@example.com" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="contact_phone" label="電話番号">
                <Input placeholder="+81-3-1234-5678" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="address" label="住所">
            <Input.TextArea rows={2} placeholder="東京都千代田区..." />
          </Form.Item>
          <Form.Item name="notes" label="備考">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block style={{ background: '#1F3864' }}>
              {editingCompany ? '更新する' : '登録する'}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Companies;