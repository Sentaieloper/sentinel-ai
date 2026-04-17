import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	define: {
		'process.env': {},
	},
	resolve: {
		alias: {
			buffer: 'buffer',
		},
	},
	optimizeDeps: {
		include: ['buffer', '@coral-xyz/anchor', '@solana/web3.js'],
	},
	server: {
		port: 5176,
		proxy: {
			'/api': {
				target: 'http://localhost:8001',
				changeOrigin: true,
			}
		}
	}
});
