import type { ColorValue } from "react-native";
import Svg, { Path, Circle, Rect } from "react-native-svg";
export type IconName =
  | "home"
  | "chart"
  | "user"
  | "bell"
  | "arrow-up"
  | "arrow-down"
  | "pix"
  | "eye"
  | "calendar"
  | "chevron"
  | "back"
  | "sparkles"
  | "check"
  | "close"
  | "clock"
  | "shield";
const paths: Record<IconName, string> = {
  home: "M3 10 12 3l9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z",
  chart: "M3 3v18h18M6 15l5-5 4 3 6-8",
  user: "M4 21v-2a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v2",
  bell: "M18 8a6 6 0 0 0-12 0c0 8-3 8-3 10h18c0-2-3-2-3-10M10 21h4",
  "arrow-up": "M6 18 18 6M6 6h12v12",
  "arrow-down": "M18 6 6 18M6 6v12h12",
  pix: "m12 2 10 10-10 10L2 12ZM6 8l6 6 6-6M6 16l6-6 6 6",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z",
  calendar: "M4 5h16v16H4ZM4 10h16M8 2v6M16 2v6",
  chevron: "m9 5 7 7-7 7",
  back: "m15 5-7 7 7 7",
  sparkles: "m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3ZM20 2v4M18 4h4",
  check: "m5 12 4 4L19 6",
  close: "m6 6 12 12M6 18 18 6",
  clock: "M12 7v5l4 2",
  shield: "m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6ZM8 12l3 3 5-6",
};
export function Icon({
  name,
  color = "#1F4DD8",
  size = 22,
}: {
  name: IconName;
  color?: ColorValue;
  size?: number;
}) {
  return (
    <Svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      accessible={false}
    >
      <Path d={paths[name]} />
      {name === "user" && <Circle cx={12} cy={6} r={4} />}
      {name === "eye" && <Circle cx={12} cy={12} r={3} />}
      {name === "clock" && <Circle cx={12} cy={12} r={9} />}
      {name === "calendar" && <Rect x={8} y={13} width={2} height={2} />}
    </Svg>
  );
}
