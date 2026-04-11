<script lang="ts">
	import { onMount } from 'svelte';

	type RiskLevel = 'Safe' | 'Warning' | 'Danger' | 'Critical';

	interface Position {
		id: string;
		protocol: string;
		asset: string;
		healthFactor: number;
		collateral: number;
		debt: number;
		riskLevel: RiskLevel;
		lastChecked: string;
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

	let positions: Position[] = fallbackPositions;
	let recentAlerts: AlertItem[] = fallbackAlerts;
	let dataSource: 'LIVE' | 'DEMO' = 'DEMO';

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

	onMount(async () => {
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
	});

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

	<!-- Positions Grid -->
	<div class="section-header">
		<h2>MONITORED POSITIONS</h2>
		<div class="section-meta">
			<span class="data-badge" class:live={dataSource === 'LIVE'}>{dataSource}</span>
			<span class="count">{positions.length} active</span>
		</div>
	</div>
	<div class="positions-grid">
		{#each positions as pos}
			<div class="position-card panel">
				<div class="pos-header">
					<div>
						<span class="pos-protocol">{pos.protocol}</span>
						<span class="pos-asset">{pos.asset}</span>
					</div>
					<span class="badge {riskClass(pos.riskLevel)}">{pos.riskLevel}</span>
				</div>
				<div class="pos-health">
					<div class="health-label">
						<span>Health Factor</span>
						<span style="color: {gaugeColor(pos.healthFactor)}">{pos.healthFactor.toFixed(2)}</span>
					</div>
					<div class="gauge-bar">
						<div class="gauge-fill" style="width: {gaugeWidth(pos.healthFactor)}%; background: {gaugeColor(pos.healthFactor)}"></div>
					</div>
				</div>
				<div class="pos-details">
					<div class="detail-row">
						<span class="detail-label">Collateral</span>
						<span class="detail-value">${pos.collateral.toLocaleString()}</span>
					</div>
					<div class="detail-row">
						<span class="detail-label">Debt</span>
						<span class="detail-value">${pos.debt.toLocaleString()}</span>
					</div>
					<div class="detail-row">
						<span class="detail-label">Last Check</span>
						<span class="detail-value dim">{pos.lastChecked}</span>
					</div>
				</div>
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

	@media (max-width: 768px) {
		.stats-row {
			grid-template-columns: repeat(2, 1fr);
		}
		.positions-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
