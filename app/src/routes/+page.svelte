<script lang="ts">
	import { onMount } from 'svelte';
	import { walletStore } from '$lib/stores/wallet';
	import OpenPositionModal from '$lib/components/OpenPositionModal.svelte';

	let modalOpen = false;
	let onChainAvailable = true;
	// On-chain Anchor program is deployed at 5QiE51bSE3yqJFmRhj1CHt2NwaJpC2iodsaLDrZJDheE on devnet.

	type RiskLevel = 'Safe' | 'Warning' | 'Danger' | 'Critical';

	interface AdviceTip {
		severity: RiskLevel;
		title: string;
		body: string;
	}

	interface Position {
		id: string;
		protocol: string;
		asset: string;
		healthFactor?: number;
		healthPercent?: number;
		leverage?: number;
		direction?: 'LONG' | 'SHORT' | 'FLAT';
		entryPrice?: number;
		oraclePrice?: number;
		notional?: number;
		unrealizedPnl?: number;
		collateral?: number;
		debt?: number;
		balance?: number;
		solEquivalent?: number;
		exchangeRate?: number;
		riskLevel: RiskLevel;
		lastChecked: string;
		source?: string;
		advice?: AdviceTip[];
	}

	interface AlertItem {
		id: string;
		type: string;
		protocol: string;
		message: string;
		timestamp: string;
		severity: RiskLevel;
	}

	interface Stats {
		totalCollateral: number;
		totalDebt: number;
		avgHealthFactor: number;
		atRiskCount: number;
	}

	const fallbackPositions: Position[] = [
		{ id: '1', protocol: 'Kamino', asset: 'SOL/USDC', healthFactor: 2.41, collateral: 12500, debt: 5180, riskLevel: 'Safe', lastChecked: '2m ago' },
		{ id: '2', protocol: 'Drift', asset: 'ETH-PERP', healthFactor: 1.35, collateral: 8200, debt: 6074, riskLevel: 'Warning', lastChecked: '45s ago' },
		{ id: '3', protocol: 'Marinade', asset: 'mSOL', healthFactor: 4.10, collateral: 25000, debt: 6097, riskLevel: 'Safe', lastChecked: '1m ago' },
		{ id: '4', protocol: 'Kamino', asset: 'JitoSOL/SOL', healthFactor: 1.08, collateral: 3400, debt: 3148, riskLevel: 'Critical', lastChecked: '10s ago' },
	];

	const fallbackAlerts: AlertItem[] = [
		{ id: 'a1', type: 'CRITICAL', protocol: 'Kamino', message: 'JitoSOL/SOL health factor below 1.10 — liquidation imminent', timestamp: '10s ago', severity: 'Critical' },
		{ id: 'a2', type: 'WARNING', protocol: 'Drift', message: 'ETH-PERP position approaching warning zone (HF: 1.35)', timestamp: '2m ago', severity: 'Warning' },
		{ id: 'a3', type: 'PROTECTED', protocol: 'Kamino', message: 'Auto-protect triggered: added 200 USDC collateral', timestamp: '15m ago', severity: 'Safe' },
	];

	interface SupportedProtocol {
		name: string;
		kind: string;
		status: 'TRACKING' | 'OFFLINE' | 'SOON';
		mark: string;
		accent: string;
	}

	const supportedProtocols: SupportedProtocol[] = [
		{ name: 'Sentinel Perps', kind: 'On-chain leverage · devnet',  status: 'TRACKING', mark: '▲', accent: '#3ddc84' },
		{ name: 'Kamino',         kind: 'Lending · devnet',            status: 'TRACKING', mark: '▣', accent: '#ff8c42' },
		{ name: 'MarginFi',       kind: 'Lending · devnet',            status: 'TRACKING', mark: '◇', accent: '#b07bff' },
		{ name: 'Marinade',       kind: 'Liquid staking · devnet',     status: 'TRACKING', mark: '◆', accent: '#52c4ff' },
		{ name: 'Wallet',         kind: 'SOL + SPL balances · devnet', status: 'TRACKING', mark: '●', accent: '#3ddc84' },
		{ name: 'Drift',          kind: 'Perpetuals · paused',         status: 'OFFLINE',  mark: '◈', accent: '#7a9a7a' },
		{ name: 'Zeta',           kind: 'Perpetuals · shutdown',       status: 'OFFLINE',  mark: '◉', accent: '#7a9a7a' },
		{ name: 'Jupiter',        kind: 'Perpetuals · mainnet-only',   status: 'SOON',     mark: '◎', accent: '#7a9a7a' },
	];

	let positions: Position[] = fallbackPositions;
	let recentAlerts: AlertItem[] = fallbackAlerts;
	let dataSource: 'LIVE' | 'DEMO' = 'DEMO';
	let livePositions: Position[] = [];
	let liveLoading = false;
	let liveError = '';
	let hasDriftAccount = false;
	let currentWallet: string | null = null;

	let totalCollateral = 0;
	let totalDebt = 0;
	let avgHealth = 0;
	let criticalCount = 0;

	function computeStats(posData: Position[]) {
		totalCollateral = posData.reduce((s, p) => s + p.collateral, 0);
		totalDebt = posData.reduce((s, p) => s + p.debt, 0);
		avgHealth = posData.reduce((s, p) => s + p.healthFactor, 0) / posData.length;
		criticalCount = posData.filter(p => p.riskLevel === 'Critical' || p.riskLevel === 'Danger').length;
	}

	computeStats(positions);

	async function loadDemo() {
		try {
			const [statsRes, posRes, alertsRes] = await Promise.all([
				fetch('/api/stats'),
				fetch('/api/positions'),
				fetch('/api/alerts'),
			]);

			if (statsRes.ok && posRes.ok && alertsRes.ok) {
				const statsData: Stats = await statsRes.json();
				positions = await posRes.json();
				recentAlerts = (await alertsRes.json()).slice(0, 3);
				dataSource = 'LIVE';

				totalCollateral = statsData.totalCollateral;
				totalDebt = statsData.totalDebt;
				avgHealth = statsData.avgHealthFactor;
				criticalCount = statsData.atRiskCount;
			}
		} catch {
			// API unavailable — keep fallback data
		}
	}

	async function evaluateOnChain(raw: any): Promise<Position | null> {
		const collateralSol = Number(raw.collateralLamports) / 1_000_000_000;
		try {
			const solPriceRes = await fetch('/api/pyth/SOL');
			const solPrice = (await solPriceRes.json()).price;
			const collateralUsd = collateralSol * solPrice;
			const leverage = raw.leverageBps / 100;
			const entryPrice = Number(raw.entryPriceMicro) / 1_000_000;

			const res = await fetch('/api/sentinel/evaluate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					id: raw.pda,
					asset: raw.asset,
					direction: raw.direction,
					collateralUsd,
					leverage,
					entryPrice,
					openedAt: raw.openedAt,
					source: 'sentinel-onchain',
				}),
			});
			if (!res.ok) return null;
			return await res.json();
		} catch {
			return null;
		}
	}

	async function loadOnChainPositions(wallet: string): Promise<Position[]> {
		try {
			const mod = await import('$lib/onchain/openLeveraged');
			const raw = await mod.listOnChainPositions(wallet);
			const evaluated = await Promise.all(raw.map(evaluateOnChain));
			return evaluated.filter((p): p is Position => p !== null);
		} catch (e) {
			console.warn('on-chain fetch failed', e);
			return [];
		}
	}

	async function loadLivePositions(wallet: string) {
		liveLoading = true;
		liveError = '';
		try {
			const [paperRes, onChain, chainRes] = await Promise.all([
				fetch(`/api/paper/positions/${wallet}`).then((r) => (r.ok ? r.json() : [])),
				loadOnChainPositions(wallet),
				fetch(`/api/positions/chain/${wallet}`).then((r) => (r.ok ? r.json() : { positions: [] })),
			]);
			const paper = Array.isArray(paperRes) ? paperRes : [];
			const chain = Array.isArray(chainRes?.positions) ? chainRes.positions : [];
			livePositions = [...onChain, ...paper, ...chain];
			hasDriftAccount = livePositions.length > 0;
		} catch (e: any) {
			liveError = e?.message || 'failed to load live positions';
			hasDriftAccount = false;
			livePositions = [];
		} finally {
			liveLoading = false;
		}
	}

	async function closePosition(pos: Position) {
		if (!currentWallet) return;
		try {
			if (pos.source === 'sentinel-paper') {
				await fetch(`/api/paper/close/${pos.id}?wallet=${currentWallet}`, { method: 'POST' });
			} else if (pos.source === 'sentinel-onchain') {
				const solPrice = (await (await fetch(`/api/pyth/${pos.asset.split('-')[0]}`)).json()).price;
				const mod = await import('$lib/onchain/openLeveraged');
				await mod.closeLeveragedPosition(pos.id, solPrice);
			}
			await loadLivePositions(currentWallet);
		} catch (e: any) {
			liveError = e?.message || 'close failed';
		}
	}

	function handleOpened() {
		if (currentWallet) loadLivePositions(currentWallet);
	}

	onMount(async () => {
		await loadDemo();
	});

	walletStore.subscribe((state) => {
		if (state.connected && state.address && state.address !== currentWallet) {
			currentWallet = state.address;
			loadLivePositions(state.address);
		}
		if (!state.connected) {
			currentWallet = null;
			livePositions = [];
			hasDriftAccount = false;
			liveError = '';
		}
	});

	$: mergedPositions = currentWallet
		? livePositions
		: positions;

	function riskClass(level: RiskLevel): string {
		return `badge-${level.toLowerCase()}`;
	}

	function gaugeColor(hf: number): string {
		if (hf >= 2.0) return 'var(--safe)';
		if (hf >= 1.5) return 'var(--warning)';
		if (hf >= 1.15) return 'var(--danger)';
		return 'var(--critical)';
	}

	function gaugeWidth(hf: number): number {
		return Math.min(Math.max((hf / 5) * 100, 5), 100);
	}
</script>

<div class="dashboard">
	<!-- Stats Row -->
	<div class="stats-row">
		<div class="stat-card">
			<div class="stat-label">TOTAL COLLATERAL</div>
			<div class="stat-value">${totalCollateral.toLocaleString()}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">TOTAL DEBT</div>
			<div class="stat-value">${totalDebt.toLocaleString()}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">AVG HEALTH FACTOR</div>
			<div class="stat-value" style="color: {gaugeColor(avgHealth)}">{avgHealth.toFixed(2)}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">AT RISK</div>
			<div class="stat-value" style="color: {criticalCount > 0 ? 'var(--critical)' : 'var(--safe)'}">{criticalCount}</div>
		</div>
	</div>

	<!-- Supported Protocols -->
	<div class="section-header">
		<h2>SUPPORTED PROTOCOLS</h2>
		<span class="count">{supportedProtocols.filter(p => p.status === 'TRACKING').length}/{supportedProtocols.length} online</span>
	</div>
	<div class="protocols-row">
		{#each supportedProtocols as proto}
			<div class="proto-card panel" class:proto-offline={proto.status !== 'TRACKING'}>
				<div class="proto-mark" style="color: {proto.accent}">{proto.mark}</div>
				<div class="proto-body">
					<div class="proto-name">{proto.name}</div>
					<div class="proto-kind">{proto.kind}</div>
				</div>
				<span class="proto-status proto-status-{proto.status.toLowerCase()}">{proto.status}</span>
			</div>
		{/each}
	</div>

	{#if currentWallet}
		<div class="live-banner panel" class:live-ok={livePositions.length > 0} class:live-empty={livePositions.length === 0 && !liveLoading && !liveError}>
			<div class="live-banner-left">
				<span class="live-dot"></span>
				<span class="live-title">
					{#if liveLoading}
						Loading positions for {currentWallet.slice(0, 4)}…{currentWallet.slice(-4)}
					{:else if liveError}
						Position reader error: {liveError}
					{:else if livePositions.length > 0}
						LIVE · {livePositions.length} tracked position{livePositions.length === 1 ? '' : 's'} for {currentWallet.slice(0, 4)}…{currentWallet.slice(-4)}
					{:else}
						Wallet {currentWallet.slice(0, 4)}…{currentWallet.slice(-4)} connected · no open positions yet
					{/if}
				</span>
			</div>
			<div class="live-banner-actions">
				<button class="live-cta" on:click={() => modalOpen = true}>
					+ OPEN POSITION
				</button>
				{#if livePositions.length > 0}
					<button class="live-refresh" on:click={() => currentWallet && loadLivePositions(currentWallet)}>REFRESH</button>
				{/if}
			</div>
		</div>
	{/if}

	<OpenPositionModal
		open={modalOpen}
		wallet={currentWallet}
		{onChainAvailable}
		on:close={() => modalOpen = false}
		on:opened={handleOpened}
	/>

	<!-- Positions Grid -->
	<div class="section-header">
		<h2>MONITORED POSITIONS</h2>
		<div class="section-meta">
			{#if currentWallet && livePositions.length > 0}
				<span class="data-badge live">LIVE · DEVNET</span>
			{:else if currentWallet}
				<span class="data-badge">NO POSITIONS</span>
			{:else}
				<span class="data-badge" class:live={dataSource === 'LIVE'}>{dataSource}</span>
			{/if}
			<span class="count">{mergedPositions.length} active</span>
		</div>
	</div>
	<div class="positions-grid">
		{#each mergedPositions as pos}
			<div class="position-card panel" class:pos-live={pos.source === 'sentinel-onchain' || pos.source === 'drift-devnet'} class:pos-balance={pos.source === 'native' || pos.source === 'spl' || pos.source === 'marinade'}>
				<div class="pos-header">
					<div>
						<span class="pos-protocol">
							{pos.protocol}
							{#if pos.source === 'sentinel-onchain'}<span class="live-tag">ON-CHAIN</span>{/if}
							{#if pos.source === 'sentinel-paper'}<span class="live-tag paper">PAPER</span>{/if}
							{#if pos.source === 'kamino' || pos.source === 'marginfi'}<span class="live-tag live">LIVE</span>{/if}
							{#if pos.source === 'marinade'}<span class="live-tag stake">STAKED</span>{/if}
							{#if pos.source === 'native' || pos.source === 'spl'}<span class="live-tag wallet">WALLET</span>{/if}
						</span>
						<span class="pos-asset">{pos.asset}{#if pos.direction && pos.direction !== 'FLAT'} · <span class="dir dir-{pos.direction.toLowerCase()}">{pos.direction}</span>{/if}</span>
					</div>
					<span class="badge {riskClass(pos.riskLevel)}">{pos.riskLevel}</span>
				</div>
				{#if pos.healthFactor !== undefined && pos.source !== 'native' && pos.source !== 'spl' && pos.source !== 'marinade'}
					<div class="pos-health">
						<div class="health-label">
							<span>Health Factor</span>
							<span style="color: {gaugeColor(pos.healthFactor)}">{pos.healthFactor.toFixed(2)}{#if pos.healthPercent !== undefined} · {pos.healthPercent.toFixed(0)}%{/if}</span>
						</div>
						<div class="gauge-bar">
							<div class="gauge-fill" style="width: {gaugeWidth(pos.healthFactor)}%; background: {gaugeColor(pos.healthFactor)}"></div>
						</div>
					</div>
				{/if}
				<div class="pos-details">
					{#if pos.balance !== undefined}
						<div class="detail-row">
							<span class="detail-label">Balance</span>
							<span class="detail-value">{pos.balance.toLocaleString(undefined, { maximumFractionDigits: 6 })} {pos.asset}</span>
						</div>
					{/if}
					{#if pos.solEquivalent !== undefined}
						<div class="detail-row">
							<span class="detail-label">≈ in SOL</span>
							<span class="detail-value">{pos.solEquivalent.toFixed(4)} SOL</span>
						</div>
					{/if}
					{#if pos.exchangeRate !== undefined}
						<div class="detail-row">
							<span class="detail-label">mSOL / SOL</span>
							<span class="detail-value">{pos.exchangeRate.toFixed(4)}</span>
						</div>
					{/if}
					{#if pos.collateral !== undefined && pos.balance === undefined}
						<div class="detail-row">
							<span class="detail-label">Collateral</span>
							<span class="detail-value">${pos.collateral.toLocaleString()}</span>
						</div>
					{/if}
					{#if pos.notional !== undefined}
						<div class="detail-row">
							<span class="detail-label">Notional</span>
							<span class="detail-value">${pos.notional.toLocaleString()}</span>
						</div>
					{:else if pos.debt !== undefined && pos.balance === undefined}
						<div class="detail-row">
							<span class="detail-label">Debt</span>
							<span class="detail-value">${pos.debt.toLocaleString()}</span>
						</div>
					{/if}
					{#if pos.leverage}
						<div class="detail-row">
							<span class="detail-label">Leverage</span>
							<span class="detail-value">{pos.leverage.toFixed(2)}x</span>
						</div>
					{/if}
					{#if pos.unrealizedPnl !== undefined}
						<div class="detail-row">
							<span class="detail-label">Unrealized PnL</span>
							<span class="detail-value" style="color: {pos.unrealizedPnl >= 0 ? 'var(--safe)' : 'var(--critical)'}">
								{pos.unrealizedPnl >= 0 ? '+' : ''}${pos.unrealizedPnl.toLocaleString()}
							</span>
						</div>
					{/if}
					<div class="detail-row">
						<span class="detail-label">Last Check</span>
						<span class="detail-value dim">{pos.lastChecked}</span>
					</div>
				</div>

				{#if pos.advice && pos.advice.length > 0}
					<div class="advice-block">
						<div class="advice-header">BOT ADVICE</div>
						{#each pos.advice as tip}
							<div class="advice-tip advice-{tip.severity.toLowerCase()}">
								<div class="advice-title">{tip.title}</div>
								<div class="advice-body">{tip.body}</div>
							</div>
						{/each}
					</div>
				{/if}

				{#if pos.source === 'sentinel-paper' || pos.source === 'sentinel-onchain'}
					<div class="pos-actions">
						<button class="close-pos-btn" on:click={() => closePosition(pos)}>CLOSE POSITION</button>
					</div>
				{/if}
			</div>
		{/each}
	</div>

	<!-- Recent Alerts -->
	<div class="section-header" style="margin-top: 32px;">
		<h2>RECENT ALERTS</h2>
		<a href="/alerts" class="view-all">View All &raquo;</a>
	</div>
	<div class="alerts-list">
		{#each recentAlerts as alert}
			<div class="alert-row panel">
				<span class="badge {riskClass(alert.severity)}">{alert.type}</span>
				<span class="alert-message">{alert.message}</span>
				<span class="alert-time">{alert.timestamp}</span>
			</div>
		{/each}
	</div>
</div>

<style>
	.dashboard {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.stats-row {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 12px;
	}

	.stat-card {
		background: var(--bg-panel);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 16px;
	}

	.stat-label {
		font-size: 10px;
		font-weight: 600;
		color: var(--text-dim);
		letter-spacing: 1px;
		margin-bottom: 8px;
	}

	.stat-value {
		font-size: 24px;
		font-weight: 700;
		color: var(--text-primary);
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 16px;
	}

	.section-header h2 {
		font-size: 12px;
		font-weight: 600;
		color: var(--text-secondary);
		letter-spacing: 1.5px;
	}

	.section-meta {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.count {
		font-size: 11px;
		color: var(--text-dim);
	}

	.data-badge {
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 1px;
		padding: 2px 6px;
		border-radius: 2px;
		background: rgba(255, 170, 0, 0.15);
		color: var(--warning);
	}

	.data-badge.live {
		background: rgba(61, 220, 132, 0.15);
		color: var(--safe);
	}

	.view-all {
		font-size: 11px;
	}

	.positions-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 12px;
	}

	.position-card {
		padding: 16px;
	}

	.pos-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 12px;
	}

	.pos-protocol {
		font-size: 10px;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 1px;
		display: block;
		margin-bottom: 2px;
	}

	.pos-asset {
		font-size: 15px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.pos-health {
		margin-bottom: 14px;
	}

	.health-label {
		display: flex;
		justify-content: space-between;
		font-size: 11px;
		color: var(--text-secondary);
		margin-bottom: 6px;
	}

	.pos-details {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		font-size: 11px;
	}

	.detail-label {
		color: var(--text-dim);
	}

	.detail-value {
		color: var(--text-secondary);
	}

	.detail-value.dim {
		color: var(--text-dim);
	}

	.alerts-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.alert-row {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 12px 16px;
	}

	.alert-message {
		flex: 1;
		font-size: 12px;
		color: var(--text-secondary);
	}

	.alert-time {
		font-size: 10px;
		color: var(--text-dim);
		white-space: nowrap;
	}

	.live-banner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 12px 16px;
		border-left: 3px solid var(--accent-amber);
	}

	.live-banner.live-ok {
		border-left-color: var(--accent-green);
	}

	.live-banner.live-empty {
		border-left-color: var(--text-dim);
	}

	.live-banner-left {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.live-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--accent-amber);
		animation: pulse-glow 2s infinite;
	}

	.live-banner.live-ok .live-dot {
		background: var(--accent-green);
	}

	.live-banner.live-empty .live-dot {
		background: var(--text-dim);
		animation: none;
	}

	.live-title {
		font-size: 11px;
		color: var(--text-primary);
		letter-spacing: 0.5px;
	}

	.live-banner-actions {
		display: flex;
		gap: 6px;
	}

	.live-cta, .live-refresh {
		background: transparent;
		border: 1px solid var(--border-bright);
		color: var(--accent-green);
		font-family: inherit;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 1px;
		padding: 5px 10px;
		border-radius: 2px;
		cursor: pointer;
		text-decoration: none;
	}

	.live-cta:hover, .live-refresh:hover {
		border-color: var(--accent-green);
	}

	.pos-actions {
		margin-top: 12px;
		padding-top: 10px;
		border-top: 1px dashed var(--border);
	}

	.close-pos-btn {
		width: 100%;
		background: transparent;
		border: 1px solid var(--border-bright);
		color: var(--text-secondary);
		font-family: inherit;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 1.5px;
		padding: 8px;
		border-radius: 2px;
		cursor: pointer;
	}

	.close-pos-btn:hover {
		border-color: var(--critical);
		color: var(--critical);
	}

	.live-tag {
		display: inline-block;
		margin-left: 6px;
		font-size: 8px;
		font-weight: 700;
		color: var(--accent-green);
		background: rgba(61,220,132,0.12);
		padding: 1px 4px;
		border-radius: 2px;
		letter-spacing: 1px;
	}

	.live-tag.paper {
		color: var(--warning);
		background: rgba(255,170,0,0.12);
	}

	.live-tag.stake {
		color: #52c4ff;
		background: rgba(82,196,255,0.12);
	}

	.live-tag.wallet {
		color: #7a9a7a;
		background: rgba(122,154,122,0.15);
	}

	.pos-live {
		border-color: rgba(160, 123, 255, 0.4);
	}

	.pos-balance {
		border-color: rgba(82, 196, 255, 0.25);
	}

	.dir {
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 1px;
		padding: 1px 4px;
		border-radius: 2px;
		margin-left: 4px;
	}

	.dir-long { background: rgba(61,220,132,0.15); color: var(--safe); }
	.dir-short { background: rgba(255,68,68,0.15); color: var(--critical); }

	.advice-block {
		margin-top: 14px;
		padding-top: 12px;
		border-top: 1px dashed var(--border);
	}

	.advice-header {
		font-size: 9px;
		color: var(--text-dim);
		letter-spacing: 1.5px;
		margin-bottom: 8px;
	}

	.advice-tip {
		padding: 8px 10px;
		margin-bottom: 6px;
		border-radius: 2px;
		border-left: 2px solid transparent;
		background: rgba(255,255,255,0.02);
	}

	.advice-tip:last-child { margin-bottom: 0; }

	.advice-critical { border-left-color: var(--critical); }
	.advice-warning  { border-left-color: var(--warning); }
	.advice-danger   { border-left-color: var(--danger); }
	.advice-safe     { border-left-color: var(--safe); }

	.advice-title {
		font-size: 11px;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 3px;
	}

	.advice-body {
		font-size: 11px;
		color: var(--text-secondary);
		line-height: 1.4;
	}

	.protocols-row {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 10px;
	}

	.proto-card {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 12px;
		position: relative;
	}

	.proto-card.proto-offline {
		opacity: 0.55;
	}

	.proto-mark {
		font-size: 22px;
		line-height: 1;
		min-width: 22px;
		text-align: center;
	}

	.proto-body {
		flex: 1;
		min-width: 0;
	}

	.proto-name {
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		letter-spacing: 0.5px;
	}

	.proto-kind {
		font-size: 9px;
		color: var(--text-dim);
		margin-top: 2px;
		letter-spacing: 0.3px;
	}

	.proto-status {
		font-size: 8px;
		font-weight: 700;
		letter-spacing: 1px;
		padding: 2px 5px;
		border-radius: 2px;
	}

	.proto-status-tracking {
		background: rgba(61,220,132,0.15);
		color: var(--safe);
	}

	.proto-status-offline {
		background: rgba(255,68,68,0.1);
		color: var(--text-dim);
	}

	.proto-status-soon {
		background: rgba(255,170,0,0.12);
		color: var(--warning);
	}

	@media (max-width: 900px) {
		.protocols-row {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (max-width: 768px) {
		.stats-row {
			grid-template-columns: repeat(2, 1fr);
		}
		.positions-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
