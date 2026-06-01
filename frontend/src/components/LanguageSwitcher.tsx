'use client';
import React from 'react';
import { Dropdown, Button, Space } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { useTranslation } from '@/hooks/useTranslation';
import { type Locale } from '@/lib/i18n';

const LOCALE_LABELS: Record<Locale, string> = {
  'zh-CN': '中文',
  'en-US': 'English',
  'ja-JP': '日本語',
};

const LOCALE_FLAGS: Record<Locale, string> = {
  'zh-CN': '🇨🇳',
  'en-US': '🇺🇸',
  'ja-JP': '🇯🇵',
};

interface LanguageSwitcherProps {
  /** Show flag emoji next to label. Defaults to true. */
  showFlag?: boolean;
  /** Button type passed to Ant Design Button. Defaults to "text". */
  buttonType?: 'text' | 'link' | 'default' | 'primary' | 'dashed';
  /** Display mode: show current language label or just the icon. Defaults to "icon". */
  mode?: 'icon' | 'label';
}

export default function LanguageSwitcher({
  showFlag = true,
  buttonType = 'text',
  mode = 'icon',
}: LanguageSwitcherProps) {
  const { locale, setLocale, locales } = useTranslation();

  const menuItems = locales.map((loc) => ({
    key: loc,
    label: (
      <Space>
        {showFlag && <span>{LOCALE_FLAGS[loc]}</span>}
        <span>{LOCALE_LABELS[loc]}</span>
      </Space>
    ),
    onClick: () => setLocale(loc),
  }));

  const currentLabel = (
    <Space>
      {showFlag && <span>{LOCALE_FLAGS[locale]}</span>}
      {mode === 'label' && <span>{LOCALE_LABELS[locale]}</span>}
    </Space>
  );

  return (
    <Dropdown menu={{ items: menuItems, selectedKeys: [locale] }} placement="bottomRight">
      <Button type={buttonType} icon={<GlobalOutlined />}>
        {mode === 'label' ? currentLabel : null}
      </Button>
    </Dropdown>
  );
}
