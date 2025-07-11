'use client';

import { useState } from 'react';

interface ApiResponse {
  status: 'success' | 'error';
  user_message?: string;
  ai_response?: string;
  response_content?: string;
  model?: string;
  response_time_ms?: number;
  error?: string;
  [key: string]: unknown;
}

interface BlobStorageResponse {
  status: 'success' | 'error';
  message?: string;
  upload_info?: any;
  sas_url?: string;
  documents?: any[];
  count?: number;
  error?: string;
  test_results?: any;
  [key: string]: unknown;
}

interface SearchResponse {
  status: 'success' | 'error';
  results?: any[];
  count?: number;
  error?: string;
  [key: string]: unknown;
}

interface IndexResponse {
  status: 'success' | 'error';
  message?: string;
  processed_chunks?: number;
  filename?: string;
  index_type?: string;
  error?: string;
  [key: string]: unknown;
}

interface DocumentIntelligenceResponse {
  status: 'success' | 'error';
  file_type?: string;
  filename?: string;
  pages_processed?: number;
  sample_content?: string;
  metadata?: any;
  message?: string;
  supported_formats?: string[];
  error?: string;
  [key: string]: unknown;
}

export default function AzureServicesTestPage() {
  // Azure OpenAI
  const [openaiMessage, setOpenaiMessage] = useState<string>(
    'Azure OpenAIの接続テストです'
  );
  const [openaiResponse, setOpenaiResponse] = useState<ApiResponse | null>(
    null
  );
  const [openaiLoading, setOpenaiLoading] = useState<boolean>(false);

  // Azure Blob Storage
  const [blobResponse, setBlobResponse] = useState<BlobStorageResponse | null>(
    null
  );
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [blobLoading, setBlobLoading] = useState<boolean>(false);

  // Azure AI Search
  const [searchQuery, setSearchQuery] = useState<string>('test search query');
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(
    null
  );
  const [searchLoading, setSearchLoading] = useState<boolean>(false);

  // Real-time Indexing
  const [indexFile, setIndexFile] = useState<File | null>(null);
  const [indexResponse, setIndexResponse] = useState<IndexResponse | null>(
    null
  );
  const [indexLoading, setIndexLoading] = useState<boolean>(false);

  // Azure AI Document Intelligence
  const [docIntelFile, setDocIntelFile] = useState<File | null>(null);
  const [docIntelResponse, setDocIntelResponse] =
    useState<DocumentIntelligenceResponse | null>(null);
  const [docIntelLoading, setDocIntelLoading] = useState<boolean>(false);

  // 環境変数からAPI URLを取得
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  // Azure OpenAI関連の関数
  const testOpenAIChat = async () => {
    setOpenaiLoading(true);
    try {
      const res = await fetch(`${apiUrl}/test/azure-openai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: openaiMessage }),
      });
      const data = await res.json();
      setOpenaiResponse(data);
    } catch (error) {
      setOpenaiResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setOpenaiLoading(false);
  };

  const testOpenAIConnectivity = async () => {
    setOpenaiLoading(true);
    try {
      const res = await fetch(
        `${apiUrl}/health/azure-openai/test/connectivity`,
        {
          method: 'POST',
        }
      );
      const data = await res.json();
      setOpenaiResponse(data);
    } catch (error) {
      setOpenaiResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setOpenaiLoading(false);
  };

  // Blob Storage関連の関数
  const testBlobStorageHealth = async () => {
    setBlobLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/blob-storage/health`);
      const data = await res.json();
      setBlobResponse(data);
    } catch (error) {
      setBlobResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setBlobLoading(false);
  };

  const testBlobStorageConnectivity = async () => {
    setBlobLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/blob-storage/test-connectivity`, {
        method: 'POST',
      });
      const data = await res.json();
      setBlobResponse(data);
    } catch (error) {
      setBlobResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setBlobLoading(false);
  };

  const uploadFile = async () => {
    if (!selectedFile) {
      setBlobResponse({
        status: 'error',
        error: 'ファイルが選択されていません',
      });
      return;
    }

    setBlobLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('generate_sas', 'true');

      const res = await fetch(`${apiUrl}/api/blob-storage/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setBlobResponse(data);
    } catch (error) {
      setBlobResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setBlobLoading(false);
  };

  const listDocuments = async () => {
    setBlobLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/blob-storage/list`);
      const data = await res.json();
      setBlobResponse(data);
    } catch (error) {
      setBlobResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setBlobLoading(false);
  };

  // Azure AI Search関連の関数
  const testSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResponse({
        status: 'error',
        error: '検索クエリを入力してください',
      });
      return;
    }

    setSearchLoading(true);
    try {
      const res = await fetch(
        `${apiUrl}/search?query=${encodeURIComponent(searchQuery)}`
      );
      const data = await res.json();
      setSearchResponse(data);
    } catch (error) {
      setSearchResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setSearchLoading(false);
  };

  // Real-time Indexing関連の関数
  const testRealtimeIndexing = async () => {
    if (!indexFile) {
      setIndexResponse({
        status: 'error',
        error: 'ファイルが選択されていません',
      });
      return;
    }

    setIndexLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', indexFile);

      const indexType = '01INDEX01TYPE001001001001'; // デフォルトインデックスタイプ
      const res = await fetch(
        `${apiUrl}/index?index_type=${encodeURIComponent(indexType)}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (res.ok) {
        setIndexResponse({
          status: 'success',
          message: 'ファイルのインデックス化が完了しました',
          filename: indexFile.name,
          index_type: '01INDEX01TYPE001001001001',
        });
      } else {
        const errorData = await res.json();
        setIndexResponse({
          status: 'error',
          error: errorData.detail || 'インデックス化に失敗しました',
        });
      }
    } catch (error) {
      setIndexResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setIndexLoading(false);
  };

  // Document Intelligence関連の関数
  const testDocumentIntelligence = async () => {
    if (!docIntelFile) {
      setDocIntelResponse({
        status: 'error',
        error: 'ファイルが選択されていません',
      });
      return;
    }

    setDocIntelLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', docIntelFile);

      const res = await fetch(`${apiUrl}/test/document-intelligence`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setDocIntelResponse(data);
    } catch (error) {
      setDocIntelResponse({
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
    setDocIntelLoading(false);
  };

  const renderResponse = (response: any, title: string) => {
    if (!response) return null;

    return (
      <div className="bg-gray-100 p-4 rounded mt-4">
        <h3 className="font-semibold mb-2">{title}:</h3>
        <div className="flex items-center space-x-2 mb-2">
          <span
            className={`px-2 py-1 rounded text-sm font-medium ${
              response.status === 'success' || response.status === 'healthy'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {response.status}
          </span>
          {response.model && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
              {response.model}
            </span>
          )}
          {response.response_time_ms && (
            <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm">
              {Math.round(response.response_time_ms)}ms
            </span>
          )}
        </div>
        <pre className="text-sm overflow-auto bg-white p-2 rounded border">
          {JSON.stringify(response, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-8 max-w-7xl">
      <h1 className="text-3xl font-bold mb-8 text-center">
        🔬 Azure Services テスト (INFRA-001, INFRA-002, INFRA-003)
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
        {/* Azure OpenAI テスト (INFRA-001) */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 text-blue-600">
            🤖 Azure OpenAI (INFRA-001)
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                テストメッセージ:
              </label>
              <textarea
                value={openaiMessage}
                onChange={e => setOpenaiMessage(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                rows={2}
              />
            </div>

            <div className="flex flex-col space-y-2">
              <button
                onClick={testOpenAIConnectivity}
                disabled={openaiLoading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {openaiLoading ? '実行中...' : '接続テスト'}
              </button>
              <button
                onClick={testOpenAIChat}
                disabled={openaiLoading || !openaiMessage.trim()}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                {openaiLoading ? '実行中...' : 'チャットテスト'}
              </button>
            </div>
          </div>

          {renderResponse(openaiResponse, 'Azure OpenAI 結果')}
        </div>

        {/* Azure Blob Storage テスト (INFRA-003) */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 text-purple-600">
            📁 Azure Blob Storage (INFRA-003)
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                ファイル選択:
              </label>
              <input
                type="file"
                onChange={e => setSelectedFile(e.target.files?.[0] || null)}
                className="w-full p-2 border border-gray-300 rounded"
              />
              {selectedFile && (
                <p className="text-sm text-gray-600 mt-1">
                  選択: {selectedFile.name} (
                  {Math.round(selectedFile.size / 1024)}KB)
                </p>
              )}
            </div>

            <div className="flex flex-col space-y-2">
              <button
                onClick={testBlobStorageHealth}
                disabled={blobLoading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {blobLoading ? '実行中...' : 'ヘルスチェック'}
              </button>
              <button
                onClick={testBlobStorageConnectivity}
                disabled={blobLoading}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                {blobLoading ? '実行中...' : '接続テスト'}
              </button>
              <button
                onClick={uploadFile}
                disabled={blobLoading || !selectedFile}
                className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
              >
                {blobLoading ? '実行中...' : 'ファイルアップロード'}
              </button>
              <button
                onClick={listDocuments}
                disabled={blobLoading}
                className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
              >
                {blobLoading ? '実行中...' : 'ドキュメント一覧'}
              </button>
            </div>
          </div>

          {renderResponse(blobResponse, 'Blob Storage 結果')}
        </div>

        {/* Azure AI Search テスト (INFRA-002) */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 text-green-600">
            🔍 Azure AI Search (INFRA-002)
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                検索クエリ:
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                placeholder="検索したいキーワードを入力"
              />
            </div>

            <div className="flex flex-col space-y-2">
              <button
                onClick={testSearch}
                disabled={searchLoading || !searchQuery.trim()}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                {searchLoading ? '実行中...' : '検索実行'}
              </button>
            </div>
          </div>

          {renderResponse(searchResponse, 'AI Search 結果')}
        </div>

        {/* Real-time Indexing テスト */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 text-blue-600">
            ⚡ リアルタイムインデックス化
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                インデックス化するファイル:
              </label>
              <input
                type="file"
                accept=".pdf,.docx,.pptx,.html,.xlsx,.xls,.xlsm,.png,.jpg,.jpeg"
                onChange={e => setIndexFile(e.target.files?.[0] || null)}
                className="w-full p-2 border border-gray-300 rounded"
              />
              {indexFile && (
                <p className="text-sm text-gray-600 mt-1">
                  選択: {indexFile.name} ({Math.round(indexFile.size / 1024)}KB)
                </p>
              )}
            </div>

            <div className="flex flex-col space-y-2">
              <button
                onClick={testRealtimeIndexing}
                disabled={indexLoading || !indexFile}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {indexLoading ? '処理中...' : '⚡ リアルタイムインデックス化'}
              </button>
            </div>
          </div>

          {renderResponse(indexResponse, 'インデックス化 結果')}
        </div>

        {/* Azure AI Document Intelligence テスト (INFRA-004) */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 text-orange-600">
            📄 Azure AI Document Intelligence (INFRA-004)
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                PDFまたは画像ファイル:
              </label>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={e => setDocIntelFile(e.target.files?.[0] || null)}
                className="w-full p-2 border border-gray-300 rounded"
              />
              {docIntelFile && (
                <p className="text-sm text-gray-600 mt-1">
                  選択: {docIntelFile.name} (
                  {Math.round(docIntelFile.size / 1024)}KB)
                </p>
              )}
            </div>

            <div className="flex flex-col space-y-2">
              <button
                onClick={testDocumentIntelligence}
                disabled={docIntelLoading || !docIntelFile}
                className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
              >
                {docIntelLoading ? '処理中...' : '📄 文書解析テスト'}
              </button>
            </div>
          </div>

          {renderResponse(docIntelResponse, 'Document Intelligence 結果')}
        </div>
      </div>

      {/* 使用方法説明 */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-8">
        <h2 className="text-xl font-semibold mb-4">📋 使用方法</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <h3 className="font-semibold text-blue-600 mb-2">
              🤖 Azure OpenAI
            </h3>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              <li>
                <strong>接続テスト</strong>: Azure OpenAI APIへの基本接続確認
              </li>
              <li>
                <strong>チャットテスト</strong>:
                カスタムメッセージでAI応答テスト
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-purple-600 mb-2">
              📁 Blob Storage
            </h3>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              <li>
                <strong>ヘルスチェック</strong>:
                ストレージアカウントの健康状態確認
              </li>
              <li>
                <strong>接続テスト</strong>: アップロード・削除の総合テスト
              </li>
              <li>
                <strong>ファイルアップロード</strong>:
                実際のファイルアップロード＋SAS URL生成
              </li>
              <li>
                <strong>ドキュメント一覧</strong>: 保存済みファイル一覧表示
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-green-600 mb-2">🔍 AI Search</h3>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              <li>
                <strong>検索実行</strong>: インデックスからのドキュメント検索
              </li>
              <li>
                ハイブリッド検索（キーワード＋ベクター＋セマンティック）対応
              </li>
              <li>日本語解析器（ja.microsoft）使用</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-blue-600 mb-2">
              ⚡ リアルタイムインデックス化
            </h3>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              <li>
                <strong>即座にインデックス化</strong>:
                ファイルアップロード完了と同時に検索可能
              </li>
              <li>
                対応形式: PDF, DOCX, PPTX, HTML, Excel, 画像（PNG, JPG, JPEG）
              </li>
              <li>
                テキスト抽出 → 埋め込みベクター生成 → インデックス登録を自動実行
              </li>
              <li>keywords フィールド: マークダウンヘッダーから自動抽出</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-orange-600 mb-2">
              📄 Document Intelligence
            </h3>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              <li>
                <strong>文書解析テスト</strong>: PDF・画像からテキスト抽出
              </li>
              <li>レイアウト認識と構造化マークダウン変換</li>
              <li>対応形式: PDF, PNG, JPG, JPEG</li>
              <li>OCR機能で手書き・印刷文字を認識</li>
              <li>日本語文書の高精度解析</li>
            </ul>
          </div>
        </div>

        <div className="mt-4 p-4 bg-yellow-50 rounded">
          <h3 className="font-semibold text-yellow-800 mb-2">⚠️ 注意事項:</h3>
          <ul className="text-yellow-700 text-sm space-y-1">
            <li>• このページは開発・テスト専用です</li>
            <li>• 本番環境では適切なアクセス制御を実装してください</li>
            <li>
              • アップロードしたファイルは実際にAzure Blob Storageに保存されます
            </li>
            <li>• SAS URLは24時間有効です</li>
            <li>• リアルタイムインデックス化は即座に検索可能になります</li>
            <li>• ファイルサイズが大きい場合は処理時間がかかります</li>
            <li>• Document Intelligenceは高精度なPDF・画像解析を提供します</li>
            <li>• 処理時間はファイルサイズと複雑さに依存します</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
