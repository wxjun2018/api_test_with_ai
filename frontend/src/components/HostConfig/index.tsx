import React, { useState, useEffect } from 'react';
import {
    Card,
    Table,
    Button,
    Space,
    Modal,
    Form,
    Input,
    Switch,
    Tag,
    message,
    Popconfirm,
    Tooltip
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    QuestionCircleOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ReloadOutlined
} from '@ant-design/icons';
import { filterAPI, proxyAPI } from '../../services/api';

const { TextArea } = Input;

interface HostRule {
    id: string;
    host: string;
    enabled: boolean;
    description?: string;
    includeSubdomains: boolean;
}

const HostConfig: React.FC = () => {
    const [form] = Form.useForm();
    const [rules, setRules] = useState<HostRule[]>([]);
    const [loading, setLoading] = useState(false);
    const [modalVisible, setModalVisible] = useState(false);
    const [editingRule, setEditingRule] = useState<HostRule | null>(null);

    // 加载Host规则
    const loadRules = async () => {
        try {
            setLoading(true);
            const response = await filterAPI.listHosts();
            setRules(response || []);
        } catch (error) {
            console.error('Failed to load host rules:', error);
            message.error('加载Host规则失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadRules();
    }, []);

    // 处理规则提交
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields();
            if (editingRule) {
                await filterAPI.updateHost(editingRule.id, values);
                message.success('规则更新成功');
            } else {
                await filterAPI.addHost(values);
                message.success('规则添加成功');
            }
            setModalVisible(false);
            form.resetFields();
            setEditingRule(null);
            loadRules();
            // 自动重新加载Host规则
            await handleReloadHosts();
        } catch (error) {
            console.error('Failed to submit host rule:', error);
        }
    };

    // 处理规则删除
    const handleDelete = async (id: string) => {
        try {
            await filterAPI.deleteHost(id);
            message.success('规则删除成功');
            loadRules();
            // 自动重新加载Host规则
            await handleReloadHosts();
        } catch (error) {
            console.error('Failed to delete host rule:', error);
        }
    };

    // 处理规则启用/禁用
    const handleToggle = async (id: string, enabled: boolean) => {
        try {
            await filterAPI.toggleHost(id, enabled);
            message.success(`规则${enabled ? '启用' : '禁用'}成功`);
            loadRules();
            // 自动重新加载Host规则
            await handleReloadHosts();
        } catch (error) {
            console.error('Failed to toggle host rule:', error);
        }
    };

    // 重新加载Host规则
    const handleReloadHosts = async () => {
        try {
            await proxyAPI.reloadHosts();
            message.success('Host规则重新加载成功');
        } catch (error) {
            console.error('Failed to reload host rules:', error);
            message.error('重新加载Host规则失败');
        }
    };

    // 表格列定义
    const columns = [
        {
            title: '域名',
            dataIndex: 'host',
            key: 'host',
            render: (host: string, record: HostRule) => (
                <Space>
                    {host}
                    {record.includeSubdomains && (
                        <Tooltip title="包含子域名">
                            <Tag color="blue">*.{host}</Tag>
                        </Tooltip>
                    )}
                </Space>
            )
        },
        {
            title: '描述',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true
        },
        {
            title: '状态',
            dataIndex: 'enabled',
            key: 'enabled',
            render: (enabled: boolean, record: HostRule) => (
                <Switch
                    checked={enabled}
                    onChange={(checked) => handleToggle(record.id, checked)}
                    checkedChildren={<CheckCircleOutlined />}
                    unCheckedChildren={<CloseCircleOutlined />}
                />
            )
        },
        {
            title: '操作',
            key: 'action',
            render: (_: any, record: HostRule) => (
                <Space>
                    <Button
                        type="text"
                        icon={<EditOutlined />}
                        onClick={() => {
                            setEditingRule(record);
                            form.setFieldsValue(record);
                            setModalVisible(true);
                        }}
                    >
                        编辑
                    </Button>
                    <Popconfirm
                        title="确定要删除这条规则吗？"
                        onConfirm={() => handleDelete(record.id)}
                    >
                        <Button type="text" danger icon={<DeleteOutlined />}>
                            删除
                        </Button>
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <Card
            title="域名过滤配置"
            extra={
                <Space>
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={handleReloadHosts}
                    >
                        重新加载规则
                    </Button>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => {
                            setEditingRule(null);
                            form.resetFields();
                            setModalVisible(true);
                        }}
                    >
                        添加域名
                    </Button>
                </Space>
            }
        >
            <Table
                rowKey="id"
                columns={columns}
                dataSource={rules}
                loading={loading}
                pagination={{
                    defaultPageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `共 ${total} 条`
                }}
            />

            <Modal
                title={editingRule ? '编辑域名规则' : '添加域名规则'}
                open={modalVisible}
                onOk={handleSubmit}
                onCancel={() => {
                    setModalVisible(false);
                    form.resetFields();
                    setEditingRule(null);
                }}
            >
                <Form
                    form={form}
                    layout="vertical"
                    initialValues={{
                        enabled: true,
                        includeSubdomains: false
                    }}
                >
                    <Form.Item
                        label={
                            <Space>
                                域名
                                <Tooltip title="支持精确域名或通配符域名，例如：example.com、*.example.com">
                                    <QuestionCircleOutlined />
                                </Tooltip>
                            </Space>
                        }
                        name="host"
                        rules={[
                            { required: true, message: '请输入域名' },
                            {
                                pattern: /^[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)*$/,
                                message: '请输入有效的域名'
                            }
                        ]}
                    >
                        <Input placeholder="请输入域名，例如：example.com" />
                    </Form.Item>

                    <Form.Item
                        label="包含子域名"
                        name="includeSubdomains"
                        valuePropName="checked"
                    >
                        <Switch />
                    </Form.Item>

                    <Form.Item
                        label="描述"
                        name="description"
                    >
                        <TextArea
                            placeholder="请输入规则描述"
                            autoSize={{ minRows: 2, maxRows: 4 }}
                        />
                    </Form.Item>

                    <Form.Item
                        label="启用规则"
                        name="enabled"
                        valuePropName="checked"
                    >
                        <Switch />
                    </Form.Item>
                </Form>
            </Modal>
        </Card>
    );
};

export default HostConfig; 