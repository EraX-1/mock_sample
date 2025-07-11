const fs = require('fs');
const path = require('path');
const axios = require('axios');
const dotenv = require('dotenv');

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8080';
const ENV_FILES = [
  path.resolve(process.cwd(), '.env.development'),
  path.resolve(process.cwd(), '.env.production'),
];

async function updateCoreConfig() {
  try {
    // APIから設定を取得
    const response = await axios.get(`${API_URL}/core_config`);
    const config = response.data;

    // 各環境変数ファイルに設定を反映
    for (const envFile of ENV_FILES) {
      // 現在の.envファイルの内容を読み込む
      const currentEnv = fs.readFileSync(envFile, 'utf8');
      const envConfig = dotenv.parse(currentEnv);

      // 新しい設定を追加
      envConfig.NEXT_PUBLIC_CORE_NAME = config.NAME;
      envConfig.NEXT_PUBLIC_SEARCH_INDEX_NAME_JP_LIST = JSON.stringify(
        config.SEARCH_INDEX_NAME_JP_LIST
      );
      envConfig.NEXT_PUBLIC_SEARCH_INDEX_NAME_ID_LIST = JSON.stringify(
        config.SEARCH_INDEX_NAME_ID_LIST
      );
      envConfig.NEXT_PUBLIC_SEARCH_INDEX_AZURE_ID_LIST = JSON.stringify(
        config.SEARCH_INDEX_AZURE_ID_LIST
      );
      envConfig.NEXT_PUBLIC_MODEL_LIST = JSON.stringify(config.MODEL_LIST);
      envConfig.NEXT_PUBLIC_DEFAULT_MODEL = config.DEFAULT_MODEL;

      // .envファイルに書き込む
      const newEnv = Object.entries(envConfig)
        .map(([key, value]) => {
          // JSON文字列の場合はシングルクォートで囲む
          if (value.startsWith('[') || value.startsWith('{')) {
            return `${key} = '${value}'`;
          }
          // それ以外の場合はダブルクォートで囲む
          return `${key} = "${value}"`;
        })
        .join('\n');

      fs.writeFileSync(envFile, newEnv);
      console.log(
        `Core config has been updated successfully in ${path.basename(
          envFile
        )}!`
      );
    }
  } catch (error) {
    console.error('Error updating core config:', error.message);
    process.exit(1);
  }
}

updateCoreConfig();
