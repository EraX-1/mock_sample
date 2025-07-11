'use client';

import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Card as TremorCard,
  Text,
  Title,
  Grid,
  List,
  ListItem,
  Flex,
  Badge,
  Metric,
} from '@tremor/react';
import {
  getAdminDashboardApi,
  getUserInfoApi,
  updateUserRoleApi,
  getSearchIndexTypesApi,
  updateSearchIndexTypeApi,
  reorderSearchIndexTypesApi,
  uploadAndIndexFileApi,
  getUploadedFilesApi,
  deleteFileApi,
  getIndexedFilesApi,
} from '@/services/apiService';
import { FC } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Button,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  TextField,
} from '@mui/material';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { notFound, useRouter } from 'next/navigation';
import Link from 'next/link';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import ReorderIcon from '@mui/icons-material/Reorder';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { LinearProgress, Chip, Alert } from '@mui/material';

const DemoChatDashboard: React.FC = () => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);
  const [data, setData] = useState<{
    last24hChatCount: number;
    last7daysChatCount: number;
    last7daysTransition: any[];
    latestChatList: any[];
    userList: any[];
  }>({
    last24hChatCount: 0,
    last7daysChatCount: 0,
    last7daysTransition: [],
    latestChatList: [],
    userList: [],
  });

  const [isUpdatingRole, setIsUpdatingRole] = useState<string | null>(null);
  const [roleUpdateSuccess, setRoleUpdateSuccess] = useState<boolean>(false);

  // モーダル関連のステートを追加
  const [openModal, setOpenModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [newRole, setNewRole] = useState<string>('');
  const [isRoleChanged, setIsRoleChanged] = useState(false);

  // 検索インデックス関連のステートを追加
  const [searchIndexTypes, setSearchIndexTypes] = useState<any[]>([]);
  const [editingIndexId, setEditingIndexId] = useState<string | null>(null);
  const [editingIndexName, setEditingIndexName] = useState<string>('');
  const [indexUpdateSuccess, setIndexUpdateSuccess] = useState<boolean>(false);

  // ドキュメント管理関連のステートを追加
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [indexedFiles, setIndexedFiles] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [selectedIndexType, setSelectedIndexType] = useState<string>('');

  useEffect(() => {
    (async () => {
      try {
        // まずユーザー情報を取得して管理者かどうかを確認
        const { response: userInfo, error: userError } = await getUserInfoApi();

        // ユーザー情報の取得に失敗した場合（未ログイン）はログイン画面にリダイレクト
        if (userError || !userInfo) {
          router.push('/signin');
          return;
        }

        // ログイン済みだが管理者でない場合もログイン画面にリダイレクト
        if (userInfo.role !== 'admin') {
          router.push('/signin');
          return;
        }

        // 管理者権限があることを確認
        setIsAdmin(true);

        // 管理者の場合はダッシュボードデータを取得
        const { response, error } = await getAdminDashboardApi();

        if (error) {
          console.error('管理者ダッシュボードの取得に失敗しました:', error);
          setIsLoading(false);
          return;
        }

        let last7daysChatCount = 0;
        response.last_7days_transition.map((item: any, index: number) => {
          last7daysChatCount += item.chat_count;
          return index;
        });

        const builtData = {
          last24hChatCount: response.last_24h_chat_count,
          last7daysChatCount: last7daysChatCount,
          last7daysTransition: response.last_7days_transition.map(
            (item: any, index: number) => {
              return {
                date: item.date,
                chat_count: item.chat_count,
                token_usage: item.token_usage || 0,
                key: `transition-${index}`,
              };
            }
          ),
          latestChatList: response.latest_chat_list,
          userList: response.user_list.map((user: any) => {
            return {
              id: user.id,
              email: user.email,
              created_at: user.created_at,
              role: user.role,
            };
          }),
        };
        setData(builtData);
        setIsLoading(false);

        // 検索インデックス一覧を取得
        const { response: indexTypes, error: indexError } =
          await getSearchIndexTypesApi();
        if (indexError) {
          console.error(
            '検索インデックス一覧の取得に失敗しました:',
            indexError
          );
        } else if (indexTypes) {
          setSearchIndexTypes(indexTypes);
          // 最初のインデックスタイプをデフォルトとして選択
          if (indexTypes.length > 0) {
            setSelectedIndexType(indexTypes[0].id);
          }
        }

        // アップロード済みファイル一覧を取得
        const { response: uploadedFilesData, error: uploadedFilesError } =
          await getUploadedFilesApi();
        if (uploadedFilesError) {
          console.error(
            'アップロード済みファイル一覧の取得に失敗しました:',
            uploadedFilesError
          );
        } else if (uploadedFilesData) {
          console.log('Uploaded files data:', uploadedFilesData);
          setUploadedFiles(uploadedFilesData.documents || []);
        }

        // インデックス済みファイル一覧を取得
        const { response: indexedFilesData, error: indexedFilesError } =
          await getIndexedFilesApi();
        if (indexedFilesError) {
          console.error(
            'インデックス済みファイル一覧の取得に失敗しました:',
            indexedFilesError
          );
        } else if (indexedFilesData) {
          console.log('Indexed files data:', indexedFilesData);
          setIndexedFiles(indexedFilesData || []);
          console.log('Set indexedFiles state to:', indexedFilesData);
        }
      } catch (err) {
        console.error('エラーが発生しました:', err);
        // エラーが発生した場合もログイン画面にリダイレクト
        router.push('/signin');
      }
    })();
  }, [router]);

  // モーダルを開く関数
  const handleOpenModal = (user: any) => {
    setSelectedUser(user);
    setNewRole(user.role);
    setIsRoleChanged(false);
    setOpenModal(true);
  };

  // モーダルを閉じる関数
  const handleCloseModal = () => {
    setOpenModal(false);
    setSelectedUser(null);
    setNewRole('');
  };

  // 権限変更時の処理
  const handleRoleChange = (event: any) => {
    const role = event.target.value as string;
    setNewRole(role);
    setIsRoleChanged(role !== selectedUser?.role);
  };

  // 権限変更を確定する関数
  const handleConfirmRoleChange = async () => {
    if (!selectedUser || !isRoleChanged) return;

    setIsUpdatingRole(selectedUser.id);

    const { response, error } = await updateUserRoleApi({
      user_id: selectedUser.id,
      role: newRole,
    });

    if (error) {
      console.error('権限の更新に失敗しました:', error);
    } else {
      // 成功したら、データを更新
      setData(prevData => ({
        ...prevData,
        userList: prevData.userList.map((user: any) =>
          user.id === selectedUser.id ? { ...user, role: newRole } : user
        ) as any[],
      }));
      setRoleUpdateSuccess(true);

      // 3秒後に成功メッセージを消す
      setTimeout(() => {
        setRoleUpdateSuccess(false);
      }, 3000);
    }

    setIsUpdatingRole(null);
    handleCloseModal();
  };

  // 編集モードを開始する関数
  const handleStartEdit = (indexType: any) => {
    setEditingIndexId(indexType.id);
    setEditingIndexName(indexType.folder_name);
  };

  // 編集をキャンセルする関数
  const handleCancelEdit = () => {
    setEditingIndexId(null);
    setEditingIndexName('');
  };

  // 編集を保存する関数
  const handleSaveEdit = async (indexTypeId: string) => {
    const { response, error } = await updateSearchIndexTypeApi({
      index_type_id: indexTypeId,
      folder_name: editingIndexName,
    });

    if (error) {
      console.error('インデックス名の更新に失敗しました:', error);
    } else {
      // 成功したら、データを更新
      setSearchIndexTypes(prevTypes =>
        prevTypes.map(type =>
          type.id === indexTypeId
            ? { ...type, folder_name: editingIndexName }
            : type
        )
      );
      setIndexUpdateSuccess(true);

      // 3秒後に成功メッセージを消す
      setTimeout(() => {
        setIndexUpdateSuccess(false);
      }, 3000);
    }

    setEditingIndexId(null);
  };

  // ドラッグ&ドロップの処理関数を修正
  const handleReorder = async (
    indexTypeId: string,
    direction: 'up' | 'down'
  ) => {
    const currentIndex = searchIndexTypes.findIndex(
      item => item.id === indexTypeId
    );
    if (
      (direction === 'up' && currentIndex <= 0) ||
      (direction === 'down' && currentIndex >= searchIndexTypes.length - 1)
    ) {
      return; // 移動できない場合は何もしない
    }

    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    const items = Array.from(searchIndexTypes);
    const [reorderedItem] = items.splice(currentIndex, 1);
    items.splice(newIndex, 0, reorderedItem);

    setSearchIndexTypes(items);

    // APIを呼び出して順序を保存
    const { response, error } = await reorderSearchIndexTypesApi({
      index_type_ids: items.map(item => item.id),
    });

    if (error) {
      console.error('インデックス順序の更新に失敗しました:', error);
    }
  };

  // ファイル選択ハンドラー
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setSelectedFiles(files);
      setUploadError(null);
    }
  };

  // ファイルアップロードハンドラー
  const handleFileUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setUploadError('ファイルを選択してください');
      return;
    }

    if (!selectedIndexType) {
      setUploadError('インデックスタイプを選択してください');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(0);

    try {
      const uploadPromises = Array.from(selectedFiles).map(
        async (file, index) => {
          const { response, error } = await uploadAndIndexFileApi(
            file,
            selectedIndexType
          );

          if (error) {
            throw new Error(
              `ファイル "${file.name}" のアップロードに失敗しました: ${error}`
            );
          }

          // プログレスを更新
          setUploadProgress(((index + 1) / selectedFiles.length) * 100);
          return response;
        }
      );

      await Promise.all(uploadPromises);

      setUploadSuccess(true);
      setSelectedFiles(null);

      // ファイル一覧を再取得
      const { response: uploadedFilesData } = await getUploadedFilesApi();
      if (uploadedFilesData) {
        setUploadedFiles(uploadedFilesData.documents || []);
      }

      const { response: indexedFilesData } = await getIndexedFilesApi();
      if (indexedFilesData) {
        setIndexedFiles(indexedFilesData || []);
      }

      // 成功メッセージを3秒後に消す
      setTimeout(() => {
        setUploadSuccess(false);
      }, 3000);

      // ファイル入力をリセット
      const fileInput = document.getElementById(
        'file-upload-input'
      ) as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    } catch (error) {
      setUploadError(
        error instanceof Error ? error.message : 'アップロードに失敗しました'
      );
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // ファイル削除ハンドラー
  const handleFileDelete = async (blobName: string) => {
    if (!confirm(`ファイル "${blobName}" を削除しますか？`)) {
      return;
    }

    try {
      const { response, error } = await deleteFileApi(blobName);

      if (error) {
        alert(`ファイルの削除に失敗しました: ${error}`);
        return;
      }

      // ファイル一覧を再取得
      const { response: uploadedFilesData } = await getUploadedFilesApi();
      if (uploadedFilesData) {
        setUploadedFiles(uploadedFilesData.documents || []);
      }

      const { response: indexedFilesData } = await getIndexedFilesApi();
      if (indexedFilesData) {
        setIndexedFiles(indexedFilesData || []);
      }
    } catch (error) {
      alert('ファイルの削除に失敗しました');
    }
  };

  // ローディング中は何も表示しない（リダイレクト処理中も含む）
  if (isLoading || isAdmin === null) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="p-8 space-y-6 bg-white rounded-lg">
          <h2 className="text-xl font-bold text-center mb-12">認証確認中...</h2>
        </div>
      </div>
    );
  }

  // 以下、ダッシュボード表示コード
  return (
    <div className="min-h-screen bg-gradient-to-r from-gray-100 to-gray-200 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 戻るボタン (MUI版) */}
        <Box sx={{ mb: 3 }}>
          <Link href="/chat" passHref style={{ textDecoration: 'none' }}>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<ArrowBackIcon />}
              sx={{
                borderRadius: '8px',
                textTransform: 'none',
                fontWeight: 500,
              }}
            >
              チャットページに戻る
            </Button>
          </Link>
        </Box>

        {/* ヘッダー */}
        <div className="mb-8 text-center">
          <Title className="text-3xl font-bold mb-2">
            管理者ダッシュボード
          </Title>
          <Text className="text-gray-700">チャットの統計情報</Text>
        </div>

        {/* メトリクスカード */}
        <Grid numItems={1} numItemsSm={2} numItemsLg={2} className="gap-8 mb-8">
          <TremorCard className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <Flex alignItems="start" className="justify-between">
              <div>
                <Text className="text-gray-600">直近24時間</Text>
                <Metric className="mt-2 text-3xl font-semibold">
                  {data.last24hChatCount}
                </Metric>
              </div>
              <Badge
                size="xl"
                className="bg-blue-100 text-blue-700 rounded-full px-3 py-1"
              >
                24h
              </Badge>
            </Flex>
          </TremorCard>

          <TremorCard className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300 mt-2">
            <Flex alignItems="start" className="justify-between">
              <div>
                <Text className="text-gray-600">直近7日間</Text>
                <Metric className="mt-2 text-3xl font-semibold">
                  {data.last7daysChatCount}
                </Metric>
              </div>
              <Badge
                size="xl"
                className="bg-green-100 text-green-700 rounded-full px-3 py-1"
              >
                7d
              </Badge>
            </Flex>
          </TremorCard>
        </Grid>

        {/* チャート＆チャット履歴 */}
        <Grid numItems={1} numItemsLg={2} className="gap-8">
          {/* 二軸バーチャートエリア */}
          <TremorCard className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <Title className="text-xl font-semibold">
              チャット数・トークン使用量推移
            </Title>
            <Text className="mt-1 text-gray-600">直近7日間の推移</Text>
            <div style={{ width: '100%', height: 300 }} className="mt-4">
              <ResponsiveContainer>
                <ComposedChart data={data.last7daysTransition}>
                  <defs>
                    <linearGradient
                      id="chatGradient"
                      key="chatGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.8} />
                      <stop
                        offset="95%"
                        stopColor="#2563eb"
                        stopOpacity={0.2}
                      />
                    </linearGradient>
                    <linearGradient
                      id="tokenGradient"
                      key="tokenGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset="5%" stopColor="#16a34a" stopOpacity={0.8} />
                      <stop
                        offset="95%"
                        stopColor="#16a34a"
                        stopOpacity={0.2}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    stroke="#f0f0f0"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#666', fontSize: 12 }}
                    tickLine={false}
                    axisLine={{ stroke: '#eee' }}
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fill: '#666', fontSize: 12 }}
                    tickLine={false}
                    axisLine={{ stroke: '#eee' }}
                    tickFormatter={value => `${value}件`}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fill: '#666', fontSize: 12 }}
                    tickLine={false}
                    axisLine={{ stroke: '#eee' }}
                    tickFormatter={value => `${value.toLocaleString()}T`}
                  />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg shadow-lg p-4">
                            <p
                              className="text-gray-600 font-medium mb-2"
                              key="tooltip-label"
                            >
                              {label}
                            </p>
                            {payload.map((entry, index) => (
                              <p
                                key={`tooltip-value-${index}`}
                                className={
                                  entry.name === 'チャット数'
                                    ? 'text-blue-600 font-medium'
                                    : 'text-green-600 font-medium'
                                }
                              >
                                {entry.name}: {entry.value}
                                {entry.name === 'チャット数' ? '件' : ''}
                              </p>
                            ))}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend
                    verticalAlign="top"
                    height={36}
                    iconType="circle"
                    iconSize={10}
                    wrapperStyle={{
                      paddingBottom: '20px',
                    }}
                  />
                  <Bar
                    yAxisId="left"
                    dataKey="chat_count"
                    name="チャット数"
                    fill="url(#chatGradient)"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={50}
                    animationBegin={200}
                    animationDuration={1000}
                  />
                  <Bar
                    yAxisId="right"
                    dataKey="token_usage"
                    name="トークン使用量"
                    fill="url(#tokenGradient)"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={50}
                    animationBegin={400}
                    animationDuration={1000}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </TremorCard>

          {/* チャット履歴エリア */}
          <TremorCard className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300 mt-2">
            <Flex className="justify-between items-center">
              <Title className="text-xl font-semibold">
                最近のチャット(最大20件)
              </Title>
              <Badge className="bg-blue-100 text-blue-700 rounded-full px-3 py-1">
                {data.latestChatList.length}件
              </Badge>
            </Flex>
            <List className="mt-4 space-y-4">
              {data.latestChatList.map((chat: any, index) => (
                <ListItem
                  key={chat.id || `chat-${index}`}
                  className="bg-gray-50 p-4 rounded-lg shadow-sm"
                >
                  <Flex className="justify-between items-start">
                    <div className="flex-1">
                      <Text className="font-medium text-gray-800">
                        {chat.message}
                      </Text>
                      <Text className="text-xs text-gray-500 mt-1">
                        {new Date(chat.created_at).toLocaleString()}
                      </Text>
                    </div>
                    {/* <Badge
                      color="green"
                      size="sm"
                      className="rounded-full px-2 py-1"
                    >
                      {chat.status}
                    </Badge> */}
                  </Flex>
                  {/* <Text className="text-gray-700 mt-3">{chat.answer}</Text> */}
                </ListItem>
              ))}
            </List>
          </TremorCard>
        </Grid>

        {/* ユーザー一覧セクション */}
        <div className="mt-8">
          <TremorCard className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <Flex className="justify-between items-center mb-4">
              <Title className="text-xl font-semibold">ユーザー一覧</Title>
              <Badge className="bg-blue-100 text-blue-700 rounded-full px-3 py-1">
                {data.userList.length}件
              </Badge>
            </Flex>
            {roleUpdateSuccess && (
              <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg flex items-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                ユーザー権限を更新しました
              </div>
            )}
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>メールアドレス</TableCell>
                    <TableCell>作成日時</TableCell>
                    <TableCell>現在の権限</TableCell>
                    <TableCell>操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.userList.map((user: any) => (
                    <TableRow key={user.id}>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        {new Date(user.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge
                          color={user.role === 'admin' ? 'blue' : 'gray'}
                          size="sm"
                          className={`rounded-full px-2 py-1 ${
                            user.role === 'admin'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {user.role === 'admin' ? '管理者' : '一般ユーザー'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outlined"
                          color="primary"
                          size="small"
                          onClick={() => handleOpenModal(user)}
                          sx={{
                            borderRadius: '8px',
                            textTransform: 'none',
                          }}
                        >
                          権限を変更
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TremorCard>
        </div>

        {/* 検索インデックス管理セクション */}
        <div className="mt-8">
          <TremorCard className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <Flex className="justify-between items-center mb-4">
              <Title className="text-xl font-semibold">参照元管理</Title>
              <Badge className="bg-blue-100 text-blue-700 rounded-full px-3 py-1">
                {searchIndexTypes.length}件
              </Badge>
            </Flex>

            {indexUpdateSuccess && (
              <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg flex items-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                参照元名を更新しました
              </div>
            )}

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell width="10%">順序</TableCell>
                    <TableCell width="40%">参照元名</TableCell>
                    <TableCell width="35%">ID</TableCell>
                    <TableCell width="15%">操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {searchIndexTypes.map((indexType, index) => (
                    <TableRow key={indexType.id}>
                      <TableCell>
                        <Flex>
                          <Button
                            size="small"
                            disabled={index === 0}
                            onClick={() => handleReorder(indexType.id, 'up')}
                            sx={{ minWidth: '30px', p: 0 }}
                          >
                            ↑
                          </Button>
                          <Button
                            size="small"
                            disabled={index === searchIndexTypes.length - 1}
                            onClick={() => handleReorder(indexType.id, 'down')}
                            sx={{ minWidth: '30px', p: 0 }}
                          >
                            ↓
                          </Button>
                        </Flex>
                      </TableCell>
                      <TableCell>
                        {editingIndexId === indexType.id ? (
                          <TextField
                            fullWidth
                            size="small"
                            value={editingIndexName}
                            onChange={e => setEditingIndexName(e.target.value)}
                            autoFocus
                          />
                        ) : (
                          indexType.folder_name
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="textSecondary">
                          {indexType.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {editingIndexId === indexType.id ? (
                          <Flex>
                            <Button
                              variant="contained"
                              color="primary"
                              size="small"
                              startIcon={<SaveIcon />}
                              onClick={() => handleSaveEdit(indexType.id)}
                              sx={{
                                borderRadius: '8px',
                                textTransform: 'none',
                                mr: 1,
                              }}
                            >
                              保存
                            </Button>
                            <Button
                              variant="outlined"
                              color="inherit"
                              size="small"
                              startIcon={<CancelIcon />}
                              onClick={handleCancelEdit}
                              sx={{
                                borderRadius: '8px',
                                textTransform: 'none',
                              }}
                            >
                              キャンセル
                            </Button>
                          </Flex>
                        ) : (
                          <Button
                            variant="outlined"
                            color="primary"
                            size="small"
                            startIcon={<EditIcon />}
                            onClick={() => handleStartEdit(indexType)}
                            sx={{
                              borderRadius: '8px',
                              textTransform: 'none',
                            }}
                          >
                            編集
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="body2" color="textSecondary" className="mt-4">
              ※上下ボタンで表示順序を変更できます。変更は即時に反映されます。
            </Typography>
          </TremorCard>
        </div>

        {/* ドキュメント管理セクション */}
        <div className="mt-8">
          <TremorCard className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <Flex className="justify-between items-center mb-4">
              <Title className="text-xl font-semibold">ドキュメント管理</Title>
              <Badge className="bg-purple-100 text-purple-700 rounded-full px-3 py-1">
                アップロード済み: {uploadedFiles.length}件
              </Badge>
            </Flex>

            {/* 成功・エラーメッセージ */}
            {uploadSuccess && (
              <Alert severity="success" className="mb-4">
                ファイルのアップロードとインデックス化が完了しました
              </Alert>
            )}

            {uploadError && (
              <Alert severity="error" className="mb-4">
                {uploadError}
              </Alert>
            )}

            {/* ファイルアップロードエリア */}
            <Box className="mb-6">
              <Typography variant="h6" className="mb-3">
                新しいドキュメントをアップロード
              </Typography>

              <Box className="border-2 border-dashed border-gray-300 rounded-lg p-6 mb-4 text-center bg-gray-50">
                <CloudUploadIcon sx={{ fontSize: 48, color: 'gray', mb: 2 }} />
                <Typography variant="body1" className="mb-2">
                  ファイルを選択してアップロード
                </Typography>
                <Typography
                  variant="body2"
                  color="textSecondary"
                  className="mb-3"
                >
                  対応形式: PDF, DOCX, PPTX, Excel, HTML, 画像 (PNG, JPG)
                </Typography>

                <input
                  id="file-upload-input"
                  type="file"
                  multiple
                  accept=".pdf,.docx,.pptx,.xlsx,.xls,.html,.htm,.png,.jpg,.jpeg"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <label htmlFor="file-upload-input">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<CloudUploadIcon />}
                    sx={{ mr: 2 }}
                  >
                    ファイルを選択
                  </Button>
                </label>

                {selectedFiles && selectedFiles.length > 0 && (
                  <Box className="mt-3">
                    <Typography variant="body2">
                      選択済み: {selectedFiles.length}ファイル
                    </Typography>
                    <Box className="flex flex-wrap gap-2 mt-2">
                      {Array.from(selectedFiles).map((file, index) => (
                        <Chip key={index} label={file.name} size="small" />
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>

              <Box className="flex items-center gap-4 mb-4">
                <FormControl size="small" sx={{ minWidth: 200 }}>
                  <InputLabel>インデックスタイプ</InputLabel>
                  <Select
                    value={selectedIndexType}
                    onChange={e => setSelectedIndexType(e.target.value)}
                    label="インデックスタイプ"
                  >
                    {searchIndexTypes.map(indexType => (
                      <MenuItem key={indexType.id} value={indexType.id}>
                        {indexType.folder_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleFileUpload}
                  disabled={
                    isUploading || !selectedFiles || selectedFiles.length === 0
                  }
                  startIcon={<CloudUploadIcon />}
                  sx={{ borderRadius: '8px', textTransform: 'none' }}
                >
                  {isUploading ? 'アップロード中...' : 'アップロード開始'}
                </Button>
              </Box>

              {/* アップロード進行状況 */}
              {isUploading && (
                <Box className="mb-4">
                  <Typography variant="body2" className="mb-1">
                    アップロード進行状況: {Math.round(uploadProgress)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={uploadProgress}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              )}
            </Box>

            {/* アップロード済みファイル一覧 */}
            <Typography variant="h6" className="mb-3">
              アップロード済みドキュメント一覧
            </Typography>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ファイル名</TableCell>
                    <TableCell>アップロード日時</TableCell>
                    <TableCell>インデックス状態</TableCell>
                    <TableCell>操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {uploadedFiles.map((file: any) => {
                    // ファイル名からタイムスタンプを除去する関数
                    const removeTimestampFromFilename = (
                      filename: string
                    ): string => {
                      // 20250124_123456_filename.pdf のようなパターンからfilename.pdfを抽出
                      const match = filename.match(/^\d{8}_\d{6}_(.+)$/);
                      return match ? match[1] : filename;
                    };

                    // フロントエンドのファイル名（タイムスタンプ付き）からタイムスタンプを除去
                    const cleanFileName = removeTimestampFromFilename(
                      file.name
                    );

                    // データベースのファイル名も同様にクリーンアップして比較
                    const isIndexed = indexedFiles.some((indexedFile: any) => {
                      const cleanIndexedName = removeTimestampFromFilename(
                        indexedFile.original_blob_name
                      );
                      return (
                        cleanIndexedName === cleanFileName ||
                        indexedFile.original_blob_name === file.name
                      );
                    });

                    // デバッグ情報を出力
                    console.log('File check:', {
                      fileName: file.name,
                      cleanFileName,
                      isIndexed,
                      indexedFiles: indexedFiles.map(f => ({
                        original: f.original_blob_name,
                        clean: removeTimestampFromFilename(
                          f.original_blob_name
                        ),
                      })),
                      matchingIndexedFile: indexedFiles.find(
                        f =>
                          removeTimestampFromFilename(f.original_blob_name) ===
                            cleanFileName || f.original_blob_name === file.name
                      ),
                    });

                    return (
                      <TableRow key={file.name}>
                        <TableCell>
                          <Typography variant="body2">{file.name}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(file.last_modified).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={
                              isIndexed ? <CheckCircleIcon /> : <ErrorIcon />
                            }
                            label={
                              isIndexed ? 'インデックス済み' : '未インデックス'
                            }
                            color={isIndexed ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="outlined"
                            color="error"
                            size="small"
                            startIcon={<DeleteIcon />}
                            onClick={() => handleFileDelete(file.name)}
                            sx={{
                              borderRadius: '8px',
                              textTransform: 'none',
                            }}
                          >
                            削除
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {uploadedFiles.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} align="center">
                        <Typography variant="body2" color="textSecondary">
                          アップロード済みファイルがありません
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="body2" color="textSecondary" className="mt-4">
              ※ファイルアップロード後、自動的にAzure AI
              Searchでインデックス化されます。
            </Typography>
          </TremorCard>
        </div>

        {/* 権限変更モーダル */}
        <Dialog
          open={openModal}
          onClose={handleCloseModal}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>ユーザー権限の変更</DialogTitle>
          <DialogContent>
            {selectedUser && (
              <div className="py-4">
                <div className="mb-4">
                  <Typography variant="subtitle1" className="font-medium">
                    ユーザー情報
                  </Typography>
                  <Typography variant="body2" className="mt-1">
                    メールアドレス: {selectedUser.email}
                  </Typography>
                  <Typography variant="body2" className="mt-1">
                    現在の権限:{' '}
                    {selectedUser.role === 'admin' ? '管理者' : '一般ユーザー'}
                  </Typography>
                </div>

                <FormControl fullWidth variant="outlined" className="mt-4">
                  <InputLabel>新しい権限</InputLabel>
                  <Select
                    value={newRole}
                    onChange={e => handleRoleChange(e)}
                    label="新しい権限"
                  >
                    <MenuItem value="user">一般ユーザー</MenuItem>
                    <MenuItem value="admin">管理者</MenuItem>
                  </Select>
                  <FormHelperText>
                    権限の変更は次回ログイン時から有効になります。
                  </FormHelperText>
                </FormControl>
              </div>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseModal} color="inherit">
              キャンセル
            </Button>
            <Button
              onClick={handleConfirmRoleChange}
              color="primary"
              variant="contained"
              disabled={!isRoleChanged || isUpdatingRole === selectedUser?.id}
              sx={{
                borderRadius: '8px',
                textTransform: 'none',
              }}
            >
              {isUpdatingRole === selectedUser?.id ? '更新中...' : '変更を確定'}
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    </div>
  );
};

export default DemoChatDashboard;
