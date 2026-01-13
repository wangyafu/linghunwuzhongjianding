// API 配置
// 根据环境自动选择 base URL

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// API 端点
export const API_ENDPOINTS = {
    presetSpecies: `${API_BASE_URL}/api/preset-species`,
    diagnose: `${API_BASE_URL}/api/diagnose`,
}

// 通用 fetch 包装器
export async function apiFetch<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    const response = await fetch(endpoint, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    })

    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
    }

    return response.json()
}
