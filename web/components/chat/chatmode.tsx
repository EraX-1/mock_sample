import React from 'react';
import type { NextPage } from 'next';

export type Chatmode = {
  text: string;
};

const Chatmode: NextPage<Chatmode> = ({ text }) => {
  return (
    <div className=" hover:bg-zinc-200  w-full flex flex-row items-center justify-start text-black h-10 gap-3">
      <img className="w-6 h-6 object-cover" alt="" src="/ai-icon.png" />
      <div className="relative leading-normal font-normal text-sm">{text}</div>
    </div>
  );
};

export default Chatmode;
