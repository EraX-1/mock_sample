'use client';

import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  CircularProgress,
} from '@mui/material';
import { useRouter } from 'next/navigation';
import { getMaintenanceStatusApi } from '@/services/apiService';

export default function Maintenance() {
  const [message, setMessage] = useState<string>('');
  const [checking, setChecking] = useState<boolean>(false);
  const router = useRouter();

  // URLからメッセージを取得
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlMessage = urlParams.get('message');
    if (urlMessage) {
      setMessage(decodeURIComponent(urlMessage));
    }
  }, []);

  // メンテナンス状態を確認する関数
  const checkMaintenanceStatus = async () => {
    setChecking(true);
    try {
      const { response, error } = await getMaintenanceStatusApi();

      if (error) {
        console.error('メンテナンス状態の確認中にエラーが発生しました:', error);
        return;
      }

      // メンテナンスが解除されていればサインアップページにリダイレクト
      if (!response?.maintenance) {
        router.push('/signin');
      } else {
        // メンテナンス中の場合はメッセージを更新
        if (response.message) {
          setMessage(response.message);
        }
        alert(
          'まだメンテナンス中です。しばらくしてからもう一度お試しください。'
        );
      }
    } catch (error) {
      console.error('メンテナンス状態の確認中に例外が発生しました:', error);
    } finally {
      setChecking(false);
    }
  };

  // ページロード時にもメンテナンス状態を確認
  useEffect(() => {
    const checkOnLoad = async () => {
      try {
        const { response, error } = await getMaintenanceStatusApi();

        if (error) {
          console.error(
            '初期メンテナンス状態の確認中にエラーが発生しました:',
            error
          );
          return;
        }

        // メンテナンスが解除されていればサインアップページにリダイレクト
        if (!response?.maintenance) {
          router.push('/signin');
        }
      } catch (error) {
        console.error(
          '初期メンテナンス状態の確認中に例外が発生しました:',
          error
        );
      }
    };

    checkOnLoad();
  }, [router]);

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          py: 5,
        }}
      >
        <Typography variant="h2" component="h1" gutterBottom align="center">
          メンテナンス中
        </Typography>

        <Paper
          elevation={3}
          sx={{
            p: 4,
            my: 4,
            width: '100%',
            borderRadius: 2,
          }}
        >
          <Typography variant="body1" paragraph>
            {message || 'システムメンテナンス中です。しばらくお待ちください。'}
          </Typography>
        </Paper>

        <Typography
          variant="h6"
          align="center"
          color="text.secondary"
          sx={{ mb: 4 }}
        >
          ご不便をおかけして申し訳ありません。
          <br />
          しばらく経ってから再度アクセスしてください。
        </Typography>

        <Button
          variant="contained"
          color="primary"
          onClick={checkMaintenanceStatus}
          disabled={checking}
          startIcon={
            checking ? <CircularProgress size={20} color="inherit" /> : null
          }
        >
          {checking ? '読み込み中...' : '再読み込み'}
        </Button>
      </Box>
    </Container>
  );
}
