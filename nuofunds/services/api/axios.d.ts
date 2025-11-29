import 'axios';

declare module 'axios' {
  export interface AxiosRequestConfig {
    token?: string | null;
  }
}
