const { defineConfig } = require("eslint/config");
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([
  expoConfig,
  {
    files: ["tests/*.cjs"],
    languageOptions: {
      globals: { __dirname: "readonly", require: "readonly" },
    },
  },
  { ignores: [".expo/*", "dist/*"] },
]);
