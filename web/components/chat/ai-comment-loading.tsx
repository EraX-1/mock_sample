import { Box } from '@mui/material';
import { keyframes, styled } from '@mui/system';
import type { NextPage } from 'next';

const gradientAnimation = keyframes`
  0% { background-position: 200% 50%; }
  100% { background-position: -100% 50%; }
`;

const GradientText = styled('p')({
  background: 'linear-gradient(90deg, #d3d3d3, #555555, #d3d3d3)',
  backgroundSize: '400% 400%',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  animation: `${gradientAnimation} 5s linear infinite`,
});

const AICommentLoading: NextPage = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
      }}
    >
      <Box>
        <img
          className="relative w-8 h-8 object-cover"
          alt=""
          src="/ai-icon.png"
        />
      </Box>

      <GradientText>ドキュメントを検索中</GradientText>
    </Box>
  );
};

export default AICommentLoading;
