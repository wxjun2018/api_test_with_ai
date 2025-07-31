import React, { useState, useEffect } from 'react';
import {
    Card,
    Form,
    Input,
    InputNumber,
    Switch,
    Radio,
    Button,
    Space,
    Alert,
    Typography,
    message,
    Tooltip,
    Badge
} from 'antd';
import {
    PlayCircleOutlined,
    PauseCircleOutlined,
    DownloadOutlined,
    QuestionCircleOutlined
} from '@ant-design/icons';
import { proxyAPI } from '@/services/api';
import styles from './index.module.less';

const { Text, Link } = Typography;

interface ProxyStatus {
    running: boolean;
    port?: number;
    mode?: 'system' | 'manual';
    enableHttps?: boolean;
    certPath?: string;
}

const ProxyConfig: React.FC = () => {
    const [form] = Form.useForm();
    const [status, setStatus] = useState<ProxyStatus>({ running: false });
    const [loading, setLoading] = useState(false);

    // 加载代理状态和配置
    const loadStatus = async () => {
        try {
            const [statusData, configData] = await Promise.all([
                proxyAPI.getStatus(),
                proxyAPI.getConfig()
            ]);
            setStatus(statusData);
            form.setFieldsValue(configData);
        } catch (error) {
            console.error('Failed to load proxy status:', error);
        }
    };

    useEffect(() => {
        loadStatus();
    }, []);

    // 启动代理
    const handleStart = async () => {
        try {
            setLoading(true);
            const values = await form.validateFields();
            await proxyAPI.start(values);
            message.success('代理服务已启动');
            loadStatus();
        } catch (error) {
            console.error('Failed to start proxy:', error);
        } finally {
            setLoading(false);
        }
    };

    // 停止代理
    const handleStop = async () => {
        try {
            setLoading(true);
            await proxyAPI.stop();
            message.success('代理服务已停止');
            loadStatus();
        } catch (error) {
            console.error('Failed to stop proxy:', error);
        } finally {
            setLoading(false);
        }
    };

    // 下载证书
    const handleDownloadCert = async () => {
        try {
            const response = await proxyAPI.getCertificate();
            const url = window.URL.createObjectURL(new Blob([response]));
            const link = document.createElement('a');
            link.href = url;
            link.download = 'mitmproxy-ca-cert.pem';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Failed to download certificate:', error);
        }
    };

    // 保存配置
    const handleSave = async () => {
        try {
            setLoading(true);
            const values = await form.validateFields();
            await proxyAPI.updateConfig(values);
            message.success('配置已保存');
            loadStatus();
        } catch (error) {
            console.error('Failed to save config:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card
            title={
                <Space>
                    代理服务配置
                    <Badge
                        status={status.running ? 'success' : 'default'}
                        text={status.running ? '运行中' : '已停止'}
                    />
                </Space>
            }
            className={styles.container}
        >
            {status.running && (
                <Alert
                    message={
                        <Space>
                            <Text>代理服务运行中，端口：{status.port}</Text>
                            <Text>模式：{status.mode === 'system' ? '系统代理' : '手动配置'}</Text>
                        </Space>
                    }
                    type="success"
                    showIcon
                    className={styles.alert}
                />
            )}

            <Form
                form={form}
                layout="vertical"
                initialValues={{
                    port: 8080,
                    mode: 'system',
                    enableHttps: true
                }}
            >
                <Form.Item
                    label="代理端口"
                    name="port"
                    rules={[
                        { required: true, message: '请输入代理端口' },
                        { type: 'number', min: 1024, max: 65535, message: '端口范围：1024-65535' }
                    ]}
                >
                    <InputNumber style={{ width: '100%' }} min={1024} max={65535} placeholder="请输入代理端口" />
                </Form.Item>

                <Form.Item
                    label={
                        <Space>
                            代理模式
                            <Tooltip title="系统代理：自动配置系统代理设置；手动配置：需要手动在应用中设置代理">
                                <QuestionCircleOutlined />
                            </Tooltip>
                        </Space>
                    }
                    name="mode"
                >
                    <Radio.Group>
                        <Radio value="system">系统代理</Radio>
                        <Radio value="manual">手动配置</Radio>
                    </Radio.Group>
                </Form.Item>

                <Form.Item
                    label={
                        <Space>
                            HTTPS支持
                            <Tooltip title="启用HTTPS支持需要安装证书">
                                <QuestionCircleOutlined />
                            </Tooltip>
                        </Space>
                    }
                    name="enableHttps"
                    valuePropName="checked"
                >
                    <Switch />
                </Form.Item>

                <Form.Item>
                    <Space direction="vertical" style={{ width: '100%' }}>
                        <Space>
                            <Button
                                type="primary"
                                icon={status.running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                                onClick={status.running ? handleStop : handleStart}
                                loading={loading}
                            >
                                {status.running ? '停止代理' : '启动代理'}
                            </Button>
                            <Button onClick={handleSave} loading={loading}>
                                保存配置
                            </Button>
                            <Button
                                icon={<DownloadOutlined />}
                                onClick={handleDownloadCert}
                                disabled={!status.enableHttps}
                            >
                                下载证书
                            </Button>
                        </Space>
                        {status.enableHttps && (
                            <Alert
                                message="HTTPS配置说明"
                                description={
                                    <div>
                                        <Text>1. 下载并安装证书到系统受信任的根证书颁发机构</Text>
                                        <br />
                                        <Text>2. Windows系统可双击证书文件安装</Text>
                                        <br />
                                        <Text>
                                            3. 更多帮助请参考：
                                            <Link href="https://docs.mitmproxy.org/stable/concepts-certificates/" target="_blank">
                                                mitmproxy证书安装说明
                                            </Link>
                                        </Text>
                                    </div>
                                }
                                type="info"
                                showIcon
                            />
                        )}
                    </Space>
                </Form.Item>
            </Form>
        </Card>
    );
};

export default ProxyConfig; 