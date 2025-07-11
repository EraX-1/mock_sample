import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { FlatCompat } from '@eslint/eslintrc';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  {
    rules: {
      '@typescript-eslint/no-empty-object-type': 'off', // 空のオブジェクト型の警告を無効化
      '@typescript-eslint/no-unused-vars': 'off', // 未使用変数の警告を無効化
      '@typescript-eslint/no-explicit-any': 'off', // any型の使用を許可
      'react/display-name': 'off', // display nameに関するルールを無効化
      'react-hooks/exhaustive-deps': 'warn', // useEffectやuseCallbackの依存配列警告に変更
      '@next/next/no-img-element': 'off', // <img>タグ使用の警告を無効化
    },
  },
];

export default eslintConfig;
