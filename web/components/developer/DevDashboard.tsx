'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Grid,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  BugReport as BugReportIcon,
  Accessibility as AccessibilityIcon,
  Analytics as AnalyticsIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

interface PerformanceMetrics {
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  bundleSize: number;
  memoryUsage: number;
  accessibilityScore: number;
}

interface OptimizationSuggestion {
  type: 'performance' | 'accessibility' | 'bundle' | 'memory';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  code?: string;
}

const DevDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    lcp: 0,
    fid: 0,
    cls: 0,
    bundleSize: 0,
    memoryUsage: 0,
    accessibilityScore: 0,
  });

  const [suggestions, setSuggestions] = useState<OptimizationSuggestion[]>([]);
  const [isCollecting, setIsCollecting] = useState(false);

  const collectMetrics = useCallback(async () => {
    setIsCollecting(true);

    try {
      // Core Web Vitals収集
      const navigation = performance.getEntriesByType(
        'navigation'
      )[0] as PerformanceNavigationTiming;

      // LCP測定
      const lcpEntries = performance.getEntriesByType(
        'largest-contentful-paint'
      );
      const lcp =
        lcpEntries.length > 0 ? lcpEntries[lcpEntries.length - 1].startTime : 0;

      // CLS測定（簡略化）
      const cls = Math.random() * 0.1; // 実際の実装では layout-shift エントリを使用

      // Bundle size estimation
      const bundleSize = await estimateBundleSize();

      // Memory usage
      const memoryInfo = (performance as any).memory;
      const memoryUsage = memoryInfo
        ? memoryInfo.usedJSHeapSize / 1024 / 1024
        : 0;

      // Accessibility score simulation
      const accessibilityScore = await calculateAccessibilityScore();

      setMetrics({
        lcp: lcp / 1000, // ミリ秒から秒に変換
        fid: Math.random() * 100, // FIDは実際のユーザーインタラクションが必要
        cls,
        bundleSize,
        memoryUsage,
        accessibilityScore,
      });

      // 最適化提案を生成
      generateOptimizationSuggestions({
        lcp: lcp / 1000,
        fid: Math.random() * 100,
        cls,
        bundleSize,
        memoryUsage,
        accessibilityScore,
      });
    } catch (error) {
      console.error('メトリクス収集エラー:', error);
    } finally {
      setIsCollecting(false);
    }
  }, []);

  useEffect(() => {
    collectMetrics();
    const interval = setInterval(collectMetrics, 5000); // 5秒ごとに更新
    return () => clearInterval(interval);
  }, [collectMetrics]);

  const estimateBundleSize = async (): Promise<number> => {
    // 実際の実装では webpack-bundle-analyzer の結果を使用
    return Math.random() * 500 + 200; // KB
  };

  const calculateAccessibilityScore = async (): Promise<number> => {
    // 実際の実装では axe-core を使用してアクセシビリティをスキャン
    const elements = document.querySelectorAll('*');
    let score = 100;

    // 簡略化されたチェック
    elements.forEach(el => {
      if (el.tagName === 'IMG' && !el.getAttribute('alt')) score -= 5;
      if (
        el.tagName === 'BUTTON' &&
        !el.getAttribute('aria-label') &&
        !el.textContent?.trim()
      )
        score -= 3;
    });

    return Math.max(0, score);
  };

  const generateOptimizationSuggestions = (
    currentMetrics: PerformanceMetrics
  ) => {
    const newSuggestions: OptimizationSuggestion[] = [];

    if (currentMetrics.lcp > 2.5) {
      newSuggestions.push({
        type: 'performance',
        title: 'LCP改善が必要',
        description: '画像の最適化とプリロードを実装してください',
        impact: 'high',
        code: `// Next.js Image最適化
import Image from 'next/image';

<Image
  src="/hero-image.jpg"
  alt="Hero"
  priority // LCPに重要な画像
  width={800}
  height={600}
/>`,
      });
    }

    if (currentMetrics.bundleSize > 300) {
      newSuggestions.push({
        type: 'bundle',
        title: 'バンドルサイズが大きい',
        description: 'コード分割とtree-shakingを実装してください',
        impact: 'medium',
        code: `// Dynamic import使用
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Loading...</p>,
});`,
      });
    }

    if (currentMetrics.accessibilityScore < 90) {
      newSuggestions.push({
        type: 'accessibility',
        title: 'アクセシビリティ改善',
        description: 'ARIAラベルとaltテキストを追加してください',
        impact: 'high',
        code: `// アクセシビリティ改善例
<button aria-label="チャットを送信" type="submit">
  <SendIcon />
</button>

<img src="chart.png" alt="売上グラフ：前月比20%増加" />`,
      });
    }

    setSuggestions(newSuggestions);
  };

  const getScoreColor = (value: number, thresholds: [number, number]) => {
    if (value <= thresholds[0]) return '#4caf50'; // green
    if (value <= thresholds[1]) return '#ff9800'; // orange
    return '#f44336'; // red
  };

  const getAccessibilityColor = (score: number) => {
    if (score >= 90) return '#4caf50';
    if (score >= 70) return '#ff9800';
    return '#f44336';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ mr: 2 }}>
          Developer Dashboard
        </Typography>
        <Tooltip title="メトリクスを更新">
          <IconButton onClick={collectMetrics} disabled={isCollecting}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
        {isCollecting && <LinearProgress sx={{ ml: 2, flex: 1 }} />}
      </Box>

      {/* Core Web Vitals */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SpeedIcon sx={{ mr: 1 }} />
                <Typography variant="h6">LCP</Typography>
              </Box>
              <Typography
                variant="h4"
                sx={{ color: getScoreColor(metrics.lcp, [2.5, 4.0]) }}
              >
                {metrics.lcp.toFixed(2)}s
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Largest Contentful Paint
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SpeedIcon sx={{ mr: 1 }} />
                <Typography variant="h6">FID</Typography>
              </Box>
              <Typography
                variant="h4"
                sx={{ color: getScoreColor(metrics.fid, [100, 300]) }}
              >
                {metrics.fid.toFixed(0)}ms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                First Input Delay
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AnalyticsIcon sx={{ mr: 1 }} />
                <Typography variant="h6">CLS</Typography>
              </Box>
              <Typography
                variant="h4"
                sx={{ color: getScoreColor(metrics.cls, [0.1, 0.25]) }}
              >
                {metrics.cls.toFixed(3)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Cumulative Layout Shift
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccessibilityIcon sx={{ mr: 1 }} />
                <Typography variant="h6">A11y Score</Typography>
              </Box>
              <Typography
                variant="h4"
                sx={{
                  color: getAccessibilityColor(metrics.accessibilityScore),
                }}
              >
                {metrics.accessibilityScore.toFixed(0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Accessibility Score
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Bundle & Memory */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <BugReportIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Bundle Size</Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min((metrics.bundleSize / 500) * 100, 100)}
                sx={{ mb: 1 }}
              />
              <Typography variant="h5">
                {metrics.bundleSize.toFixed(0)} KB
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MemoryIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Memory Usage</Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.min((metrics.memoryUsage / 100) * 100, 100)}
                sx={{ mb: 1 }}
              />
              <Typography variant="h5">
                {metrics.memoryUsage.toFixed(1)} MB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 最適化提案 */}
      <Typography variant="h5" sx={{ mb: 2 }}>
        AI最適化提案
      </Typography>
      <Grid container spacing={2}>
        {suggestions.map((suggestion, index) => (
          <Grid item xs={12} key={index}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6" sx={{ mr: 2 }}>
                  {suggestion.title}
                </Typography>
                <Chip
                  label={suggestion.impact}
                  color={
                    suggestion.impact === 'high'
                      ? 'error'
                      : suggestion.impact === 'medium'
                        ? 'warning'
                        : 'info'
                  }
                  size="small"
                />
              </Box>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {suggestion.description}
              </Typography>
              {suggestion.code && (
                <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{ fontFamily: 'monospace' }}
                  >
                    {suggestion.code}
                  </Typography>
                </Paper>
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default DevDashboard;
