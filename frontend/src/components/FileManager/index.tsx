import React, { useState, useEffect } from 'react';
import { Table, Button, Upload, Space, Modal, message, Card, Statistic, Row, Col } from 'antd';
import { UploadOutlined, DeleteOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import { fileAPI } from '@/services/api';
import dayjs from 'dayjs';
import styles from './index.module.less';

interface FileInfo {
    name: string;
    original_name?: string;
    path: string;
    size: number;
    created_at: string;
    modified_at?: string;
}

interface StorageStats {
    total_size: number;
    file_count: number;
}

interface FileManagerProps {
    directory: 'har' | 'processed' | 'reports';
    title: string;
    accept?: string;
    onFileUploaded?: (file: FileInfo) => void;
}

const FileManager: React.FC<FileManagerProps> = ({
    directory,
    title,
    accept,
    onFileUploaded
}) => {
    const [files, setFiles] = useState<FileInfo[]>([]);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState<StorageStats>();
    const [uploadModalVisible, setUploadModalVisible] = useState(false);

    // 加载文件列表
    const loadFiles = async () => {
        try {
            setLoading(true);
            const data = await fileAPI.list(directory);
            setFiles(data);
        } catch (error) {
            console.error('Failed to load files:', error);
        } finally {
            setLoading(false);
        }
    };

    // 加载存储统计
    const loadStats = async () => {
        try {
            const data = await fileAPI.getStats();
            setStats(data[directory]);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    };

    useEffect(() => {
        loadFiles();
        loadStats();
    }, [directory]);

    // 处理文件上传
    const handleUpload = async (file: File) => {
        try {
            const data = await fileAPI.upload(directory, file);
            message.success('文件上传成功');
            loadFiles();
            loadStats();
            onFileUploaded?.(data);
            return false;
        } catch (error) {
            console.error('Failed to upload file:', error);
            return false;
        }
    };

    // 处理文件删除
    const handleDelete = async (filename: string) => {
        Modal.confirm({
            title: '确认删除',
            content: `确定要删除文件 ${filename} 吗？`,
            onOk: async () => {
                try {
                    await fileAPI.delete(directory, filename);
                    message.success('文件删除成功');
                    loadFiles();
                    loadStats();
                } catch (error) {
                    console.error('Failed to delete file:', error);
                }
            }
        });
    };

    // 处理文件下载
    const handleDownload = async (filename: string) => {
        try {
            await fileAPI.download(directory, filename);
        } catch (error) {
            console.error('Failed to download file:', error);
        }
    };

    // 表格列定义
    const columns = [
        {
            title: '文件名',
            dataIndex: 'name',
            key: 'name',
            render: (text: string, record: FileInfo) => (
                <span title={record.original_name}>{text}</span>
            )
        },
        {
            title: '大小',
            dataIndex: 'size',
            key: 'size',
            render: (size: number) => {
                const units = ['B', 'KB', 'MB', 'GB'];
                let value = size;
                let unitIndex = 0;
                while (value >= 1024 && unitIndex < units.length - 1) {
                    value /= 1024;
                    unitIndex++;
                }
                return `${value.toFixed(2)} ${units[unitIndex]}`;
            }
        },
        {
            title: '创建时间',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss')
        },
        {
            title: '操作',
            key: 'action',
            render: (_: any, record: FileInfo) => (
                <Space>
                    <Button
                        type="text"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownload(record.name)}
                    >
                        下载
                    </Button>
                    <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleDelete(record.name)}
                    >
                        删除
                    </Button>
                </Space>
            )
        }
    ];

    return (
        <Card
            title={title}
            extra={
                <Space>
                    <Upload
                        accept={accept}
                        showUploadList={false}
                        beforeUpload={handleUpload}
                    >
                        <Button icon={<UploadOutlined />}>上传文件</Button>
                    </Upload>
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={() => {
                            loadFiles();
                            loadStats();
                        }}
                    >
                        刷新
                    </Button>
                </Space>
            }
        >
            <Row gutter={16} className={styles.stats}>
                <Col span={12}>
                    <Statistic
                        title="文件数量"
                        value={stats?.file_count || 0}
                        suffix="个"
                    />
                </Col>
                <Col span={12}>
                    <Statistic
                        title="总大小"
                        value={(stats?.total_size || 0) / 1024 / 1024}
                        precision={2}
                        suffix="MB"
                    />
                </Col>
            </Row>

            <Table
                rowKey="name"
                columns={columns}
                dataSource={files}
                loading={loading}
                pagination={{
                    defaultPageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `共 ${total} 条`
                }}
            />
        </Card>
    );
};

export default FileManager; 