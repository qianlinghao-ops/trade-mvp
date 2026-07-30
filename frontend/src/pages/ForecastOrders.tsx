import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Button, Modal, Form, Select, Upload, Space, Typography,
  message, Row, Col, Tag, Tabs, InputNumber, Alert, Divider, Tooltip,
  Statistic, Progress,
} from 'antd';
import {
  UploadOutlined, PlusOutlined, CheckCircleOutlined, CalculatorOutlined,
  FileTextOutlined, BellOutlined, InfoCircleOutlined, ArrowRightOutlined,
} from '@ant-design/icons';
import { useDropzone } from 'react-dropzone';
import client from '../api/client';
import { formatAmount } from '../components/StatusTag';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const ForecastOrders: React.FC = () => {
  const [forecasts, setForecasts] = useState<any[]>([]);
  const [proposals, setProposals] = useState<any[]>([]);
  const [safetyStocks, setSafetyStocks] = useState<any[]>([]);
  const [leadTimes, setLeadTimes] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadVisible, setUploadVisible] = useState(false);
  const [calcVisible, setCalcVisible] = useState(false);
  const [proposalDetailVisible, setProposalDetailVisible] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState<any>(null);
  const [calcResult, setCalcResult] = useState<any>(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [approving, setApproving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadForm] = Form.useForm();
  const [calcForm] = Form.useForm();
  const [notifSettings, setNotifSettings] = useState<any>(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [fRes, pRes, ssRes, ltRes, cusRes, supRes, nsRes] = await Promise.all([
        client.get('/forecast'),
        client.get('/forecast/proposals/list'),
        client.get('/forecast/safety-stocks/list'),
        client.get('/forecast/lead-times/list'),
        client.get('/companies?company_type=customer'),
        client.get('/companies?company_type=supplier'),
        client.get('/notifications/settings'),
      ]);
      setForecasts(fRes.data.items);
      setProposals(pRes.data.items);
      setSafetyStocks(ssRes.data.items);
      setLeadTimes(ltRes.data.items);
      setCustomers(cusRes.data.items);
      setSuppliers(supRes.data.items);
      setNotifSettings(nsRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  // ─── 内示アップロード ───────────────────────────────────────────────
  const onDrop = useCallback(async (files: File[]) => {
    if (!files.length) return;
    const values = uploadForm.getFieldsValue();
    if (!values.customer_id || !values.forecast_month) {
      message.warning('得意先と内示月を先に選択してください');
      return;
    }
    const formData = new FormData();
    formData.append('file', files[0]);
    formData.append('customer_id', values.customer_id);
    formData.append('forecast_month', values.forecast_month);
    setUploading(true);
    try {
      await client.post('/forecast/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      message.success('内示PDFを取り込みました！');
      setUploadVisible(false);
      uploadForm.resetFields();
      fetchAll();
    } catch (e: any) {
      message.error('取り込みに失敗しました: ' + (e.response?.data?.detail || e.message));
    } finally {
      setUploading(false);
    }
  }, [uploadForm]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'application/pdf': ['.pdf'] }, multiple: false });

  // ─── 自動発注計算 ───────────────────────────────────────────────────
  const handleCalculate = async (values: any) => {
    setCalcLoading(true);
    try {
      const res = await client.post('/forecast/proposals/calculate', {
        supplier_id: values.supplier_id,
        target_month: values.target_month,
      });
      setCalcResult(res.data);
    } catch (e: any) {
      message.error('計算に失敗しました: ' + (e.response?.data?.detail || e.message));
    } finally {
      setCalcLoading(false);
    }
  };

  const handleSaveProposal = async () => {
    if (!calcResult) return;
    try {
      await client.post('/forecast/proposals', {
        supplier_id: calcForm.getFieldValue('supplier_id'),
        target_month: calcForm.getFieldValue('target_month'),
        items: calcResult.items,
      });
      message.success('発注提案を保存しました');
      setCalcVisible(false);
      setCalcResult(null);
      calcForm.resetFields();
      fetchAll();
    } catch (e) {
      message.error('保存に失敗しました');
    }
  };

  const handleApprove = async (proposalId: string) => {
    setApproving(true);
    try {
      const res = await client.put(`/forecast/proposals/${proposalId}/approve`);
      message.success(`✅ ${res.data.po_number} を自動作成しました！`);
      setProposalDetailVisible(false);
      fetchAll();
    } catch (e: any) {
      message.error('承認に失敗しました: ' + (e.response?.data?.detail || e.message));
    } finally {
      setApproving(false);
    }
  };

  const handleSendAlert = async () => {
    try {
      const res = await client.post('/notifications/send-low-stock-alert');
      message.success(res.data.message);
    } catch (e) {
      message.error('送信に失敗しました');
    }
  };

  // ─── 安全在庫更新 ───────────────────────────────────────────────────
  const handleSafetyStockUpdate = async (productId: string, qty: number) => {
    try {
      await client.put(`/forecast/safety-stocks/${productId}`, { safety_stock_qty: qty });
      message.success('安全在庫を更新しました');
      fetchAll();
    } catch (e) {
      message.error('更新に失敗しました');
    }
  };

  // ─── 月ラベル生成 ───────────────────────────────────────────────────
  const getMonthOptions = () => {
    const options = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() + i, 1);
      const label = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      options.push({ value: label, label });
    }
    return options;
  };

  const [forecastDetail, setForecastDetail] = useState<any>(null);
  const [forecastDetailVisible, setForecastDetailVisible] = useState(false);

  const proposalStatusMap: Record<string, { label: string; color: string }> = {
    draft: { label: '下書き', color: 'default' },
    approved: { label: '承認済', color: 'green' },
    ordered: { label: '発注済', color: 'blue' },
    rejected: { label: '却下', color: 'red' },
  };

  const forecastStatusMap: Record<string, { label: string; color: string }> = {
    uploaded: { label: 'アップロード済', color: 'blue' },
    processing: { label: '処理中', color: 'processing' },
    confirmed: { label: '確認済', color: 'green' },
    error: { label: 'エラー', color: 'red' },
  };

  return (
    <div>
      <Title level={4} style={{ color: '#1F3864', marginBottom: 24 }}>
        📊 内示管理・自動発注
      </Title>

      {/* メール設定警告 */}
      {notifSettings && !notifSettings.smtp_configured && (
        <Alert
          type="info"
          message="メール通知を有効にするには、Railwayの環境変数にSMTP設定を追加してください"
          description="Settings → Variables → SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO を設定"
          style={{ marginBottom: 16 }}
          showIcon
          action={<Button size="small" onClick={handleSendAlert}>アラートテスト</Button>}
        />
      )}

      <Tabs defaultActiveKey="forecast">
        {/* ─── 内示管理タブ ─── */}
        <TabPane tab="📄 内示管理" key="forecast">
          <Card
            title={`内示一覧（${forecasts.length}件）`}
            extra={
              <Button type="primary" icon={<UploadOutlined />}
                onClick={() => setUploadVisible(true)}
                style={{ background: '#1F3864' }}>
                内示PDFを取り込む
              </Button>
            }
          >
            <Table
              dataSource={forecasts}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
              columns={[
                { title: '得意先', dataIndex: 'customer_name', key: 'customer_name' },
                { title: '内示月', dataIndex: 'forecast_month', key: 'forecast_month' },
                { title: 'ファイル名', dataIndex: 'original_filename', key: 'original_filename',
                  render: (v: string) => <Text ellipsis style={{ maxWidth: 200 }}>{v}</Text> },
                { title: '明細数', dataIndex: 'items_count', key: 'items_count',
                  render: (v: number) => `${v}件` },
                { title: 'ステータス', dataIndex: 'status', key: 'status',
                  render: (v: string) => {
                    const s = forecastStatusMap[v] || { label: v, color: 'default' };
                    return <Tag color={s.color}>{s.label}</Tag>;
                  }},
                { title: '取込日時', dataIndex: 'created_at', key: 'created_at',
                  render: (v: string) => v ? new Date(v).toLocaleString('ja-JP') : '-' },
                { title: '操作', key: 'actions',
                  render: (_: any, record: any) => (
                    <Button size="small" icon={<FileTextOutlined />}
                      onClick={async () => {
                        const res = await client.get(`/forecast/${record.id}`);
                        setForecastDetail(res.data);
                        setForecastDetailVisible(true);
                      }}>
                      内示数量を確認
                    </Button>
                  )
                },
              ]}
            />
          </Card>
        </TabPane>

        {/* ─── 自動発注提案タブ ─── */}
        <TabPane tab="🤖 自動発注提案" key="proposals">
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} lg={16}>
              <Card title="💡 自動発注計算の仕組み" size="small" style={{ background: '#e8f0fe', border: 'none' }}>
                <div style={{ fontSize: 16, fontWeight: 'bold', color: '#1F3864', marginBottom: 8 }}>
                  発注数量 = 内示数量 − 現在庫数量 − 発注残数量 + 安全在庫係数
                </div>
                <Row gutter={16}>
                  {[
                    { label: '内示数量', desc: '得意先からのPDF内示', color: '#1F3864' },
                    { label: '現在庫数量', desc: 'リアルタイム在庫', color: '#52c41a' },
                    { label: '発注残数量', desc: '未入荷の発注合計', color: '#fa8c16' },
                    { label: '安全在庫係数', desc: '商品別バッファ', color: '#722ed1' },
                  ].map((item, i) => (
                    <Col span={6} key={i}>
                      <div style={{ textAlign: 'center', padding: '8px 4px' }}>
                        <div style={{ color: item.color, fontWeight: 'bold', fontSize: 13 }}>{item.label}</div>
                        <div style={{ color: '#888', fontSize: 11 }}>{item.desc}</div>
                      </div>
                    </Col>
                  ))}
                </Row>
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card size="small">
                <Button type="primary" icon={<CalculatorOutlined />} block
                  onClick={() => setCalcVisible(true)}
                  style={{ background: '#1F3864', marginBottom: 8 }}>
                  発注数量を自動計算
                </Button>
                <Button icon={<BellOutlined />} block onClick={handleSendAlert}>
                  在庫アラートメール送信
                </Button>
              </Card>
            </Col>
          </Row>

          <Card title={`発注提案一覧（${proposals.length}件）`}>
            <Table
              dataSource={proposals}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
              columns={[
                { title: '仕入先', dataIndex: 'supplier_name', key: 'supplier_name' },
                { title: '対象月', dataIndex: 'target_month', key: 'target_month' },
                { title: 'ステータス', dataIndex: 'status', key: 'status',
                  render: (v: string) => {
                    const s = proposalStatusMap[v] || { label: v, color: 'default' };
                    return <Tag color={s.color}>{s.label}</Tag>;
                  }},
                { title: '明細数', dataIndex: 'items_count', key: 'items_count',
                  render: (v: number) => `${v}件` },
                { title: '合計金額', dataIndex: 'total_amount', key: 'total_amount',
                  render: (v: number) => <Text strong>{formatAmount(v, 'JPY')}</Text> },
                { title: '作成日', dataIndex: 'proposal_date', key: 'proposal_date' },
                {
                  title: '操作', key: 'actions',
                  render: (_: any, record: any) => (
                    <Space>
                      <Button size="small" icon={<FileTextOutlined />}
                        onClick={async () => {
                          const res = await client.get(`/forecast/proposals/${record.id}`);
                          setSelectedProposal(res.data);
                          setProposalDetailVisible(true);
                        }}>
                        詳細
                      </Button>
                      {record.status === 'draft' && (
                        <Button size="small" type="primary" icon={<CheckCircleOutlined />}
                          onClick={() => handleApprove(record.id)}
                          style={{ background: '#52c41a', borderColor: '#52c41a' }}>
                          承認・発注書作成
                        </Button>
                      )}
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        </TabPane>

        {/* ─── 安全在庫設定タブ ─── */}
        <TabPane tab="🛡️ 安全在庫設定" key="safety">
          <Card title="商品別安全在庫係数" extra={
            <Tooltip title="安全在庫係数は発注計算時に加算されます。欠品リスクに応じて設定してください。">
              <InfoCircleOutlined style={{ color: '#1F3864' }} />
            </Tooltip>
          }>
            <Table
              dataSource={safetyStocks}
              rowKey="product_id"
              loading={loading}
              pagination={{ pageSize: 20 }}
              columns={[
                { title: 'SKU', dataIndex: 'sku', key: 'sku',
                  render: (v: string) => <Text code>{v}</Text> },
                { title: '商品名', dataIndex: 'product_name', key: 'product_name' },
                {
                  title: '安全在庫係数', dataIndex: 'safety_stock_qty', key: 'safety_stock_qty',
                  render: (v: number, record: any) => (
                    <Space>
                      <InputNumber
                        defaultValue={v}
                        min={0}
                        style={{ width: 100 }}
                        onBlur={(e) => {
                          const newVal = parseInt(e.target.value) || 0;
                          if (newVal !== v) {
                            handleSafetyStockUpdate(record.product_id, newVal);
                          }
                        }}
                      />
                      <Text type="secondary">個</Text>
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        </TabPane>

        {/* ─── リードタイム設定タブ ─── */}
        <TabPane tab="⏱️ リードタイム設定" key="leadtime">
          <Card
            title="仕入先別リードタイム（日数）"
            extra={
              <Button type="primary" icon={<PlusOutlined />}
                style={{ background: '#1F3864' }}
                onClick={async () => {
                  const supplier_id = suppliers[0]?.id;
                  if (!supplier_id) return;
                  await client.post('/forecast/lead-times', { supplier_id, lead_time_days: 30 });
                  message.success('追加しました');
                  fetchAll();
                }}>
                追加
              </Button>
            }
          >
            <Table
              dataSource={leadTimes}
              rowKey="id"
              loading={loading}
              pagination={false}
              columns={[
                { title: '仕入先', dataIndex: 'supplier_name', key: 'supplier_name' },
                { title: '商品', dataIndex: 'product_name', key: 'product_name' },
                {
                  title: 'リードタイム（日）', dataIndex: 'lead_time_days', key: 'lead_time_days',
                  render: (v: number, record: any) => (
                    <InputNumber
                      defaultValue={v}
                      min={1}
                      max={365}
                      style={{ width: 100 }}
                      onBlur={async (e) => {
                        const newVal = parseInt(e.target.value) || 30;
                        if (newVal !== v) {
                          await client.put(`/forecast/lead-times/${record.id}`, { lead_time_days: newVal });
                          message.success('更新しました');
                          fetchAll();
                        }
                      }}
                    />
                  ),
                },
                { title: '備考', dataIndex: 'notes', key: 'notes', render: (v: string) => v || '-' },
              ]}
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* ─── 内示詳細モーダル ─── */}
      <Modal
        title={`📊 内示数量詳細: ${forecastDetail?.customer_name} (${forecastDetail?.forecast_month})`}
        open={forecastDetailVisible}
        onCancel={() => setForecastDetailVisible(false)}
        width={1000}
        footer={<Button onClick={() => setForecastDetailVisible(false)}>閉じる</Button>}
      >
        {forecastDetail && (
          <div>
            <Alert
              type="info"
              message={`抽出件数: ${forecastDetail.items?.length}件 | 月別内示数量（6ヶ月分）`}
              style={{ marginBottom: 16 }}
              showIcon
            />
            <Table
              dataSource={forecastDetail.items}
              rowKey="id"
              size="small"
              scroll={{ x: 900 }}
              pagination={{ pageSize: 20 }}
              columns={[
                { title: '部番', dataIndex: 'sku', key: 'sku', fixed: 'left' as const, width: 200,
                  render: (v: string) => <Text code style={{ fontSize: 11 }}>{v}</Text> },
                { title: '部品名称', dataIndex: 'product_name', key: 'product_name', width: 180,
                  render: (v: string) => <Text ellipsis style={{ maxWidth: 160 }}>{v}</Text> },
                ...(forecastDetail.items?.[0]?.months?.map((m: any, i: number) => ({
                  title: m.label || `月${i+1}`,
                  key: `month_${i}`,
                  width: 90,
                  align: 'right' as const,
                  render: (_: any, record: any) => {
                    const qty = record.months?.[i]?.qty || 0;
                    return <Text strong style={{ color: qty > 0 ? '#1F3864' : '#ccc' }}>{qty.toLocaleString()}</Text>;
                  }
                })) || []),
                { title: '商品マスタ', key: 'product_id', width: 100,
                  render: (_: any, record: any) => record.product_id
                    ? <Tag color="green">紐付済</Tag>
                    : <Tag color="orange">未紐付</Tag>
                },
              ]}
            />
            {forecastDetail.items?.some((i: any) => !i.product_id) && (
              <Alert
                type="warning"
                message="「未紐付」の部番は商品マスタに登録されていません。商品マスタに部番を登録すると自動発注計算に使用できます。"
                style={{ marginTop: 16 }}
                showIcon
              />
            )}
          </div>
        )}
      </Modal>

      {/* ─── 内示アップロードモーダル ─── */}
      <Modal
        title="📄 内示PDFを取り込む"
        open={uploadVisible}
        onCancel={() => setUploadVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={uploadForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="customer_id" label="得意先" rules={[{ required: true }]}>
                <Select placeholder="得意先を選択">
                  {customers.map(c => <Option key={c.id} value={c.id}>{c.company_name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="forecast_month" label="内示月" rules={[{ required: true }]}>
                <Select placeholder="内示月を選択">
                  {getMonthOptions().map(o => <Option key={o.value} value={o.value}>{o.label}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <div
            {...getRootProps()}
            style={{
              border: `2px dashed ${isDragActive ? '#1F3864' : '#d9d9d9'}`,
              borderRadius: 8, padding: '40px 20px', textAlign: 'center',
              background: isDragActive ? '#e8f0fe' : '#fafafa', cursor: 'pointer',
            }}
          >
            <input {...getInputProps()} />
            {uploading ? (
              <Space direction="vertical">
                <Text>PDF解析中...</Text>
              </Space>
            ) : (
              <Space direction="vertical">
                <UploadOutlined style={{ fontSize: 32, color: '#1F3864' }} />
                <Text strong>内示PDFをドロップ、またはクリックして選択</Text>
                <Text type="secondary">PDF形式のみ対応</Text>
              </Space>
            )}
          </div>
          <Alert
            type="info"
            message="PDFから自動抽出できない場合は、取り込み後に手動で数量を修正できます"
            style={{ marginTop: 16 }}
            showIcon
          />
        </Form>
      </Modal>

      {/* ─── 自動計算モーダル ─── */}
      <Modal
        title="🤖 発注数量を自動計算"
        open={calcVisible}
        onCancel={() => { setCalcVisible(false); setCalcResult(null); calcForm.resetFields(); }}
        width={900}
        footer={calcResult ? [
          <Button key="cancel" onClick={() => { setCalcVisible(false); setCalcResult(null); calcForm.resetFields(); }}>
            キャンセル
          </Button>,
          <Button key="save" type="primary" onClick={handleSaveProposal}
            style={{ background: '#1F3864' }}>
            発注提案として保存
          </Button>,
        ] : null}
      >
        <Form form={calcForm} layout="vertical" onFinish={handleCalculate}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="supplier_id" label="仕入先" rules={[{ required: true }]}>
                <Select placeholder="仕入先を選択">
                  {suppliers.map(s => <Option key={s.id} value={s.id}>{s.company_name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="target_month" label="対象月" rules={[{ required: true }]}>
                <Select placeholder="対象月を選択">
                  {getMonthOptions().map(o => <Option key={o.value} value={o.value}>{o.label}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          {!calcResult && (
            <Button type="primary" htmlType="submit" loading={calcLoading} block
              icon={<CalculatorOutlined />} style={{ background: '#1F3864' }}>
              計算実行
            </Button>
          )}
        </Form>

        {calcResult && (
          <div style={{ marginTop: 16 }}>
            <Alert
              type={calcResult.items.length > 0 ? "success" : "warning"}
              message={`計算完了: ${calcResult.items.length}件 / 合計 ${formatAmount(calcResult.total_amount, 'JPY')}`}
              description={
                calcResult.items.length === 0
                  ? "内示データが見つかりません。先に内示PDFを取り込んでください。"
                  : `計算式: ${calcResult.formula_note} | 商品マスタ未登録の部番は単価0円で表示されます`
              }
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Table
              dataSource={calcResult.items}
              rowKey="product_id"
              size="small"
              pagination={false}
              columns={[
                { title: '部番/SKU', dataIndex: 'sku', key: 'sku', width: 200,
                  render: (v: string) => <Text code style={{ fontSize: 11 }}>{v}</Text> },
                { title: '部品名称', dataIndex: 'product_name', key: 'product_name', width: 180,
                  render: (v: string) => <Text ellipsis style={{ maxWidth: 160 }}>{v}</Text> },
                { title: '内示数量', dataIndex: 'forecast_qty', key: 'forecast_qty',
                  render: (v: number) => <Text strong style={{ color: '#1F3864' }}>{v.toLocaleString()}</Text> },
                { title: '現在庫', dataIndex: 'current_stock', key: 'current_stock',
                  render: (v: number) => <Text style={{ color: '#52c41a' }}>-{v}</Text> },
                { title: '発注残', dataIndex: 'pending_order_qty', key: 'pending_order_qty',
                  render: (v: number) => <Text style={{ color: '#fa8c16' }}>-{v}</Text> },
                { title: '安全在庫', dataIndex: 'safety_stock_qty', key: 'safety_stock_qty',
                  render: (v: number) => <Text style={{ color: '#722ed1' }}>+{v}</Text> },
                { title: '発注数量', dataIndex: 'proposed_qty', key: 'proposed_qty',
                  render: (v: number) => (
                    <Text strong style={{ color: v > 0 ? '#1F3864' : '#999', fontSize: 16 }}>{v.toLocaleString()}</Text>
                  ) },
                { title: '金額', dataIndex: 'amount', key: 'amount',
                  render: (v: number) => v > 0 ? formatAmount(v, 'JPY') : '-' },
                { title: '商品マスタ', dataIndex: 'linked', key: 'linked',
                  render: (v: boolean) => v
                    ? <Tag color="green">紐付済</Tag>
                    : <Tag color="orange">未登録</Tag> },
              ]}
            />
          </div>
        )}
      </Modal>

      {/* ─── 発注提案詳細モーダル ─── */}
      <Modal
        title={`📋 発注提案詳細: ${selectedProposal?.target_month}`}
        open={proposalDetailVisible}
        onCancel={() => setProposalDetailVisible(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setProposalDetailVisible(false)}>閉じる</Button>,
          selectedProposal?.status === 'draft' && (
            <Button key="approve" type="primary" loading={approving}
              icon={<CheckCircleOutlined />}
              onClick={() => handleApprove(selectedProposal.id)}
              style={{ background: '#52c41a', borderColor: '#52c41a' }}>
              承認して発注書を自動作成
            </Button>
          ),
        ]}
      >
        {selectedProposal && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}><Statistic title="仕入先" value={selectedProposal.supplier_name} /></Col>
              <Col span={6}><Statistic title="対象月" value={selectedProposal.target_month} /></Col>
              <Col span={6}><Statistic title="合計金額" value={formatAmount(selectedProposal.total_amount, 'JPY')} /></Col>
              <Col span={6}><Statistic title="明細数" value={`${selectedProposal.items?.length}件`} /></Col>
            </Row>
            <Alert
              type="info"
              message="計算式: 発注数量 = 内示数量 − 現在庫数量 − 発注残数量 + 安全在庫係数"
              style={{ marginBottom: 16 }}
              showIcon
            />
            <Table
              dataSource={selectedProposal.items}
              rowKey="id"
              size="small"
              pagination={false}
              columns={[
                { title: 'SKU', dataIndex: 'sku', key: 'sku', render: (v: string) => <Text code>{v}</Text> },
                { title: '商品名', dataIndex: 'product_name', key: 'product_name' },
                { title: '計算内訳', dataIndex: 'formula', key: 'formula',
                  render: (v: string) => <Text type="secondary" style={{ fontSize: 11 }}>{v}</Text> },
                { title: '発注数量', dataIndex: 'proposed_qty', key: 'proposed_qty',
                  render: (v: number) => <Text strong style={{ color: '#1F3864', fontSize: 16 }}>{v}</Text> },
                { title: '単価', dataIndex: 'unit_price', key: 'unit_price',
                  render: (v: number) => formatAmount(v, 'JPY') },
                { title: '金額', dataIndex: 'amount', key: 'amount',
                  render: (v: number) => <Text strong>{formatAmount(v, 'JPY')}</Text> },
              ]}
            />
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ForecastOrders;