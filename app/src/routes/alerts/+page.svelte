<script lang="ts">
	type Severity = 'Safe' | 'Warning' | 'Danger' | 'Critical';

	interface Alert {
		id: string;
		type: string;
		protocol: string;
		position: string;
		message: string;
		healthFactor: number;
		timestamp: string;
		severity: Severity;
	}

	const alerts: Alert[] = [
		{ id: 'a1', type: 'LIQUIDATION_IMMINENT', protocol: 'Kamino', position: 'JitoSOL/SOL', message: 'Health factor dropped below 1.10 — liquidation within ~15 minutes at current rate', healthFactor: 1.08, timestamp: '10 seconds ago', severity: 'Critical' },
		{ id: 'a2', type: 'HEALTH_DECLINING', protocol: 'Drift', position: 'ETH-PERP', message: 'Position approaching warning zone — health factor 1.35 and declining', healthFactor: 1.35, timestamp: '2 minutes ago', severity: 'Warning' },
		{ id: 'a3', type: 'AUTO_PROTECT', protocol: 'Kamino', position: 'JitoSOL/SOL', message: 'Auto-protect triggered: added 200 USDC collateral to prevent liquidation', healthFactor: 1.08, timestamp: '15 minutes ago', severity: 'Safe' },
		{ id: 'a4', type: 'HEALTH_RECOVERED', protocol: 'Drift', position: 'SOL-PERP', message: 'Health factor recovered from 1.45 to 1.72 after price improvement', healthFactor: 1.72, timestamp: '1 hour ago', severity: 'Safe' },
		{ id: 'a5', type: 'NEW_POSITION', protocol: 'Marinade', position: 'mSOL', message: 'New position detected and added to monitoring queue', healthFactor: 4.10, timestamp: '3 hours ago', severity: 'Safe' },
		{ id: 'a6', type: 'HEALTH_DECLINING', protocol: 'Kamino', position: 'SOL/USDC', message: 'Gradual health factor decline detected — dropped from 2.80 to 2.41 in 6 hours', healthFactor: 2.41, timestamp: '6 hours ago', severity: 'Warning' },
	];

	function severityClass(s: Severity): string {
		return `badge-${s.toLowerCase()}`;
	}
</script>

<div class="alerts-page">
	<div class="page-header">
		<h1>ALERT FEED</h1>
		<div class="filter-row">
			<button class="filter-btn active">All</button>
			<button class="filter-btn">Critical</button>
			<button class="filter-btn">Warnings</button>
			<button class="filter-btn">Resolved</button>
		</div>
	</div>

	<div class="alert-feed">
		{#each alerts as alert}
			<div class="alert-card panel" class:critical-border={alert.severity === 'Critical'}>
				<div class="alert-top">
					<span class="badge {severityClass(alert.severity)}">{alert.type.replace(/_/g, ' ')}</span>
					<span class="alert-ts">{alert.timestamp}</span>
				</div>
				<div class="alert-body">
					<div class="alert-target">
						<span class="target-protocol">{alert.protocol}</span>
						<span class="target-position">{alert.position}</span>
						<span class="target-hf" style="color: {alert.healthFactor >= 2 ? 'var(--safe)' : alert.healthFactor >= 1.5 ? 'var(--warning)' : alert.healthFactor >= 1.15 ? 'var(--danger)' : 'var(--critical)'}">
							HF: {alert.healthFactor.toFixed(2)}
						</span>
					</div>
					<p class="alert-msg">{alert.message}</p>
				</div>
			</div>
		{/each}
	</div>
</div>

<style>
	.alerts-page {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.page-header h1 {
		font-size: 14px;
		font-weight: 700;
		letter-spacing: 2px;
	}

	.filter-row {
		display: flex;
		gap: 4px;
	}

	.filter-btn {
		background: var(--bg-panel);
		border: 1px solid var(--border);
		color: var(--text-dim);
		padding: 4px 12px;
		font-size: 10px;
		font-family: 'IBM Plex Mono', monospace;
		font-weight: 500;
		cursor: pointer;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		border-radius: 2px;
		transition: all 0.15s;
	}

	.filter-btn:hover {
		color: var(--text-secondary);
		border-color: var(--border-bright);
	}

	.filter-btn.active {
		color: var(--accent-green);
		border-color: var(--accent-green);
		background: rgba(61, 220, 132, 0.08);
	}

	.alert-feed {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.alert-card {
		padding: 14px 18px;
	}

	.critical-border {
		border-color: rgba(255, 68, 68, 0.3);
		background: rgba(255, 68, 68, 0.03);
	}

	.alert-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
	}

	.alert-ts {
		font-size: 10px;
		color: var(--text-dim);
	}

	.alert-body {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.alert-target {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.target-protocol {
		font-size: 10px;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.target-position {
		font-size: 13px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.target-hf {
		font-size: 11px;
		font-weight: 600;
	}

	.alert-msg {
		font-size: 12px;
		color: var(--text-secondary);
		line-height: 1.5;
	}
</style>
