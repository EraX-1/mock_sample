'use client';

import DocViewer, {
  CSVRenderer,
  IDocument,
  JPGRenderer,
  MSDocRenderer,
  PDFRenderer,
  PNGRenderer,
  TXTRenderer,
} from '@cyntler/react-doc-viewer';

import { Alert, Box, CircularProgress, Typography } from '@mui/material';
import { memo, useEffect, useState } from 'react';
import styles from './file-previewer.module.css';

type Props = {
  fileType: 'pdf' | 'xls' | 'xlsx' | 'xlsm';
  url: string;
  customStyle?: React.CSSProperties;
};

type LoadingState = 'loading' | 'loaded' | 'error' | 'timeout';

const FilePreviewer = memo(
  ({ fileType: _fileType, url: _url, customStyle }: Props) => {
    const [documents, setDocuments] = useState<IDocument[]>([]);
    const [loadingState, setLoadingState] = useState<LoadingState>('loading');
    const [errorMessage, setErrorMessage] = useState<string>('');

    useEffect(() => {
      setLoadingState('loading');
      setErrorMessage('');

      // URLの有効性をチェック
      if (!_url || _url.trim() === '') {
        setLoadingState('error');
        setErrorMessage('ファイルURLが無効です');
        return;
      }

      console.log('FilePreviewer: Loading file', {
        fileType: _fileType,
        url: _url,
      });

      // タイムアウト設定（30秒）
      const timeoutId = setTimeout(() => {
        setLoadingState('timeout');
        setErrorMessage(
          'ファイルの読み込みがタイムアウトしました。ファイルサイズが大きいか、ネットワークに問題がある可能性があります。'
        );
      }, 30000);

      // ファイルの存在確認
      fetch(_url, { method: 'HEAD' })
        .then(response => {
          clearTimeout(timeoutId);
          if (!response.ok) {
            throw new Error(
              `ファイルが見つかりません (${response.status}): ${response.statusText}`
            );
          }
          setDocuments([{ uri: _url, fileType: _fileType }]);
          setLoadingState('loaded');
        })
        .catch(error => {
          clearTimeout(timeoutId);
          console.error('FilePreviewer: Failed to load file', error);
          setLoadingState('error');
          setErrorMessage(`ファイルの読み込みに失敗しました: ${error.message}`);
        });

      return () => {
        clearTimeout(timeoutId);
      };
    }, [_fileType, _url]);

    if (loadingState === 'loading') {
      return (
        <Box
          className={styles.wrapper}
          style={customStyle}
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '400px',
            gap: 2,
          }}
        >
          <CircularProgress size={40} />
          <Typography variant="body2" color="text.secondary">
            ファイルを読み込んでいます...
          </Typography>
        </Box>
      );
    }

    if (loadingState === 'error' || loadingState === 'timeout') {
      return (
        <Box className={styles.wrapper} style={customStyle}>
          <Alert
            severity="error"
            sx={{ m: 2 }}
            action={
              <Typography
                variant="body2"
                sx={{ cursor: 'pointer', textDecoration: 'underline' }}
                onClick={() => window.location.reload()}
              >
                再試行
              </Typography>
            }
          >
            <Typography variant="body2">{errorMessage}</Typography>
            <Typography
              variant="caption"
              display="block"
              sx={{ mt: 1, opacity: 0.7 }}
            >
              URL: {_url}
            </Typography>
          </Alert>
        </Box>
      );
    }

    if (documents.length === 0) {
      return <></>;
    }

    return (
      <div className={styles.wrapper} style={customStyle}>
        <DocViewer
          pluginRenderers={[
            PDFRenderer,
            JPGRenderer,
            PNGRenderer,
            TXTRenderer,
            MSDocRenderer,
            CSVRenderer,
          ]}
          documents={documents}
          activeDocument={{ uri: _url, fileType: _fileType }}
          config={{
            pdfVerticalScrollByDefault: true,
            loadingRenderer: {
              overrideComponent: () => (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '200px',
                    gap: 2,
                  }}
                >
                  <CircularProgress size={30} />
                  <Typography variant="body2" color="text.secondary">
                    PDFを読み込んでいます...
                  </Typography>
                </Box>
              ),
            },
          }}
        />
      </div>
    );
  }
);

FilePreviewer.displayName = 'FilePreviewer';

export default FilePreviewer;
