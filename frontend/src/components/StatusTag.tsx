import React from 'react';
import { Tag } from 'antd';

const PO_STATUS_MAP: Record<string, { label: string; color: string }> = {
  draft:      { label: '下書き',   color: 'default' },
  ordered:    { label: '発注済',   color: 'blue' },
  confirmed:  { label: '確認済',   color: 'cyan' },
  in_transit: { label: '輸送中',   color: 'geekblue' },
  received:   { label: '入荷済',   color: 'green' },
  completed:  { label: '完了',     color: 'success' },
  cancelled:  { label: 'キャンセル', color: 'error' },
};

const SO_STATUS_MAP: Record<string, { label: string; color: string }> = {
  draft:     { label: '下書き',   color: 'default' },
  received:  { label: '受注',     color: 'blue' },
  confirmed: { label: '確認済',   color: 'cyan' },
  preparing: { label: '出荷準備', color: 'orange' },
  shipped:   { label: '出荷済',   color: 'geekblue' },
  completed: { label: '完了',     color: 'success' },
  cancelled: { label: 'キャンセル', color: 'error' },
};

const DOC_STATUS_MAP: Record<string, { label: string; color: string }> = {
  uploading:  { label: 'アップロード中', color: 'processing' },
  processing: { label: 'OCR処理中',     color: 'processing' },
  review:     { label: '確認待ち',       color: 'warning' },
  completed:  { label: '完了',           color: 'success' },
  error:      { label: 'エラー',         color: 'error' },
};

const DOC_TYPE_MAP: Record<string, string> = {
  po:           'P.O（発注書）',
  invoice:      'INVOICE（請求書）',
  packing_list: 'Packing List',
  bl:           'B/L（船荷証券）',
  coo:          '原産地証明',
  customs:      '通関書類',
  other:        'その他',
};

export const POStatusTag: React.FC<{ status: string }> = ({ status }) => {
  const s = PO_STATUS_MAP[status] || { label: status, color: 'default' };
  return <Tag color={s.color}>{s.label}</Tag>;
};

export const SOStatusTag: React.FC<{ status: string }> = ({ status }) => {
  const s = SO_STATUS_MAP[status] || { label: status, color: 'default' };
  return <Tag color={s.color}>{s.label}</Tag>;
};

export const DocStatusTag: React.FC<{ status: string }> = ({ status }) => {
  const s = DOC_STATUS_MAP[status] || { label: status, color: 'default' };
  return <Tag color={s.color}>{s.label}</Tag>;
};

export const DocTypeTag: React.FC<{ type: string }> = ({ type }) => {
  return <Tag color="blue">{DOC_TYPE_MAP[type] || type}</Tag>;
};

export const formatAmount = (amount: number, currency: string = 'JPY') => {
  if (currency === 'JPY') return `¥${amount.toLocaleString()}`;
  if (currency === 'USD') return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  return `${amount.toLocaleString()} ${currency}`;
};