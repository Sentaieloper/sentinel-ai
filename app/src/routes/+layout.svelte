<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';

	const navItems = [
		{ href: '/', label: 'Dashboard' },
		{ href: '/positions', label: 'Positions' },
		{ href: '/alerts', label: 'Alerts' }
	];
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
			<div class="status-indicator">
				<span class="pulse"></span>
				<span class="status-text">MONITORING</span>
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

	.main-content {
		padding-top: 24px;
		padding-bottom: 40px;
	}

	@keyframes pulse-glow {
		0%, 100% { opacity: 1; box-shadow: 0 0 4px var(--accent-green); }
		50% { opacity: 0.5; box-shadow: 0 0 8px var(--accent-green); }
	}
</style>
