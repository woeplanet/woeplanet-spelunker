import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
    root: '.',
    publicDir: false,
    build: {
        outDir: '../static',
        emptyOutDir: true,
        rollupOptions: {
            input: {
                site: resolve(__dirname, 'js/main.js')
            },
            output: {
                entryFileNames: 'js/[name].js',
                chunkFileNames: 'js/[name]-[hash].js',
                assetFileNames: (assetInfo) => {
                    if (assetInfo.name?.endsWith('.css')) {
                        return 'css/[name][extname]'
                    }
                    if (/\.(png|jpg|jpeg|gif|svg)$/.test(assetInfo.name || '')) {
                        return 'images/[name][extname]'
                    }
                    return 'assets/[name][extname]'
                }
            }
        },
        sourcemap: true,
        minify: 'esbuild'
    },
    css: {
        preprocessorOptions: {
            scss: {
                quietDeps: true
            }
        },
        devSourcemap: true
    },
    server: {
        port: 3000,
        proxy: {
            '/v1': 'http://localhost:8000'
        }
    }
})
