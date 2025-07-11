import axios from 'axios';

const customFetch = async (
  path: string,
  method: 'get' | 'post' | 'delete' | 'put',
  params = {}
) => {
  const url =
    method === 'get'
      ? `${process.env.NEXT_PUBLIC_API_URL}${path}?${new URLSearchParams(
          params as Record<string, string>
        )}`
      : `${process.env.NEXT_PUBLIC_API_URL}${path}`;
  let response;
  try {
    response = await axios({
      url: url,
      withCredentials: true,
      method,
      data: method === 'get' ? undefined : params,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorResponse = error.response;
      if (errorResponse && errorResponse.status === 403) {
        console.log('errorResponse', errorResponse);
        window.dispatchEvent(new Event('authError'));
      }
    }
    return null;
  }
};

// SSEのため、このエンドポイントのみ特殊実装
export const createChatMessageApi = async (
  params = {},
  onDataCallback: (chunk: string) => void
) => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/chat_messages`,
      {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      const errorJson = await response.json();
      throw new Error(errorJson.detail);
    }

    if (!response.body) {
      throw new Error('ストリームデータを受け取れませんでした。');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        onDataCallback(chunk);
      }
    }

    return { response: null, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getChatChatRoomsApi = async (params = {}) => {
  try {
    const response = await customFetch('/chat_rooms', 'get', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getChatRoomApi = async (params = {}) => {
  try {
    const response = await customFetch('/chat_room', 'get', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const createChatRoomsApi = async (params = {}) => {
  try {
    const response = await customFetch('/chat_rooms', 'post', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const putChatRoomsApi = async (params = {}) => {
  try {
    const response = await customFetch('/chat_rooms', 'put', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getListChatMessagesApi = async (params = {}) => {
  try {
    const response = await customFetch('/chat_messages', 'get', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const deleteChatMessagesApi = async (params = {}) => {
  try {
    const response = await customFetch('/chat_rooms', 'delete', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const logoutApi = async (params = {}) => {
  try {
    const response = await customFetch('/logout', 'post', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const dropoutApi = async (params = {}) => {
  try {
    const response = await customFetch('/dropout', 'post', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getAuthUrlApi = async () => {
  try {
    const response = await customFetch('/auth/url', 'get');
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getAdminAuthUrlApi = async () => {
  try {
    const response = await customFetch('/auth/admin/url', 'get');
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const handleAuthCallbackApi = async (code: string) => {
  try {
    const response = await customFetch('/auth/callback', 'get', { code });
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const putEvaluationApi = async (params = {}) => {
  try {
    const response = await customFetch(
      '/chat_message/evaluation',
      'put',
      params
    );
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getCoreConfigApi = async (params = {}) => {
  try {
    const response = await customFetch('/core_config', 'get', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getCoreNameApi = async (params = {}) => {
  try {
    const response = await customFetch('/core_name', 'get', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getAdminDashboardApi = async (params = {}) => {
  try {
    const response = await customFetch('/admin', 'get', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getUserInfoApi = async (params = {}) => {
  try {
    const response = await customFetch('/user', 'get', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const updateUserRoleApi = async (params = {}) => {
  try {
    const response = await customFetch('/user/role', 'put', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getSearchIndexTypesApi = async () => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/admin/search_index_types`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return { response: data, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const updateSearchIndexTypeApi = async (params: {
  index_type_id: string;
  folder_name: string;
}) => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/admin/search_index_type`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return { response: data, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const reorderSearchIndexTypesApi = async (params: {
  index_type_ids: string[];
}) => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/admin/search_index_types/reorder`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return { response: data, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getMaintenanceStatusApi = async (params = {}) => {
  try {
    const response = await customFetch('/maintenance_status', 'get', params);
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

export const getSearchIndexTypesForUserApi = async () => {
  try {
    const response = await customFetch('/search_index_types', 'get');
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

// ファイルアップロード＆インデックス化API
export const uploadAndIndexFileApi = async (
  file: File,
  indexType: string,
  onProgress?: (progress: number) => void
) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('index_type', indexType);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/index`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`Upload failed: ${response.status} - ${errorData}`);
    }

    const data = await response.json();
    return { response: data, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

// アップロード済みファイル一覧取得API
export const getUploadedFilesApi = async () => {
  try {
    const response = await customFetch('/api/blob-storage/list', 'get');
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

// ファイル削除API
export const deleteFileApi = async (blobName: string) => {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/blob-storage/delete/${encodeURIComponent(blobName)}`,
      {
        method: 'DELETE',
        credentials: 'include',
      }
    );

    if (!response.ok) {
      throw new Error(`Delete failed: ${response.status}`);
    }

    const data = await response.json();
    return { response: data, error: null };
  } catch (error) {
    return { response: null, error };
  }
};

// インデックス済みファイル一覧取得API
export const getIndexedFilesApi = async () => {
  try {
    const response = await customFetch('/indexed_files', 'get');
    return { response, error: null };
  } catch (error) {
    return { response: null, error };
  }
};
