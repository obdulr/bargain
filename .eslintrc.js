module.exports = {
  root: true,
  extends: ["eslint:recommended", "prettier"],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: "module",
  },
  env: {
    node: true,
    es6: true,
  },
  ignorePatterns: ["node_modules/", "dist/", ".next/", "build/"],
};
