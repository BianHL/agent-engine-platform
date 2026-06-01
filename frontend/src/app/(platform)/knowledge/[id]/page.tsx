'use client';
import React, { useEffect, useState, useCallback } from 'react';
import {
  Card, Descriptions, Upload, Button, Typography, Spin, message, Table, Tag, Space, Popconfirm,
  Tabs, Input, List, Modal, InputNumber,
} from 'antd';
import { UploadOutlined, DeleteOutlined, SearchOutlined, ExperimentOutlined, LinkOutlined, GlobalOutlined } from '@ant-design/icons';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import { KnowledgeBase, Document, Chunk, RetrievalResult } from '@/types';

const { Title, Text } = Typography;
const { TextArea } = Input;

const STATUS_COLORS: Record<string, string> = {
  pending: 'default',
  processing: 'processing',
  ready: 'success',
  failed: 'error',
  indexed: 'success',
  error: 'error',
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export default function KnowledgeBaseDetailPage() {
  const params = useParams();
  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [docsLoading, setDocsLoading] = useState(true);

  // Chunks state
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | undefined>();

  // Retrieval test state
  const [retrievalQuery, setRetrievalQuery] = useState('');
  const [retrievalResults, setRetrievalResults] = useState<RetrievalResult[]>([]);
  const [retrievalLoading, setRetrievalLoading] = useState(false);

  // URL import state
  const [showUrlModal, setShowUrlModal] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const [urlImporting, setUrlImporting] = useState(false);
  const [crawlMode, setCrawlMode] = useState(false);
  const [crawlMaxPages, setCrawlMaxPages] = useState(10);

  const fetchDocuments = useCallback(async (kbId: string) => {
    setDocsLoading(true);
    try {
      const res = await api.listDocuments(kbId);
      setDocuments(res.items || res || []);
    } catch {
      message.error('Failed to load documents');
    } finally {
      setDocsLoading(false);
    }
  }, []);

  const fetchChunks = useCallback(async (kbId: string, docId?: string) => {
    setChunksLoading(true);
    try {
      const res = await api.listChunks(kbId, docId);
      setChunks(res.items || res || []);
    } catch {
      message.error('Failed to load chunks');
    } finally {
      setChunksLoading(false);
    }
  }, []);

  useEffect(() => {
    if (params.id) {
      const kbId = params.id as string;
      api.getKnowledgeBase(kbId)
        .then((data) => {
          setKb(data);
          fetchDocuments(kbId);
        })
        .catch(() => message.error('Not found'))
        .finally(() => setLoading(false));
    }
  }, [params.id, fetchDocuments]);

  const handleDeleteDocument = async (docId: string) => {
    if (!kb) return;
    try {
      await api.deleteDocument(kb.id, docId);
      message.success('Document deleted');
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch {
      message.error('Failed to delete document');
    }
  };

  const handleUploadSuccess = () => {
    if (kb) {
      fetchDocuments(kb.id);
      api.getKnowledgeBase(kb.id).then(setKb).catch(() => {});
    }
  };

  const handleTabChange = (key: string) => {
    if (!kb) return;
    if (key === 'chunks') {
      fetchChunks(kb.id, selectedDocId);
    }
  };

  const handleRetrievalTest = async () => {
    if (!kb || !retrievalQuery.trim()) return;
    setRetrievalLoading(true);
    setRetrievalResults([]);
    try {
      const results = await api.retrievalTest(kb.id, retrievalQuery.trim());
      setRetrievalResults(Array.isArray(results) ? results : []);
    } catch {
      message.error('Retrieval test failed');
    } finally {
      setRetrievalLoading(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!kb) return <div>Knowledge base not found</div>;

  const docColumns = [
    { title: 'Filename', dataIndex: 'filename', key: 'filename', ellipsis: true },
    { title: 'Type', dataIndex: 'file_type', key: 'file_type', width: 100 },
    {
      title: 'Size', dataIndex: 'file_size', key: 'file_size', width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 120,
      render: (s: string) => <Tag color={STATUS_COLORS[s] || 'default'}>{s}</Tag>,
    },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: 'Action', key: 'action', width: 80,
      render: (_: any, record: Document) => (
        <Popconfirm title="Delete this document?" onConfirm={() => handleDeleteDocument(record.id)}>
          <Button type="link" danger icon={<DeleteOutlined />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  const chunkColumns = [
    {
      title: 'ID', dataIndex: 'id', key: 'id', width: 100, ellipsis: true,
    },
    {
      title: 'Document', dataIndex: 'document_id', key: 'document_id', width: 100, ellipsis: true,
    },
    {
      title: 'Content', dataIndex: 'content', key: 'content', ellipsis: true,
      render: (text: string) => (
        <div style={{ maxHeight: 60, overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {text}
        </div>
      ),
    },
    {
      title: 'Score', dataIndex: 'score', key: 'score', width: 80,
      render: (v: number | undefined) => v !== undefined ? v.toFixed(4) : '-',
    },
  ];

  return (
    <div>
      <Title level={4}>{kb.name}</Title>
      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="Description" span={2}>{kb.description || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Embedding Model">{kb.embedding_model}</Descriptions.Item>
          <Descriptions.Item label="Documents">{kb.document_count}</Descriptions.Item>
          <Descriptions.Item label="Status"><Tag color="green">{kb.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="Created">{kb.created_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card>
        <Tabs
          onChange={handleTabChange}
          items={[
            {
              key: 'documents',
              label: `Documents (${documents.length})`,
              children: (
                <>
                  <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                    <Button icon={<LinkOutlined />} onClick={() => setShowUrlModal(true)}>
                      Import from URL
                    </Button>
                    <Upload
                      customRequest={async ({ file, onSuccess }) => {
                        try {
                          await api.uploadDocument(kb.id, file as File);
                          message.success('Uploaded');
                          onSuccess?.({});
                          handleUploadSuccess();
                        } catch {
                          message.error('Upload failed');
                        }
                      }}
                      showUploadList={false}
                    >
                      <Button icon={<UploadOutlined />}>Upload Document</Button>
                    </Upload>
                  </div>
                  <Table
                    dataSource={documents}
                    columns={docColumns}
                    loading={docsLoading}
                    rowKey="id"
                    size="small"
                    pagination={{ pageSize: 20 }}
                  />
                </>
              ),
            },
            {
              key: 'chunks',
              label: `Chunks (${chunks.length})`,
              children: (
                <>
                  <div style={{ marginBottom: 12 }}>
                    <Space>
                      <Text strong>Filter by document:</Text>
                      <select
                        value={selectedDocId || ''}
                        onChange={(e) => {
                          const val = e.target.value || undefined;
                          setSelectedDocId(val);
                          fetchChunks(kb.id, val);
                        }}
                        style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid #d9d9d9' }}
                      >
                        <option value="">All documents</option>
                        {documents.map((d) => (
                          <option key={d.id} value={d.id}>{d.filename}</option>
                        ))}
                      </select>
                    </Space>
                  </div>
                  <Table
                    dataSource={chunks}
                    columns={chunkColumns}
                    loading={chunksLoading}
                    rowKey="id"
                    size="small"
                    pagination={{ pageSize: 20 }}
                    expandable={{
                      expandedRowRender: (record: Chunk) => (
                        <div style={{ padding: 8 }}>
                          <Text strong>Full content:</Text>
                          <pre style={{
                            whiteSpace: 'pre-wrap',
                            background: '#f6f8fa',
                            padding: 12,
                            borderRadius: 6,
                            maxHeight: 300,
                            overflow: 'auto',
                            fontSize: 13,
                            marginTop: 8,
                          }}>
                            {record.content}
                          </pre>
                          {record.metadata && Object.keys(record.metadata).length > 0 && (
                            <div style={{ marginTop: 8 }}>
                              <Text strong>Metadata:</Text>
                              <pre style={{
                                whiteSpace: 'pre-wrap',
                                background: '#f0f0f0',
                                padding: 8,
                                borderRadius: 4,
                                fontSize: 12,
                                marginTop: 4,
                              }}>
                                {JSON.stringify(record.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      ),
                    }}
                  />
                </>
              ),
            },
            {
              key: 'retrieval',
              label: (
                <Space>
                  <ExperimentOutlined />
                  Retrieval Test
                </Space>
              ),
              children: (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <Space.Compact style={{ width: '100%' }}>
                      <TextArea
                        value={retrievalQuery}
                        onChange={(e) => setRetrievalQuery(e.target.value)}
                        placeholder="Enter a test query to search for matching chunks..."
                        rows={3}
                        style={{ flex: 1 }}
                      />
                      <Button
                        type="primary"
                        icon={<SearchOutlined />}
                        loading={retrievalLoading}
                        onClick={handleRetrievalTest}
                        disabled={!retrievalQuery.trim()}
                        style={{ height: 'auto' }}
                      >
                        Search
                      </Button>
                    </Space.Compact>
                  </div>

                  {retrievalResults.length > 0 && (
                    <List
                      header={<Text strong>{retrievalResults.length} results found</Text>}
                      dataSource={retrievalResults}
                      renderItem={(result: RetrievalResult) => (
                        <List.Item>
                          <Card
                            size="small"
                            style={{ width: '100%' }}
                            title={
                              <Space>
                                <Tag color="blue">Score: {result.score.toFixed(4)}</Tag>
                                <Text type="secondary">Doc: {result.document_id}</Text>
                              </Space>
                            }
                          >
                            <pre style={{
                              whiteSpace: 'pre-wrap',
                              margin: 0,
                              fontSize: 13,
                              lineHeight: 1.6,
                            }}>
                              {result.content}
                            </pre>
                            {result.metadata && Object.keys(result.metadata).length > 0 && (
                              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                                Metadata: {JSON.stringify(result.metadata)}
                              </div>
                            )}
                          </Card>
                        </List.Item>
                      )}
                    />
                  )}

                  {retrievalResults.length === 0 && !retrievalLoading && retrievalQuery && (
                    <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                      Enter a query and click Search to test retrieval
                    </div>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* URL Import Modal */}
      <Modal
        title={crawlMode ? "Crawl Website" : "Import from URL"}
        open={showUrlModal}
        onCancel={() => { setShowUrlModal(false); setUrlInput(''); }}
        onOk={async () => {
          if (!urlInput.trim()) {
            message.error('Please enter a URL');
            return;
          }
          setUrlImporting(true);
          try {
            if (crawlMode) {
              const result = await api.crawlUrlToKnowledgeBase(kb.id, {
                url: urlInput.trim(),
                max_pages: crawlMaxPages,
              });
              message.success(`Crawled ${result.processed} pages`);
            } else {
              await api.addUrlToKnowledgeBase(kb.id, {
                url: urlInput.trim(),
              });
              message.success('URL imported successfully');
            }
            setShowUrlModal(false);
            setUrlInput('');
            handleUploadSuccess();
          } catch {
            message.error(crawlMode ? 'Crawl failed' : 'URL import failed');
          } finally {
            setUrlImporting(false);
          }
        }}
        confirmLoading={urlImporting}
        okText={crawlMode ? "Start Crawl" : "Import"}
      >
        <div style={{ marginBottom: 12 }}>
          <Space>
            <Button
              size="small"
              type={crawlMode ? 'default' : 'primary'}
              onClick={() => setCrawlMode(false)}
            >
              Single URL
            </Button>
            <Button
              size="small"
              type={crawlMode ? 'primary' : 'default'}
              icon={<GlobalOutlined />}
              onClick={() => setCrawlMode(true)}
            >
              Crawl Website
            </Button>
          </Space>
        </div>
        <Input
          placeholder={crawlMode ? "https://example.com (starting URL)" : "https://example.com/page"}
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          prefix={<LinkOutlined />}
        />
        {crawlMode && (
          <div style={{ marginTop: 12 }}>
            <Text type="secondary">Max pages to crawl: </Text>
            <InputNumber
              min={1}
              max={100}
              value={crawlMaxPages}
              onChange={(v) => setCrawlMaxPages(v || 10)}
              style={{ width: 80 }}
            />
          </div>
        )}
      </Modal>
    </div>
  );
}
