type ParsedEnvVar<T extends string> = T extends `[${infer Content}]`
  ? Content extends `${infer First},"${infer Rest}"`
    ? First extends `"${infer Value}"`
      ? Value | ParsedEnvVar<`[${Rest}]`>
      : never
    : Content extends `"${infer Value}"`
      ? Value
      : never
  : never;

export type ChatIndexType =
  typeof process.env.NEXT_PUBLIC_SEARCH_INDEX_NAME_ID_LIST extends string
    ? ParsedEnvVar<typeof process.env.NEXT_PUBLIC_SEARCH_INDEX_NAME_ID_LIST>
    : never;

export type ChatModelType =
  typeof process.env.NEXT_PUBLIC_MODEL_LIST extends string
    ? ParsedEnvVar<typeof process.env.NEXT_PUBLIC_MODEL_LIST>
    : never;
