import axios from 'axios';
import { message } from 'antd';

// 创建axios实例
const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
});

// 响应拦截器
api.interceptors.response.use(
    (response) => response.data,
    (error) => {
        const msg = error.response?.data?.detail || error.message;
        message.error(msg);
        return Promise.reject(error);
    }
);

// 代理配置API
export const proxyAPI = {
    // 获取代理状态
    getStatus: async () => {
        return api.get('/proxy/status');
    },

    // 启动代理服务
    start: async (config: {
        port: number;
        host?: string;
        mode: 'system' | 'manual';
        enableHttps: boolean;
        certPath?: string;
    }) => {
        return api.post('/proxy/start', config);
    },

    // 停止代理服务
    stop: async () => {
        return api.post('/proxy/stop');
    },

    // 获取证书
    getCertificate: async () => {
        return api.get('/proxy/certificate', { responseType: 'blob' });
    },

    // 获取代理配置
    getConfig: async () => {
        return api.get('/proxy/config');
    },

    // 更新代理配置
    updateConfig: async (config: {
        port: number;
        host?: string;
        mode: 'system' | 'manual';
        enableHttps: boolean;
        certPath?: string;
    }) => {
        return api.put('/proxy/config', config);
    },

    // 重新加载过滤规则
    reloadFilters: () => api.post('/proxy/reload-filters'),

    // 重新加载Host规则
    reloadHosts: () => api.post('/proxy/reload-hosts')
};

// 文件相关API
export const fileAPI = {
    // 上传文件
    upload: async (directory: string, file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post(`/files/upload/${directory}`, formData);
    },

    // 获取文件列表
    list: async (directory: string) => {
        return api.get(`/files/list/${directory}`);
    },

    // 下载文件
    download: async (directory: string, filename: string) => {
        const response = await api.get(`/files/download/${directory}/${filename}`, {
            responseType: 'blob'
        });
        const url = window.URL.createObjectURL(new Blob([response]));
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    // 删除文件
    delete: async (directory: string, filename: string) => {
        return api.delete(`/files/${directory}/${filename}`);
    },

    // 清理文件
    cleanup: async (directory: string, days: number) => {
        return api.post(`/files/cleanup/${directory}`, { days });
    },

    // 获取存储统计
    getStats: async () => {
        return api.get('/files/stats');
    }
};

// HAR文件处理API
export const harAPI = {
    // 解析HAR文件
    parse: async (filename: string) => {
        return api.post(`/har/parse/${filename}`);
    },

    // 获取API列表
    getApis: async (filename: string) => {
        return api.get(`/har/apis/${filename}`);
    },

    // 生成测试用例
    generateTests: async (filename: string) => {
        return api.post(`/har/generate-tests/${filename}`);
    }
};

// 测试用例API
export const testAPI = {
    // 获取测试用例列表
    list: async () => {
        return api.get('/tests');
    },

    // 获取测试用例详情
    get: async (id: string) => {
        return api.get(`/tests/${id}`);
    },

    // 创建测试用例
    create: async (data: any) => {
        return api.post('/tests', data);
    },

    // 更新测试用例
    update: async (id: string, data: any) => {
        return api.put(`/tests/${id}`, data);
    },

    // 删除测试用例
    delete: async (id: string) => {
        return api.delete(`/tests/${id}`);
    },

    // 执行测试用例
    run: async (id: string) => {
        return api.post(`/tests/${id}/run`);
    },

    // 获取测试结果
    getResults: async (id: string) => {
        return api.get(`/tests/${id}/results`);
    }
};

// 过滤规则API
export const filterAPI = {
    // 获取过滤规则列表
    list: async () => {
        return api.get('/filters');
    },

    // 添加过滤规则
    add: async (data: {
        pattern: string;
        type: 'url' | 'content-type' | 'host';
        enabled: boolean;
        description?: string;
    }) => {
        return api.post('/filters', data);
    },

    // 更新过滤规则
    update: async (id: string, data: {
        pattern: string;
        type: 'url' | 'content-type' | 'host';
        enabled: boolean;
        description?: string;
    }) => {
        return api.put(`/filters/${id}`, data);
    },

    // 删除过滤规则
    delete: async (id: string) => {
        return api.delete(`/filters/${id}`);
    },

    // 启用/禁用过滤规则
    toggle: async (id: string, enabled: boolean) => {
        return api.patch(`/filters/${id}/toggle`, { enabled });
    },

    // 获取预设规则
    getPresets: async () => {
        return api.get('/filters/presets');
    },

    // 应用预设规则
    applyPreset: async (presetId: string) => {
        return api.post(`/filters/presets/${presetId}/apply`);
    },

    // Host规则相关API
    listHosts: async () => {
        return api.get('/filters/hosts');
    },

    addHost: async (data: {
        host: string;
        enabled: boolean;
        description?: string;
        includeSubdomains: boolean;
    }) => {
        return api.post('/filters/hosts', data);
    },

    updateHost: async (id: string, data: {
        host: string;
        enabled: boolean;
        description?: string;
        includeSubdomains: boolean;
    }) => {
        return api.put(`/filters/hosts/${id}`, data);
    },

    deleteHost: async (id: string) => {
        return api.delete(`/filters/hosts/${id}`);
    },

    toggleHost: async (id: string, enabled: boolean) => {
        return api.patch(`/filters/hosts/${id}/toggle`, { enabled });
    },

    // 重新加载过滤规则
    reloadFilters: () => api.post('/proxy/reload-filters'),
}; 