import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Button, Upload, Select, Modal, Form, Input, InputNumber,
  Space, Typography, Tag, Progress, Descriptions, Divider, message, Tabs, Row, Col, Alert
} from 'antd';
import {
  UploadOutlined, PlusOutlined, DownloadOutlined, DeleteOutlined,
  EyeOutlined, FilePdfOutlined, CheckCircleOutlined, SyncOutlined,
} from '@ant-design/icons';
import { useDropzone } from 'react-dropzone';
import {
  listDocuments, uploadDocument, generateDocument, generateManual,
  deleteDocument, getDownloadUrl,
} from '../api';
import { Document } from '../types';
import { DocStatusTag, DocTypeTag } from '../components/StatusTag';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const DOC_TYPE_OPTIONS = [
  { value: 'po', label: 'P.O（発注書）' },
  { value: 'invoice', label: 'INVOICE（請求書）' },
  { value: 'packing_list', label: 'Packing List（梱包明細）' },
];

const Documents: React.FC = () => {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [docType, setDocType] = useState('po');
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [manualVisible, setManualVisible] = useState(false);
  const [editData, setEditData] = useState<any>(null);
  const [generating, setGenerating] = useState(false);
  const [form] = Form.useForm();

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const r = await listDocuments();
      setDocs(r.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

  const onDrop = useCallback(async (files: File[]) => {
    if (!files.length) return;
    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);
    setUploading(true);
    try {
      const r = await uploadDocument(formData);
      message.success('アップロード・OCR解析完了！内容を確認してください。');
      await fetchDocs();
      // 解析結果を表示
      const docRes = await import('../api').then(api => api.getDocument(r.data.document_id));
      setSelectedDoc(docRes.data);
      setEditData(docRes.data.extracted_data);
      setDetailVisible(true);
    } catch (e: any) {
      message.error('アップロードに失敗しました: ' + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  }, [docType]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpg', '.jpeg', '.png'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    multiple: false,
  });

  const handleGenerate = async () => {
    if (!selectedDoc) return;
    setGenerating(true);
    try {
      await generateDocument(selectedDoc.id, editData);
      message.success('書類を生成しました！');
      setDetailVisible(false);
      await fetchDocs();
    } catch (e: any) {
      message.error('生成に失敗しました: ' + (e.response?.data?.detail || e.message));
    } finally {
      setGenerating(false);
    }
  };

  const handleManualGenerate = async (values: any) => {
    setGenerating(true);
    try {
      const items = (values.items || []).map((item: any) => ({
        ...item,
        amount: (item.quantity || 0) * (item.unit_price || 0),
      }));
      await generateManual({
        doc_type: values.doc_type,
        data: { ...values, items },
      });
      message.success('書類を生成しました！');
      setManualVisible(false);
      form.resetFields();
      await fetchDocs();
    } catch (e: any) {
      message.error('生成に失敗しました');
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteDocument(id);
    message.success('削除しました');
    fetchDocs();
  };

  const columns = [
    { title: '書類種別', dataIndex: 'doc_type', key: 'doc_type', render: (v: string) => <DocTypeTag type={v} /> },
    { title: 'ファイル名', dataIndex: 'original_filename', key: 'original_filename',
      render: (v: string) => <Text ellipsis style={{ maxWidth: 200 }}>{v || '手動入力'}</Text> },
    { title: 'ステータス', dataIndex: 'status', key: 'status', render: (v: string) => <DocStatusTag status={v} /> },
    { title: '信頼度', dataIndex: 'confidence_score', key: 'confidence_score',
      render: (v: number) => v ? <Progress percent={Math.round(v * 100)} size="small" style={{ width: 80 }} /> : '-' },
    { title: '作成日時', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleString('ja-JP') : '-' },
    {
      title: '操作', key: 'actions',
      render: (_: any, record: Document) => (
        <Space>
          {record.has_generated && (
            <Button size="small" icon={<DownloadOutlined />} type="primary"
              href={getDownloadUrl(record.id)} target="_blank">PDF</Button>
          )}
          <Button size="small" icon={<DeleteOutlined />} danger
            onClick={() => handleDelete(record.id)}>削除</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ color: '#1F3864', marginBottom: 24 }}>📄 書類管理</Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="📤 書類アップロード（OCR自動解析）">
            <Space style={{ marginBottom: 16 }}>
              <Text>書類種別：</Text>
              <Select value={docType} onChange={setDocType} style={{ width: 200 }}>
                {DOC_TYPE_OPTIONS.map(o => <Option key={o.value} value={o.value}>{o.label}</Option>)}
              </Select>
            </Space>
            <div
              {...getRootProps()}
              style={{
                border: `2px dashed ${isDragActive ? '#1F3864' : '#d9d9d9'}`,
                borderRadius: 8,
                padding: '40px 20px',
                textAlign: 'center',
                background: isDragActive ? '#e8f0fe' : '#fafafa',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <input {...getInputProps()} />
              {uploading ? (
                <Space direction="vertical">
                  <SyncOutlined spin style={{ fontSize: 32, color: '#1F3864' }} />
                  <Text>OCR解析中...</Text>
                </Space>
              ) : (
                <Space direction="vertical">
                  <UploadOutlined style={{ fontSize: 32, color: '#1F3864' }} />
                  <Text strong>ここにファイルをドロップ、またはクリックして選択</Text>
                  <Text type="secondary">対応形式: PDF, JPG, PNG, DOCX, XLSX</Text>
                </Space>
              )}
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="✏️ 手動入力で書類作成">
            <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
              ファイルなしで直接データを入力して書類を生成できます
            </Text>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              block
              onClick={() => setManualVisible(true)}
              style={{ background: '#1F3864' }}
            >
              手動入力で書類作成
            </Button>
          </Card>
        </Col>
      </Row>

      <Card title={`書類一覧（${docs.length}件）`}>
        <Table
          dataSource={docs}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* OCR結果確認モーダル */}
      <Modal
        title="📋 OCR解析結果の確認・修正"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={700}
        footer={[
          <Button key="cancel" onClick={() => setDetailVisible(false)}>キャンセル</Button>,
          <Button key="generate" type="primary" loading={generating}
            icon={<FilePdfOutlined />} onClick={handleGenerate}
            style={{ background: '#1F3864' }}>
            この内容でPDF生成
          </Button>,
        ]}
      >
        {selectedDoc && editData && (
          <div>
            <Alert
              type="info"
              message={`OCR信頼度: ${Math.round((selectedDoc.confidence_score || 0) * 100)}% — 内容を確認・修正してからPDFを生成してください`}
              style={{ marginBottom: 16 }}
            />
            <Descriptions bordered size="small" column={2}>
              {Object.entries(editData).filter(([k]) => !['items', 'raw_text_preview', 'confidence_score', 'doc_type'].includes(k)).map(([k, v]) => (
                <Descriptions.Item key={k} label={k}>
                  <Input
                    defaultValue={String(v || '')}
                    onChange={e => setEditData((prev: any) => ({ ...prev, [k]: e.target.value }))}
                    size="small"
                  />
                </Descriptions.Item>
              ))}
            </Descriptions>
            {editData.items && (
              <>
                <Divider>商品明細</Divider>
                {editData.items.map((item: any, i: number) => (
                  <Card key={i} size="small" style={{ marginBottom: 8 }}>
                    <Row gutter={8}>
                      <Col span={10}>
                        <Input placeholder="品名" defaultValue={item.product_name}
                          onChange={e => {
                            const items = [...editData.items];
                            items[i] = { ...items[i], product_name: e.target.value };
                            setEditData((prev: any) => ({ ...prev, items }));
                          }} />
                      </Col>
                      <Col span={4}>
                        <InputNumber placeholder="数量" defaultValue={item.quantity} style={{ width: '100%' }}
                          onChange={v => {
                            const items = [...editData.items];
                            items[i] = { ...items[i], quantity: v, amount: (v || 0) * (items[i].unit_price || 0) };
                            setEditData((prev: any) => ({ ...prev, items }));
                          }} />
                      </Col>
                      <Col span={5}>
                        <InputNumber placeholder="単価" defaultValue={item.unit_price} style={{ width: '100%' }}
                          onChange={v => {
                            const items = [...editData.items];
                            items[i] = { ...items[i], unit_price: v, amount: (items[i].quantity || 0) * (v || 0) };
                            setEditData((prev: any) => ({ ...prev, items }));
                          }} />
                      </Col>
                      <Col span={5}>
                        <InputNumber placeholder="金額" value={item.amount} style={{ width: '100%' }} readOnly />
                      </Col>
                    </Row>
                  </Card>
                ))}
              </>
            )}
          </div>
        )}
      </Modal>

      {/* 手動入力モーダル */}
      <Modal
        title="✏️ 手動入力で書類作成"
        open={manualVisible}
        onCancel={() => setManualVisible(false)}
        width={700}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleManualGenerate}>
          <Form.Item name="doc_type" label="書類種別" initialValue="po" rules={[{ required: true }]}>
            <Select>
              {DOC_TYPE_OPTIONS.map(o => <Option key={o.value} value={o.value}>{o.label}</Option>)}
            </Select>
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="po_number" label="書類番号">
                <Input placeholder="PO-2026-0001" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="order_date" label="日付">
                <Input placeholder="2026-07-30" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="supplier" label="仕入先 / 請求先">
                <Input placeholder="取引先名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="currency" label="通貨" initialValue="JPY">
                <Select>
                  <Option value="JPY">JPY（円）</Option>
                  <Option value="USD">USD（ドル）</Option>
                  <Option value="EUR">EUR（ユーロ）</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="payment_terms" label="支払条件">
            <Input placeholder="T/T 30 days" />
          </Form.Item>
          <Divider>商品明細</Divider>
          <Form.List name="items" initialValue={[{ product_name: '', quantity: 1, unit_price: 0, unit: '個' }]}>
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...rest }) => (
                  <Row key={key} gutter={8} style={{ marginBottom: 8 }}>
                    <Col span={9}>
                      <Form.Item {...rest} name={[name, 'product_name']} noStyle>
                        <Input placeholder="品名" />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item {...rest} name={[name, 'quantity']} noStyle>
                        <InputNumber placeholder="数量" style={{ width: '100%' }} min={1} />
                      </Form.Item>
                    </Col>
                    <Col span={5}>
                      <Form.Item {...rest} name={[name, 'unit_price']} noStyle>
                        <InputNumber placeholder="単価" style={{ width: '100%' }} min={0} />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item {...rest} name={[name, 'unit']} noStyle>
                        <Input placeholder="単位" />
                      </Form.Item>
                    </Col>
                    <Col span={2}>
                      <Button danger size="small" onClick={() => remove(name)}>✕</Button>
                    </Col>
                  </Row>
                ))}
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  明細行を追加
                </Button>
              </>
            )}
          </Form.List>
          <Form.Item name="notes" label="備考" style={{ marginTop: 16 }}>
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={generating}
              icon={<FilePdfOutlined />} block style={{ background: '#1F3864' }}>
              PDF書類を生成
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Documents;