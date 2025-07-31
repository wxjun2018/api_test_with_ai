import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Modal, Form, Input, Select, Switch, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { filterAPI } from '../../services/api';
import styles from './index.module.less';

const { Option } = Select;

interface FilterRule {
    id: string;
    pattern: string;
    type: string;
    enabled: boolean;
    description?: string;
}

const FilterConfig: React.FC = () => {
    const [rules, setRules] = useState<FilterRule[]>([]);
    const [presets, setPresets] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [modalVisible, setModalVisible] = useState(false);
    const [editingRule, setEditingRule] = useState<FilterRule | null>(null);
    const [form] = Form.useForm();

    useEffect(() => {
        loadRules();
        loadPresets();
    }, []);

    const loadRules = async () => {
        try {
            setLoading(true);
            const response = await filterAPI.list();
            console.log('Filter rules response:', response);
            setRules(response || []);
        } catch (error) {
            console.error('Failed to load filter rules:', error);
            message.error('加载过滤规则失败');
            setRules([]);
        } finally {
            setLoading(false);
        }
    };

    const loadPresets = async () => {
        try {
            const response = await filterAPI.getPresets();
            console.log('Presets response:', response);
            setPresets(response || []);
        } catch (error) {
            console.error('Failed to load presets:', error);
            message.error('加载预设规则失败');
            setPresets([]);
        }
    };

    const handleAdd = () => {
        setEditingRule(null);
        form.resetFields();
        setModalVisible(true);
    };

    const handleEdit = (record: FilterRule) => {
        setEditingRule(record);
        form.setFieldsValue(record);
        setModalVisible(true);
    };

    const handleDelete = async (id: string) => {
        try {
            await filterAPI.delete(id);
            message.success('删除成功');
            loadRules();
        } catch (error) {
            message.error('删除失败');
        }
    };

    const handleToggle = async (id: string, enabled: boolean) => {
        try {
            await filterAPI.toggle(id, enabled);
            message.success(`${enabled ? '启用' : '禁用'}成功`);
            loadRules();
        } catch (error) {
            message.error(`${enabled ? '启用' : '禁用'}失败`);
        }
    };

    const handleSubmit = async (values: any) => {
        try {
            if (editingRule) {
                await filterAPI.update(editingRule.id, values);
                message.success('更新成功');
            } else {
                await filterAPI.add(values);
                message.success('添加成功');
            }
            setModalVisible(false);
            loadRules();
        } catch (error) {
            message.error(editingRule ? '更新失败' : '添加失败');
        }
    };

    const handleApplyPreset = async (presetId: string) => {
        try {
            await filterAPI.applyPreset(presetId);
            message.success('应用预设规则成功');
            loadRules();
        } catch (error) {
            message.error('应用预设规则失败');
        }
    };

    const handleReloadFilters = async () => {
        try {
            await filterAPI.reloadFilters();
            message.success('过滤规则重新加载成功');
        } catch (error) {
            message.error('重新加载过滤规则失败');
        }
    };

    const columns = [
        {
            title: '规则',
            dataIndex: 'pattern',
            key: 'pattern',
            width: '30%',
        },
        {
            title: '类型',
            dataIndex: 'type',
            key: 'type',
            width: '15%',
            render: (type: string) => {
                const typeMap: { [key: string]: string } = {
                    'url': 'URL',
                    'host': '域名',
                    'content-type': '内容类型',
                    'method': '请求方法'
                };
                return typeMap[type] || type;
            }
        },
        {
            title: '描述',
            dataIndex: 'description',
            key: 'description',
            width: '25%',
        },
        {
            title: '状态',
            dataIndex: 'enabled',
            key: 'enabled',
            width: '10%',
            render: (enabled: boolean, record: FilterRule) => (
                <Switch
                    checked={enabled}
                    onChange={(checked) => handleToggle(record.id, checked)}
                />
            )
        },
        {
            title: '操作',
            key: 'action',
            width: '20%',
            render: (_: any, record: FilterRule) => (
                <Space>
                    <Button
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    >
                        编辑
                    </Button>
                    <Popconfirm
                        title="确定要删除这个规则吗？"
                        onConfirm={() => handleDelete(record.id)}
                    >
                        <Button type="link" danger icon={<DeleteOutlined />}>
                            删除
                        </Button>
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <div className={styles.container}>
            <Card
                title="过滤规则配置"
                extra={
                    <Space>
                        <Button
                            icon={<ReloadOutlined />}
                            onClick={handleReloadFilters}
                        >
                            重新加载规则
                        </Button>
                        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                            添加规则
                        </Button>
                    </Space>
                }
            >
                <div style={{ marginBottom: 16 }}>
                    <h4>预设规则</h4>
                    <Space wrap>
                        {(presets || []).map(preset => (
                            <Button
                                key={preset.id}
                                onClick={() => handleApplyPreset(preset.id)}
                            >
                                {preset.name}
                            </Button>
                        ))}
                    </Space>
                </div>

                <Table
                    columns={columns}
                    dataSource={rules}
                    rowKey="id"
                    loading={loading}
                    pagination={false}
                />
            </Card>

            <Modal
                title={editingRule ? '编辑规则' : '添加规则'}
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                footer={null}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                >
                    <Form.Item
                        name="pattern"
                        label="规则模式"
                        rules={[{ required: true, message: '请输入规则模式' }]}
                    >
                        <Input placeholder="支持正则表达式" />
                    </Form.Item>

                    <Form.Item
                        name="type"
                        label="规则类型"
                        rules={[{ required: true, message: '请选择规则类型' }]}
                    >
                        <Select>
                            <Option value="url">URL</Option>
                            <Option value="host">域名</Option>
                            <Option value="content-type">内容类型</Option>
                            <Option value="method">请求方法</Option>
                        </Select>
                    </Form.Item>

                    <Form.Item
                        name="description"
                        label="描述"
                    >
                        <Input placeholder="规则描述（可选）" />
                    </Form.Item>

                    <Form.Item
                        name="enabled"
                        label="启用"
                        valuePropName="checked"
                        initialValue={true}
                    >
                        <Switch />
                    </Form.Item>

                    <Form.Item>
                        <Space>
                            <Button type="primary" htmlType="submit">
                                {editingRule ? '更新' : '添加'}
                            </Button>
                            <Button onClick={() => setModalVisible(false)}>
                                取消
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default FilterConfig; 