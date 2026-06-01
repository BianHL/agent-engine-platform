'use client';
import React, { useEffect, useState } from 'react';
import { Card, Form, Input, Select, Button, Typography, message, Steps, Space } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Agent } from '@/types';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const CATEGORIES = [
  '客户服务', '生产管理', '供应链', '财务管理', '人力资源',
  '质量管理', '安全环保', '办公协同', '数据分析', '其他'
];

export default function SubmitPage() {
  const router = useRouter();
  const [form] = Form.useForm();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await api.listAgents(1, 100);
      setAgents(data.items || []);
    } catch {
      // ignore
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      await api.submitForReview({
        asset_type: 'agent',
        asset_id: values.asset_id,
        title: values.title,
        summary: values.summary,
        description: values.description || '',
        category: values.category,
        tags: values.tags || [],
        visibility: values.visibility || 'tenant',
      });
      message.success('提交成功，等待管理员审核');
      router.push('/marketplace/my-submissions');
    } catch (e: any) {
      if (e?.response?.data?.detail) {
        message.error(e.response.data.detail);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ padding: '0 4px', maxWidth: 800, margin: '0 auto' }}>
      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        onClick={() => router.back()}
        style={{ marginBottom: 16 }}
      >
        返回
      </Button>

      <Card>
        <Title level={4}>申请资产上架</Title>
        <Paragraph type="secondary">
          将您的优质AI资产提交到市集，经管理员审核通过后即可被全集团发现和使用
        </Paragraph>

        <Steps
          current={currentStep}
          items={[
            { title: '选择资产' },
            { title: '填写信息' },
            { title: '提交审核' },
          ]}
          style={{ marginBottom: 32 }}
        />

        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {currentStep === 0 && (
            <>
              <Form.Item
                name="asset_id"
                label="选择要上架的智能体"
                rules={[{ required: true, message: '请选择一个智能体' }]}
              >
                <Select
                  placeholder="选择您创建的智能体"
                  showSearch
                  optionFilterProp="label"
                  options={agents.map(a => ({
                    label: `${a.name} (${a.status})`,
                    value: a.id,
                  }))}
                />
              </Form.Item>
              <Button type="primary" onClick={() => {
                form.validateFields(['asset_id']).then(() => setCurrentStep(1)).catch(() => {});
              }}>
                下一步
              </Button>
            </>
          )}

          {currentStep === 1 && (
            <>
              <Form.Item
                name="title"
                label="资产标题"
                rules={[
                  { required: true, message: '请输入标题' },
                  { max: 200, message: '标题不超过200字' },
                ]}
              >
                <Input placeholder="为您的资产起一个吸引人的标题" />
              </Form.Item>

              <Form.Item
                name="summary"
                label="简介摘要"
                rules={[
                  { required: true, message: '请输入简介' },
                  { max: 500, message: '简介不超过500字' },
                ]}
              >
                <TextArea rows={3} placeholder="简要描述资产的功能和适用场景" />
              </Form.Item>

              <Form.Item name="description" label="详细描述">
                <TextArea rows={6} placeholder="详细介绍资产的功能、使用方法、技术特点等（支持Markdown）" />
              </Form.Item>

              <Form.Item
                name="category"
                label="业务分类"
                rules={[{ required: true, message: '请选择分类' }]}
              >
                <Select placeholder="选择业务分类">
                  {CATEGORIES.map(c => (
                    <Select.Option key={c} value={c}>{c}</Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item name="tags" label="标签">
                <Select mode="tags" placeholder="输入标签，按回车添加" />
              </Form.Item>

              <Form.Item name="visibility" label="可见范围" initialValue="tenant">
                <Select>
                  <Select.Option value="department">本部门</Select.Option>
                  <Select.Option value="tenant">本单位</Select.Option>
                  <Select.Option value="public">全集团</Select.Option>
                </Select>
              </Form.Item>

              <Space>
                <Button onClick={() => setCurrentStep(0)}>上一步</Button>
                <Button type="primary" onClick={() => setCurrentStep(2)}>下一步</Button>
              </Space>
            </>
          )}

          {currentStep === 2 && (
            <>
              <Card style={{ background: '#f6ffed', marginBottom: 24 }}>
                <Paragraph>
                  您的资产将提交至本单位管理员审核。审核通过后，将在您设定的可见范围内上线。
                </Paragraph>
                <Paragraph type="secondary">
                  审核内容包括：政治合规性、数据安全性、业务适用性
                </Paragraph>
              </Card>
              <Space>
                <Button onClick={() => setCurrentStep(1)}>上一步</Button>
                <Button type="primary" htmlType="submit" loading={submitting}>
                  提交审核
                </Button>
              </Space>
            </>
          )}
        </Form>
      </Card>
    </div>
  );
}
