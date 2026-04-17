<script lang="ts">
	import { onMount } from 'svelte';
	import { walletStore } from '$lib/stores/wallet';

	type RiskLevel = 'Safe' | 'Warning' | 'Danger' | 'Critical';

	interface Position {
		id: string;
		protocol: string;
		asset: string;
		healthFactor: number;
		liquidationPrice?: number;
		collateral: number;
		debt: number;
		riskLevel: RiskLevel;
		autoProtect?: boolean;
		lastChecked: string;
		source?: string;
		direction?: 'LONG' | 'SHORT' | 'FLAT';
		leverage?: number;
		unrealizedPnl?: number;
	}

	const fallbackPositions: Position[] = [
		{ id: 'p1', protocol: 'Kamino', asset: 'SOL/USDC', healthFactor: 2.41, liquidationPrice: 68.20, collateral: 12500, debt: 5180, riskLevel: 'Safe', autoProtect: true, lastChecked: '2m ago' },
		{ id: 'p2', protocol: 'Drift', asset: 'ETH-PERP', healthFactor: 1.35, liquidationPrice: 2180.50, collateral: 8200, debt: 6074, riskLevel: 'Warning', autoProtect: false, lastChecked: '45s ago' },
		{ id: 'p3', protocol: 'Marinade', asset: 'mSOL', healthFactor: 4.10, liquidationPrice: 32.10, collateral: 25000, debt: 6097, riskLevel: 'Safe', autoProtect: true, lastChecked: '1m ago' },
		{ id: 'p4', protocol: 'Kamino', asset: 'JitoSOL/SOL', healthFactor: 1.08, liquidationPrice: 142.80, collateral: 3400, debt: 3148, riskLevel: 'Critical', autoProtect: true, lastChecked: '10s ago' },
		{ id: 'p5', protocol: 'Drift', asset: 'SOL-PERP', healthFactor: 1.72, liquidationPrice: 95.40, collateral: 6800, debt: 3953, riskLevel: 'Warning', autoProtect: false, lastChecked: '30s ago' },
	];

	let positions: Position[] = fallbackPositions;
	let livePositions: Position[] = [];
	let dataSource: 'LIVE' | 'DEMO' = 'DEMO';
	let currentWallet: string | null = null;

	async function loadDemo() {
		try {
			const res = await fetch('/api/positions');
			if (res.ok) {
				positions = await res.json();
				dataSource = 'LIVE';
			}
		} catch {
			// API unavailable — keep fallback data
		}
	}

	async function evaluateOnChainRaw(raw: any): Promise<Position | null> {
		try {
			const solPrice = (await (await fetch('/api/pyth/SOL')).json()).price;
			const collateralSol = Number(raw.collateralLamports) / 1_000_000_000;
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
			return res.ok ? await res.json() : null;
		} catch {
			return null;
		}
	}

	async function loadLive(wallet: string) {
		try {
			const paper = await fetch(`/api/paper/positions/${wallet}`).then((r) => (r.ok ? r.json() : []));
			let onchain: Position[] = [];
			try {
				const mod = await import('$lib/onchain/openLeveraged');
				const raw = await mod.listOnChainPositions(wallet);
				const evaluated = await Promise.all(raw.map(evaluateOnChainRaw));
				onchain = evaluated.filter((p): p is Position => p !== null);
			} catch {
				onchain = [];
			}
			livePositions = [...onchain, ...(Array.isArray(paper) ? paper : [])];
		} catch {
			livePositions = [];
		}
	}

	onMount(loadDemo);

	walletStore.subscribe((state) => {
		if (state.connected && state.address && state.address !== currentWallet) {
			currentWallet = state.address;
			loadLive(state.address);
		}
		if (!state.connected) {
			currentWallet = null;
			livePositions = [];
		}
	});

	$: allPositions = livePositions.length > 0
		? [...livePositions, ...positions.filter(p => p.protocol !== 'Drift')]
		: positions;

	function riskClass(level: RiskLevel): string {
		return `badge-${level.toLowerCase()}`;
	}

	function healthColor(hf: number): string {
		if (hf >= 2.0) return 'var(--safe)';
		if (hf >= 1.5) return 'var(--warning)';
		if (hf >= 1.15) return 'var(--danger)';
		return 'var(--critical)';
	}
</script>

<div class="positions-page">
	<div class="page-header">
		<h1>POSITION MONITOR</h1>
		<div class="header-meta">
			{#if livePositions.length > 0}
				<span class="data-badge live">LIVE · DRIFT DEVNET</span>
			{:else}
				<span class="data-badge" class:live={dataSource === 'LIVE'}>{dataSource}</span>
			{/if}
			<span class="subtitle">{allPositions.length} positions tracked across {new Set(allPositions.map(p => p.protocol)).size} protocols</span>
		</div>
	</div>

	<div class="table-wrap panel">
		<table>
			<thead>
				<tr>
					<th>Protocol</th>
					<th>Asset</th>
					<th>Dir</th>
					<th>Health</th>
					<th>Leverage</th>
					<th>Collateral</th>
					<th>PnL / Debt</th>
					<th>Status</th>
					<th>Updated</th>
				</tr>
			</thead>
			<tbody>
				{#each allPositions as pos}
					<tr class:row-critical={pos.riskLevel === 'Critical'} class:row-live={pos.source === 'drift-devnet'}>
						<td class="protocol-cell">
							{pos.protocol}
							{#if pos.source === 'drift-devnet'}<span class="live-mark">LIVE</span>{/if}
						</td>
						<td class="asset-cell">{pos.asset}</td>
						<td>
							{#if pos.direction && pos.direction !== 'FLAT'}
								<span class="dir dir-{pos.direction.toLowerCase()}">{pos.direction}</span>
							{:else}
								<span class="dim">—</span>
							{/if}
						</td>
						<td>
							<span style="color: {healthColor(pos.healthFactor)}; font-weight: 600">
								{pos.healthFactor.toFixed(2)}
							</span>
						</td>
						<td>{pos.leverage ? `${pos.leverage.toFixed(2)}x` : '—'}</td>
						<td>${pos.collateral.toLocaleString()}</td>
						<td>
							{#if pos.unrealizedPnl !== undefined}
								<span style="color: {pos.unrealizedPnl >= 0 ? 'var(--safe)' : 'var(--critical)'}">
									{pos.unrealizedPnl >= 0 ? '+' : ''}${pos.unrealizedPnl.toLocaleString()}
								</span>
							{:else}
								${pos.debt.toLocaleString()}
							{/if}
						</td>
						<td><span class="badge {riskClass(pos.riskLevel)}">{pos.riskLevel}</span></td>
						<td class="time-cell">{pos.lastChecked}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<style>
	.positions-page {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.page-header h1 {
		font-size: 14px;
		font-weight: 700;
		letter-spacing: 2px;
		color: var(--text-primary);
	}

	.header-meta {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-top: 4px;
	}

	.subtitle {
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

	.table-wrap {
		overflow-x: auto;
		padding: 0;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 12px;
	}

	th {
		text-align: left;
		padding: 12px 16px;
		font-size: 10px;
		font-weight: 600;
		color: var(--text-dim);
		letter-spacing: 1px;
		text-transform: uppercase;
		border-bottom: 1px solid var(--border);
		white-space: nowrap;
	}

	td {
		padding: 12px 16px;
		border-bottom: 1px solid var(--border);
		color: var(--text-secondary);
		white-space: nowrap;
	}

	tr:last-child td {
		border-bottom: none;
	}

	.row-critical {
		background: rgba(255, 68, 68, 0.05);
	}

	.protocol-cell {
		color: var(--text-dim);
		text-transform: uppercase;
		font-size: 10px;
		letter-spacing: 0.5px;
	}

	.asset-cell {
		font-weight: 600;
		color: var(--text-primary);
	}

	.shield-on {
		color: var(--accent-green);
		font-weight: 600;
		font-size: 10px;
	}

	.shield-off {
		color: var(--text-dim);
		font-size: 10px;
	}

	.time-cell {
		color: var(--text-dim);
		font-size: 10px;
	}

	.row-live {
		background: rgba(160, 123, 255, 0.04);
	}

	.live-mark {
		display: inline-block;
		margin-left: 6px;
		font-size: 8px;
		font-weight: 700;
		color: var(--accent-green);
		background: rgba(61, 220, 132, 0.12);
		padding: 1px 4px;
		border-radius: 2px;
		letter-spacing: 1px;
	}

	.dir {
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 1px;
		padding: 2px 6px;
		border-radius: 2px;
	}

	.dir-long { background: rgba(61, 220, 132, 0.15); color: var(--safe); }
	.dir-short { background: rgba(255, 68, 68, 0.15); color: var(--critical); }
	.dim { color: var(--text-dim); }
</style>
