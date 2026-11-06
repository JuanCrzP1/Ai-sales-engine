export interface ApiServer {
  apiUrl: string;
  halt(): Promise<void>;
  start(): Promise<void>;
  restart(): Promise<void>;
  databaseContains(text: string): boolean;
  databaseSize(): number;
  output(): string;
  stop(): Promise<void>;
}

export function startApiServer(): Promise<ApiServer>;
