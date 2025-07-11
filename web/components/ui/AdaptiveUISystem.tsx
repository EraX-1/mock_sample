'use client';

import React, {
  useState,
  useEffect,
  useContext,
  createContext,
  useCallback,
} from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  Switch,
  FormControlLabel,
  Paper,
  Typography,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  Brightness4 as DarkModeIcon,
  Accessibility as AccessibilityIcon,
  Speed as SpeedIcon,
  Palette as PaletteIcon,
} from '@mui/icons-material';

interface UserBehaviorData {
  clickPatterns: { [key: string]: number };
  scrollBehavior: { speed: number; frequency: number };
  timeSpent: { [component: string]: number };
  preferredActions: string[];
  errorEncounters: { [error: string]: number };
}

interface AccessibilitySettings {
  fontSize: number;
  contrast: 'normal' | 'high';
  motionReduced: boolean;
  screenReaderOptimized: boolean;
  colorBlindFriendly: boolean;
}

interface AdaptiveUISettings {
  theme: 'light' | 'dark' | 'auto';
  layout: 'compact' | 'comfortable' | 'spacious';
  animationSpeed: number;
  accessibility: AccessibilitySettings;
  autoOptimization: boolean;
}

interface UIOptimizationSuggestion {
  type: 'layout' | 'performance' | 'accessibility' | 'usability';
  title: string;
  description: string;
  confidence: number;
  impact: 'low' | 'medium' | 'high';
  autoApply?: boolean;
}

const AdaptiveUIContext = createContext<{
  settings: AdaptiveUISettings;
  updateSettings: (settings: Partial<AdaptiveUISettings>) => void;
  behaviorData: UserBehaviorData;
  suggestions: UIOptimizationSuggestion[];
}>({
  settings: {
    theme: 'light',
    layout: 'comfortable',
    animationSpeed: 1,
    accessibility: {
      fontSize: 14,
      contrast: 'normal',
      motionReduced: false,
      screenReaderOptimized: false,
      colorBlindFriendly: false,
    },
    autoOptimization: true,
  },
  updateSettings: () => {},
  behaviorData: {
    clickPatterns: {},
    scrollBehavior: { speed: 0, frequency: 0 },
    timeSpent: {},
    preferredActions: [],
    errorEncounters: {},
  },
  suggestions: [],
});

export const useAdaptiveUI = () => useContext(AdaptiveUIContext);

interface AdaptiveUIProviderProps {
  children: React.ReactNode;
}

export const AdaptiveUIProvider: React.FC<AdaptiveUIProviderProps> = ({
  children,
}) => {
  const [settings, setSettings] = useState<AdaptiveUISettings>({
    theme: 'light',
    layout: 'comfortable',
    animationSpeed: 1,
    accessibility: {
      fontSize: 14,
      contrast: 'normal',
      motionReduced: false,
      screenReaderOptimized: false,
      colorBlindFriendly: false,
    },
    autoOptimization: true,
  });

  const [behaviorData, setBehaviorData] = useState<UserBehaviorData>({
    clickPatterns: {},
    scrollBehavior: { speed: 0, frequency: 0 },
    timeSpent: {},
    preferredActions: [],
    errorEncounters: {},
  });

  const [suggestions, setSuggestions] = useState<UIOptimizationSuggestion[]>(
    []
  );

  useEffect(() => {
    // ユーザー行動のトラッキング開始
    startBehaviorTracking();

    // 保存された設定を読み込み
    loadSavedSettings();

    // 定期的な最適化提案生成（30秒ごと）
    const optimizationInterval = setInterval(() => {
      // 最適化提案の生成ロジックをここに含める
      console.log('最適化提案を生成中...');
    }, 30000);

    return () => {
      clearInterval(optimizationInterval);
    };
  }, []);

  useEffect(() => {
    // 設定変更時の自動保存
    try {
      localStorage.setItem('adaptive-ui-settings', JSON.stringify(settings));
    } catch (error) {
      console.error('設定の保存に失敗:', error);
    }
  }, [settings]);

  const startBehaviorTracking = () => {
    // クリックパターンの追跡
    document.addEventListener('click', e => {
      const target = e.target as HTMLElement;
      const elementType = target.tagName.toLowerCase();

      setBehaviorData(prev => ({
        ...prev,
        clickPatterns: {
          ...prev.clickPatterns,
          [elementType]: (prev.clickPatterns[elementType] || 0) + 1,
        },
      }));
    });

    // スクロール行動の追跡
    let scrollStartTime = Date.now();
    document.addEventListener('scroll', () => {
      const scrollTime = Date.now() - scrollStartTime;
      setBehaviorData(prev => ({
        ...prev,
        scrollBehavior: {
          speed: prev.scrollBehavior.speed + scrollTime,
          frequency: prev.scrollBehavior.frequency + 1,
        },
      }));
      scrollStartTime = Date.now();
    });

    // エラーの追跡
    window.addEventListener('error', e => {
      setBehaviorData(prev => ({
        ...prev,
        errorEncounters: {
          ...prev.errorEncounters,
          [e.message]: (prev.errorEncounters[e.message] || 0) + 1,
        },
      }));
    });
  };

  const loadSavedSettings = () => {
    try {
      const saved = localStorage.getItem('adaptive-ui-settings');
      if (saved) {
        setSettings(JSON.parse(saved));
      }
    } catch (error) {
      console.error('設定の読み込みに失敗:', error);
    }
  };

  const saveSettings = useCallback(() => {
    try {
      localStorage.setItem('adaptive-ui-settings', JSON.stringify(settings));
    } catch (error) {
      console.error('設定の保存に失敗:', error);
    }
  }, [settings]);

  const updateSettings = useCallback(
    (newSettings: Partial<AdaptiveUISettings>) => {
      setSettings(prev => ({ ...prev, ...newSettings }));
    },
    []
  );

  const generateOptimizationSuggestions = useCallback(() => {
    const newSuggestions: UIOptimizationSuggestion[] = [];

    // クリックパターン分析
    const buttonClicks = behaviorData.clickPatterns.button || 0;
    const totalClicks = Object.values(behaviorData.clickPatterns).reduce(
      (sum, count) => sum + count,
      0
    );

    if (buttonClicks / totalClicks < 0.3 && totalClicks > 50) {
      newSuggestions.push({
        type: 'usability',
        title: 'ボタンの視認性向上',
        description:
          'ボタンのサイズを大きくして、より見つけやすくすることを推奨します',
        confidence: 0.8,
        impact: 'medium',
        autoApply: true,
      });
    }

    // スクロール行動分析
    if (
      behaviorData.scrollBehavior.frequency > 100 &&
      behaviorData.scrollBehavior.speed /
        behaviorData.scrollBehavior.frequency >
        1000
    ) {
      newSuggestions.push({
        type: 'layout',
        title: 'コンテンツ密度の調整',
        description:
          '頻繁なスクロールが検出されました。より多くの情報を一画面に表示することを推奨します',
        confidence: 0.7,
        impact: 'high',
      });
    }

    // アクセシビリティチェック
    if (!settings.accessibility.screenReaderOptimized) {
      const imagesWithoutAlt =
        document.querySelectorAll('img:not([alt])').length;
      if (imagesWithoutAlt > 0) {
        newSuggestions.push({
          type: 'accessibility',
          title: 'アクセシビリティの改善',
          description: `${imagesWithoutAlt}個の画像にaltテキストがありません。スクリーンリーダー対応を推奨します`,
          confidence: 0.9,
          impact: 'high',
        });
      }
    }

    // パフォーマンス分析
    const performanceEntries = performance.getEntriesByType('navigation');
    if (performanceEntries.length > 0) {
      const loadTime = performanceEntries[0] as PerformanceNavigationTiming;
      if (loadTime.loadEventEnd - loadTime.loadEventStart > 3000) {
        newSuggestions.push({
          type: 'performance',
          title: 'ページ読み込み速度の改善',
          description:
            '読み込み時間が遅いため、画像の遅延読み込みやコンポーネントの分割を推奨します',
          confidence: 0.85,
          impact: 'high',
        });
      }
    }

    setSuggestions(newSuggestions);

    // 自動最適化が有効な場合、高信頼度の提案を自動適用
    if (settings.autoOptimization) {
      newSuggestions
        .filter(s => s.autoApply && s.confidence > 0.8)
        .forEach(suggestion => {
          console.log('提案を自動適用:', suggestion.title);
          // 簡略化: 実際の適用ロジックはここに含める
        });
    }
  }, [behaviorData, settings, setSuggestions]);

  const applyOptimizationSuggestion = useCallback(
    (suggestion: UIOptimizationSuggestion) => {
      switch (suggestion.type) {
        case 'layout':
          updateSettings({ layout: 'compact' });
          break;
        case 'accessibility':
          updateSettings({
            accessibility: {
              ...settings.accessibility,
              screenReaderOptimized: true,
            },
          });
          break;
        default:
          console.log('提案を適用:', suggestion.title);
      }
    },
    [settings.accessibility, updateSettings]
  );

  // テーマ作成
  const theme = createTheme({
    palette: {
      mode:
        settings.theme === 'auto'
          ? window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light'
          : settings.theme,
      ...(settings.accessibility.contrast === 'high' && {
        primary: { main: '#000000' },
        secondary: { main: '#ffffff' },
      }),
      ...(settings.accessibility.colorBlindFriendly && {
        primary: { main: '#0073e6' },
        secondary: { main: '#ff6b35' },
      }),
    },
    typography: {
      fontSize: settings.accessibility.fontSize,
      allVariants: {
        fontSize: settings.accessibility.fontSize,
      },
    },
    spacing:
      settings.layout === 'compact'
        ? 4
        : settings.layout === 'spacious'
          ? 12
          : 8,
    transitions: {
      duration: {
        shortest: 150 * settings.animationSpeed,
        shorter: 200 * settings.animationSpeed,
        short: 250 * settings.animationSpeed,
        standard: 300 * settings.animationSpeed,
        complex: 375 * settings.animationSpeed,
        enteringScreen: 225 * settings.animationSpeed,
        leavingScreen: 195 * settings.animationSpeed,
      },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: settings.accessibility.motionReduced
          ? {
              '*, *::before, *::after': {
                animationDuration: '0.01ms !important',
                animationIterationCount: '1 !important',
                transitionDuration: '0.01ms !important',
                scrollBehavior: 'auto !important',
              },
            }
          : {},
      },
    },
  });

  return (
    <AdaptiveUIContext.Provider
      value={{ settings, updateSettings, behaviorData, suggestions }}
    >
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </AdaptiveUIContext.Provider>
  );
};

interface AdaptiveUIControlPanelProps {
  open: boolean;
  onClose: () => void;
}

export const AdaptiveUIControlPanel: React.FC<AdaptiveUIControlPanelProps> = ({
  open,
  onClose,
}) => {
  const { settings, updateSettings, suggestions } = useAdaptiveUI();
  const [showNotification, setShowNotification] = useState(false);

  const handleSettingChange = (key: keyof AdaptiveUISettings, value: any) => {
    updateSettings({ [key]: value });
    setShowNotification(true);
  };

  if (!open) return null;

  return (
    <Paper
      sx={{
        position: 'fixed',
        top: 20,
        left: 20,
        p: 3,
        width: 350,
        maxHeight: '80vh',
        overflow: 'auto',
        zIndex: 1300,
      }}
    >
      <Typography
        variant="h6"
        sx={{ mb: 2, display: 'flex', alignItems: 'center' }}
      >
        <PaletteIcon sx={{ mr: 1 }} />
        Adaptive UI Settings
      </Typography>

      {/* テーマ設定 */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Theme</InputLabel>
        <Select
          value={settings.theme}
          onChange={e => handleSettingChange('theme', e.target.value)}
        >
          <MenuItem value="light">Light</MenuItem>
          <MenuItem value="dark">Dark</MenuItem>
          <MenuItem value="auto">Auto</MenuItem>
        </Select>
      </FormControl>

      {/* レイアウト設定 */}
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>Layout</InputLabel>
        <Select
          value={settings.layout}
          onChange={e => handleSettingChange('layout', e.target.value)}
        >
          <MenuItem value="compact">Compact</MenuItem>
          <MenuItem value="comfortable">Comfortable</MenuItem>
          <MenuItem value="spacious">Spacious</MenuItem>
        </Select>
      </FormControl>

      {/* アニメーション速度 */}
      <Typography gutterBottom>Animation Speed</Typography>
      <Slider
        value={settings.animationSpeed}
        onChange={(_, value) => handleSettingChange('animationSpeed', value)}
        min={0.1}
        max={2}
        step={0.1}
        marks={[
          { value: 0.5, label: 'Slow' },
          { value: 1, label: 'Normal' },
          { value: 1.5, label: 'Fast' },
        ]}
        sx={{ mb: 2 }}
      />

      {/* アクセシビリティ設定 */}
      <Typography
        variant="h6"
        sx={{ mb: 1, display: 'flex', alignItems: 'center' }}
      >
        <AccessibilityIcon sx={{ mr: 1 }} />
        Accessibility
      </Typography>

      <Typography gutterBottom>Font Size</Typography>
      <Slider
        value={settings.accessibility.fontSize}
        onChange={(_, value) =>
          handleSettingChange('accessibility', {
            ...settings.accessibility,
            fontSize: value,
          })
        }
        min={12}
        max={20}
        step={1}
        sx={{ mb: 2 }}
      />

      <FormControlLabel
        control={
          <Switch
            checked={settings.accessibility.motionReduced}
            onChange={e =>
              handleSettingChange('accessibility', {
                ...settings.accessibility,
                motionReduced: e.target.checked,
              })
            }
          />
        }
        label="Reduce Motion"
        sx={{ mb: 1 }}
      />

      <FormControlLabel
        control={
          <Switch
            checked={settings.accessibility.colorBlindFriendly}
            onChange={e =>
              handleSettingChange('accessibility', {
                ...settings.accessibility,
                colorBlindFriendly: e.target.checked,
              })
            }
          />
        }
        label="Color Blind Friendly"
        sx={{ mb: 2 }}
      />

      {/* 自動最適化 */}
      <FormControlLabel
        control={
          <Switch
            checked={settings.autoOptimization}
            onChange={e =>
              handleSettingChange('autoOptimization', e.target.checked)
            }
          />
        }
        label="Auto Optimization"
        sx={{ mb: 2 }}
      />

      {/* 最適化提案 */}
      {suggestions.length > 0 && (
        <>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Optimization Suggestions
          </Typography>
          {suggestions.slice(0, 3).map((suggestion, index) => (
            <Paper key={index} sx={{ p: 1, mb: 1, bgcolor: 'grey.50' }}>
              <Typography variant="subtitle2">{suggestion.title}</Typography>
              <Typography variant="body2" color="text.secondary">
                {suggestion.description}
              </Typography>
              <Typography variant="caption">
                Confidence: {(suggestion.confidence * 100).toFixed(0)}%
              </Typography>
            </Paper>
          ))}
        </>
      )}

      <Button onClick={onClose} variant="outlined" fullWidth sx={{ mt: 2 }}>
        Close
      </Button>

      <Snackbar
        open={showNotification}
        autoHideDuration={2000}
        onClose={() => setShowNotification(false)}
      >
        <Alert severity="success">Settings updated!</Alert>
      </Snackbar>
    </Paper>
  );
};
