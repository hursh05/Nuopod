/**
 * Learn more about Light and Dark modes:
 * https://docs.expo.io/guides/color-schemes/
 */

import {
  Text as DefaultText,
  View as DefaultView,
  KeyboardAvoidingView,
} from "react-native";

import Colors from "@/constants/Colors";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useColorScheme } from "./useColorScheme";

type ThemeProps = {
  lightColor?: string;
  darkColor?: string;
  backgroundColor?: string; // allow direct bg override via prop
};

export type TextProps = ThemeProps & DefaultText["props"];
export type ViewProps = ThemeProps & DefaultView["props"];

export function useThemeColor(
  props: { light?: string; dark?: string },
  colorName: keyof typeof Colors.light & keyof typeof Colors.dark
) {
  const theme = useColorScheme() ?? "light";
  const colorFromProps = props[theme];

  if (colorFromProps) {
    return colorFromProps;
  } else {
    return Colors[theme][colorName];
  }
}

export function Text(props: TextProps) {
  const { style, lightColor, darkColor, ...otherProps } = props;
  const color = useThemeColor({ light: lightColor, dark: darkColor }, "text");

  return <DefaultText style={[{ color }, style]} {...otherProps} />;
}

export function View(props: ViewProps) {
  const { style, lightColor, darkColor, backgroundColor, ...otherProps } =
    props;
  const bg =
    backgroundColor ??
    useThemeColor({ light: lightColor, dark: darkColor }, "background");

  return (
    <DefaultView style={[{ backgroundColor: bg }, style]} {...otherProps} />
  );
}

export function PageView(props: ViewProps) {
  const { style, lightColor, darkColor, backgroundColor, ...otherProps } =
    props;
  const insets = useSafeAreaInsets();
  const bg =
    backgroundColor ??
    useThemeColor({ light: lightColor, dark: darkColor }, "background");
  return (
    <KeyboardAvoidingView
      style={{
        flex: 1,
        backgroundColor: bg,
        paddingTop: insets.top,
        paddingBottom: insets.bottom,
        // borderColor: "red",
        // borderWidth: 1,
      }}
    >
      <DefaultView
        style={[
          {
            flex: 1,
            backgroundColor: bg,
          },
          style,
        ]}
        {...otherProps}
      />
    </KeyboardAvoidingView>
  );
}
