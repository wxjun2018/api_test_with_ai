import React, { useState } from 'react';
import { Layout, Menu, Typography, theme } from 'antd';
import {
    FileOutlined,
    ApiOutlined,
    CheckSquareOutlined,
    BarChartOutlined,
    SettingOutlined,
    FilterOutlined,
    GlobalOutlined
} from '@ant-design/icons';
import FileManager from '@/components/FileManager';
import ProxyConfig from '@/components/ProxyConfig';
import FilterConfig from '@/components/FilterConfig';
import HostConfig from '@/components/HostConfig';
import styles from './index.module.less';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const Home: React.FC = () => {
    const [selectedKey, setSelectedKey] = useState('proxy');
    const { token } = theme.useToken();

    const renderContent = () => {
        switch (selectedKey) {
            case 'proxy':
                return <ProxyConfig />;
            case 'filter':
                return <FilterConfig />;
            case 'host':
                return <HostConfig />;
            case 'har':
                return (
                    <FileManager
                        directory="har"
                        title="HAR文件管理"
                        accept=".har"
                    />
                );
            case 'processed':
                return (
                    <FileManager
                        directory="processed"
                        title="处理后的数据"
                        accept=".json"
                    />
                );
            case 'reports':
                return (
                    <FileManager
                        directory="reports"
                        title="测试报告"
                        accept=".html,.pdf"
                    />
                );
            default:
                return null;
        }
    };

    return (
        <Layout className={styles.container}>
            <Header className={styles.header}>
                <Title level={4} style={{ color: token.colorTextLightSolid, margin: 0 }}>
                    接口测试平台
                </Title>
            </Header>

            <Layout>
                <Sider width={200} theme="light">
                    <Menu
                        mode="inline"
                        selectedKeys={[selectedKey]}
                        style={{ height: '100%', borderRight: 0 }}
                        items={[
                            {
                                key: 'proxy',
                                icon: <SettingOutlined />,
                                label: '代理配置'
                            },
                            {
                                key: 'filter',
                                icon: <FilterOutlined />,
                                label: '过滤规则'
                            },
                            {
                                key: 'host',
                                icon: <GlobalOutlined />,
                                label: 'Host过滤'
                            },
                            {
                                key: 'har',
                                icon: <FileOutlined />,
                                label: 'HAR文件'
                            },
                            {
                                key: 'processed',
                                icon: <ApiOutlined />,
                                label: '处理后的数据'
                            },
                            {
                                key: 'reports',
                                icon: <BarChartOutlined />,
                                label: '测试报告'
                            }
                        ]}
                        onClick={({ key }) => setSelectedKey(key)}
                    />
                </Sider>

                <Layout style={{ padding: '24px' }}>
                    <Content className={styles.content}>
                        {renderContent()}
                    </Content>
                </Layout>
            </Layout>
        </Layout>
    );
};

export default Home; 