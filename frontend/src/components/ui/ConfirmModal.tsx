'use client';
import React from 'react';
import { Modal } from 'antd';

interface ConfirmModalProps {
  open: boolean;
  title: string;
  content: React.ReactNode;
  confirmLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  okText?: string;
  cancelText?: string;
  danger?: boolean;
}

export default function ConfirmModal({
  open,
  title,
  content,
  confirmLoading = false,
  onConfirm,
  onCancel,
  okText = 'OK',
  cancelText = 'Cancel',
  danger = false,
}: ConfirmModalProps) {
  return (
    <Modal
      title={title}
      open={open}
      onOk={onConfirm}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      okText={okText}
      cancelText={cancelText}
      okButtonProps={{ danger }}
    >
      {content}
    </Modal>
  );
}
