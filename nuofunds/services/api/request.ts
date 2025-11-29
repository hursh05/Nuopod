import axios, { AxiosResponse } from "axios";
import client from "./client";

import HttpStatusCode from "./HttpStatusCode";

import { useAuthStore } from "@/store/useAuthStore";
import Toast from "react-native-toast-message";

type ResponseI<T, Success = true> = {
  data: T;
  message: string;
  success: Success;
};

type ResponseErrorType = {
  [key: string]: string[];
};

const formatError = (E: ResponseI<ResponseErrorType, false>) =>
  E.data
    ? Object.keys(E.data)
        .map((key) => `${E.data[key].map((error) => `- ${error}`).join("\n")}`)
        .join("\n")
    : (E.message ?? "An unknown error has occurred");

const request = <T>(
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH",
  url: string,
  params?: object,
  requestData?: object,
  useToken?: boolean,
  showError?: boolean,
  token?: string
) =>
  (async () => {
    try {
      const response: AxiosResponse = await client({
        method,
        url,
        data: method === "GET" ? undefined : requestData,
        params,
        token:
          useToken !== false
            ? (token ?? useAuthStore.getState().token)
            : undefined,
        headers: {
          "Content-Type":
            requestData instanceof FormData
              ? "multipart/form-data"
              : "application/json",
        },
      });

      const { data, status }: { data: ResponseI<T>; status: number } = response;
      return {
        data,
        status,
        HttpStatusCode,
      };
    } catch (error: any) {
      if (!axios.isAxiosError(error)) {
        if (showError !== false) {
          Toast.show({
            type: "error",
            text1: "Error!",
            text2: `An unexpected error has occurred while processing your request!`,
          });
        }
        return {
          status: undefined,
          HttpStatusCode,
          data: { success: false, data: null },
        };
      }
      const data = error.response?.data as ResponseI<ResponseErrorType, false>;
      if (showError !== false && data) {
        Toast.show({
          type: "error",
          text1: "Error!",
          text2: formatError(data),
        });
      }
      return {
        status: error.response?.status,
        HttpStatusCode,
        data,
      };
    }
  })();

export { formatError };
export type { ResponseErrorType, ResponseI };
export default request;
