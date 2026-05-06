<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { walletStore, connectPhantom, disconnectPhantom, abbreviateAddress } from '$lib/stores/wallet';

	const navItems = [
		{ href: '/', label: 'Dashboard' },
		{ href: '/positions', label: 'Positions' },
		{ href: '/alerts', label: 'Alerts' }
	];

	let walletConnected = false;
	let walletAddress: string | null = null;

	walletStore.subscribe((state) => {
		walletConnected = state.connected;
		walletAddress = state.address;
	});

	async function handleWalletClick() {
		if (walletConnected) {
			await disconnectPhantom();
		} else {
			await connectPhantom();
		}
	}
</script>

<div class="app-shell">
	<header class="topbar">
		<div class="container topbar-inner">
			<div class="brand">
				<span class="brand-icon">&#9650;</span>
				<span class="brand-text">SENTINEL<span class="brand-ai">AI</span></span>
			</div>
			<nav class="nav-links">
				{#each navItems as item}
					<a
						href={item.href}
						class="nav-link"
						class:active={$page.url.pathname === item.href}
					>
						{item.label}
					</a>
				{/each}
			</nav>
			<div class="topbar-right">
				<div class="status-indicator">
					<span class="pulse"></span>
					<span class="status-text">MONITORING</span>
				</div>
				<button class="wallet-btn" on:click={handleWalletClick}>
					{#if walletConnected && walletAddress}
						<span class="wallet-dot connected"></span>
						<span class="wallet-addr">{abbreviateAddress(walletAddress)}</span>
					{:else}
						<span class="wallet-dot"></span>
						<span>CONNECT WALLET</span>
					{/if}
				</button>
			</div>
		</div>
	</header>

	<main class="container main-content">
		<slot />
	</main>
</div>

<style>
	.app-shell {
		min-height: 100vh;
	}

	.topbar {
		background: var(--bg-panel);
		border-bottom: 1px solid var(--border);
		padding: 12px 0;
		position: sticky;
		top: 0;
		z-index: 50;
	}

	.topbar-inner {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.brand-icon {
		color: var(--accent-green);
		font-size: 18px;
	}

	.brand-text {
		font-size: 14px;
		font-weight: 700;
		letter-spacing: 2px;
	}

	.brand-ai {
		color: var(--accent-green);
	}

	.nav-links {
		display: flex;
		gap: 4px;
	}

	.nav-link {
		padding: 6px 14px;
		font-size: 12px;
		font-weight: 500;
		color: var(--text-secondary);
		text-decoration: none;
		border-radius: 2px;
		transition: all 0.15s;
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.nav-link:hover {
		color: var(--text-primary);
		background: rgba(61, 220, 132, 0.05);
		text-decoration: none;
	}

	.nav-link.active {
		color: var(--accent-green);
		background: rgba(61, 220, 132, 0.1);
	}

	.topbar-right {
		display: flex;
		align-items: center;
		gap: 14px;
	}

	.status-indicator {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.pulse {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--accent-green);
		animation: pulse-glow 2s infinite;
	}

	.status-text {
		font-size: 10px;
		font-weight: 600;
		color: var(--accent-green);
		letter-spacing: 1px;
	}

	.wallet-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--bg-card);
		border: 1px solid var(--border-bright);
		color: var(--text-secondary);
		padding: 6px 14px;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		cursor: pointer;
		border-radius: 2px;
		transition: all 0.15s;
	}

	.wallet-btn:hover {
		border-color: var(--accent-green);
		color: var(--text-primary);
	}

	.wallet-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--text-dim);
	}

	.wallet-dot.connected {
		background: var(--accent-green);
		box-shadow: 0 0 4px var(--accent-green);
	}

	.wallet-addr {
		color: var(--accent-green);
	}

	.main-content {
		padding-top: 24px;
		padding-bottom: 40px;
	}

	@keyframes pulse-glow {
		0%, 100% { opacity: 1; box-shadow: 0 0 4px var(--accent-green); }
		50% { opacity: 0.5; box-shadow: 0 0 8px var(--accent-green); }
	}
</style>
