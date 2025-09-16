// Flat ESLint config for ESLint v9
import js from '@eslint/js';
import ts from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';

export default [
  js.configs.recommended,
  ...ts.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { 'react-hooks': reactHooks },
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'module'
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn'
    }
  },
  {
    files: ['scripts/*.cjs'],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'script'
    },
    rules: {
      // Allow commonjs requires in utility scripts
      '@typescript-eslint/no-var-requires': 'off'
    }
  },
  {
    ignores: ['dist', 'node_modules']
  }
];
