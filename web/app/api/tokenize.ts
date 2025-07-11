import { NextApiRequest, NextApiResponse } from 'next';
import { encode } from 'gpt-tokenizer';

type TokenizeResponse = {
  tokenCount: number;
  tokens: number[];
};

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse<TokenizeResponse | { error: string }>
) {
  if (req.method === 'POST') {
    const { text } = req.body;

    if (!text || typeof text !== 'string') {
      return res
        .status(400)
        .json({ error: 'Text is required and must be a string' });
    }

    try {
      const tokens = encode(text);

      return res.status(200).json({
        tokenCount: tokens.length,
        tokens,
      });
    } catch (error) {
      return res.status(500).json({ error: (error as Error).message });
    }
  } else {
    return res.status(405).json({ error: 'Method not allowed' });
  }
}
