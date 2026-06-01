'use client';
import React, { createContext, useContext, useCallback, useState, useEffect } from 'react';
import { notification, Button, Space, Typography } from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined,
  InfoCircleOutlined, BellOutlined, CloseOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface NotificationConfig {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  closable?: boolean;
  timestamp: number;
}

interface NotificationContextType {
  notifications: NotificationConfig[];
  addNotification: (config: Omit<NotificationConfig, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
}

interface NotificationProviderProps {
  children: React.ReactNode;
  maxNotifications?: number;
}

export default function NotificationProvider({
  children,
  maxNotifications = 50,
}: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<NotificationConfig[]>([]);
  const [api, contextHolder] = notification.useNotification();

  const addNotification = useCallback((config: Omit<NotificationConfig, 'id' | 'timestamp'>) => {
    const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: NotificationConfig = {
      ...config,
      id,
      timestamp: Date.now(),
    };

    setNotifications(prev => {
      const updated = [newNotification, ...prev].slice(0, maxNotifications);
      return updated;
    });

    // Show Ant Design notification
    const iconMap = {
      success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      error: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
      warning: <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
      info: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
    };

    api[config.type]({
      message: config.title,
      description: config.message,
      icon: iconMap[config.type],
      duration: config.duration ?? 4.5,
      btn: config.action ? (
        <Button size="small" type="primary" onClick={config.action.onClick}>
          {config.action.label}
        </Button>
      ) : undefined,
      onClose: () => removeNotification(id),
    });
  }, [api, maxNotifications]);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
    api.destroy();
  }, [api]);

  const success = useCallback((title: string, message?: string) => {
    addNotification({ type: 'success', title, message });
  }, [addNotification]);

  const error = useCallback((title: string, message?: string) => {
    addNotification({ type: 'error', title, message, duration: 6 });
  }, [addNotification]);

  const warning = useCallback((title: string, message?: string) => {
    addNotification({ type: 'warning', title, message });
  }, [addNotification]);

  const info = useCallback((title: string, message?: string) => {
    addNotification({ type: 'info', title, message });
  }, [addNotification]);

  const contextValue: NotificationContextType = {
    notifications,
    addNotification,
    removeNotification,
    clearAll,
    success,
    error,
    warning,
    info,
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {contextHolder}
      {children}
    </NotificationContext.Provider>
  );
}

// Notification bell component with badge
export function NotificationBell() {
  const { notifications, clearAll } = useNotification();
  const [open, setOpen] = useState(false);
  const unreadCount = notifications.filter(n => Date.now() - n.timestamp < 60000).length;

  return (
    <div style={{ position: 'relative', cursor: 'pointer' }} onClick={() => setOpen(!open)}>
      <BellOutlined style={{ fontSize: 20 }} />
      {unreadCount > 0 && (
        <div style={{
          position: 'absolute',
          top: -4,
          right: -4,
          background: '#ff4d4f',
          color: '#fff',
          borderRadius: '50%',
          width: 16,
          height: 16,
          fontSize: 10,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {unreadCount > 9 ? '9+' : unreadCount}
        </div>
      )}
    </div>
  );
}

// Toast notification hook
export function useToast() {
  const { success, error, warning, info } = useNotification();

  const toast = useCallback((
    type: NotificationType,
    title: string,
    message?: string,
    duration?: number
  ) => {
    switch (type) {
      case 'success': success(title, message); break;
      case 'error': error(title, message); break;
      case 'warning': warning(title, message); break;
      case 'info': info(title, message); break;
    }
  }, [success, error, warning, info]);

  return { toast, success, error, warning, info };
}
