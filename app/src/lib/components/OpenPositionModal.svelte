<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let open = false;
	export let wallet: string | null = null;
	export let onChainAvailable = false;

	const dispatch = createEventDispatcher<{ close: void; opened: any }>();

	type Asset = 'SOL' | 'BTC' | 'ETH';
	type Direction = 'LONG' | 'SHORT';

	let asset: Asset = 'SOL';
	let direction: Direction = 'LONG';
	let collateral = 100;
	let leverage = 5;
	let livePrice: number | null = null;
	let priceError = '';
	let submitting: 'paper' | 'onchain' | null = null;
	let submitError = '';

	let priceFetchToken = 0;
	async function refreshPrice() {
		const token = ++priceFetchToken;
		priceError = '';
		try {
			const res = await fetch(`/api/pyth/${asset}`);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const data = await res.json();
			if (token !== priceFetchToken) return; // stale request
			livePrice = data.price;
		} catch (e: any) {
			if (token !== priceFetchToken) return;
			priceError = e?.message || 'price fetch failed';
			livePrice = null;
		}
	}

	// Only refetch when modal opens or the asset actually changes.
	let lastAsset: Asset | '' = '';
	$: if (open && asset !== lastAsset) {
		lastAsset = asset;
		refreshPrice();
	}

	$: notional = collateral * leverage;
	$: liqPrice = livePrice !== null
		? direction === 'LONG'
			? livePrice * (1 - 0.95 / leverage)
			: livePrice * (1 + 0.95 / leverage)
		: null;
	$: baseSize = livePrice !== null ? notional / livePrice : null;

	function validateInputs(): string | null {
		if (!wallet) return 'Connect wallet first';
		if (!collateral || collateral < 10) return 'Collateral must be at least $10';
		if (!leverage || leverage < 1 || leverage > 20) return 'Leverage must be between 1x and 20x';
		return null;
	}

	async function submitPaper() {
		const err = validateInputs();
		if (err) { submitError = err; return; }
		submitting = 'paper';
		submitError = '';
		try {
			const res = await fetch('/api/paper/open', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					wallet,
					asset,
					direction,
					collateralUsd: collateral,
					leverage,
				}),
			});
			const body = await res.json();
			if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
			dispatch('opened', body);
			dispatch('close');
		} catch (e: any) {
			submitError = e?.message || 'failed to open';
		} finally {
			submitting = null;
		}
	}

	async function submitOnChain() {
		const err = validateInputs();
		if (err) { submitError = err; return; }
		if (!onChainAvailable) {
			submitError = 'On-chain not available yet (program deploy in progress)';
			return;
		}
		submitting = 'onchain';
		submitError = '';
		try {
			// Delegated to a dedicated module once deploy completes
			const mod = await import('$lib/onchain/openLeveraged');
			const result = await mod.openLeveragedPosition({
				wallet,
				asset,
				direction,
				collateralUsd: collateral,
				leverage,
			});
			dispatch('opened', result);
			dispatch('close');
		} catch (e: any) {
			submitError = e?.message || 'tx failed';
		} finally {
			submitting = null;
		}
	}

	function closeModal() {
		if (submitting) return;
		dispatch('close');
	}

	function handleWindowKey(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'Escape') {
			e.preventDefault();
			closeModal();
		}
	}
</script>

<svelte:window on:keydown={handleWindowKey} />

{#if open}
	<div class="backdrop" on:click={closeModal}></div>
	<div class="modal panel" role="dialog" aria-modal="true" aria-labelledby="open-position-title">
		<div class="modal-header">
			<h3 id="open-position-title">OPEN LEVERAGED POSITION</h3>
			<button class="close-btn" on:click={closeModal} aria-label="close">&times;</button>
		</div>

		<div class="modal-body">
			<div class="field-row">
				<label class="field">
					<span class="field-label">Asset</span>
					<select bind:value={asset} class="input">
						<option value="SOL">SOL / USD</option>
						<option value="BTC">BTC / USD</option>
						<option value="ETH">ETH / USD</option>
					</select>
				</label>
				<div class="field">
					<span class="field-label">Oracle price</span>
					<div class="price-display">
						{#if priceError}
							<span class="err">{priceError}</span>
						{:else if livePrice === null}
							<span class="dim">loading…</span>
						{:else}
							${livePrice.toLocaleString(undefined, { maximumFractionDigits: 4 })}
						{/if}
					</div>
				</div>
			</div>

			<div class="dir-toggle">
				<button class:active={direction === 'LONG'} on:click={() => direction = 'LONG'} class="dir-btn dir-long">LONG</button>
				<button class:active={direction === 'SHORT'} on:click={() => direction = 'SHORT'} class="dir-btn dir-short">SHORT</button>
			</div>

			<label class="field full">
				<span class="field-label">Collateral (USD)</span>
				<input type="number" min="10" step="10" bind:value={collateral} class="input" />
			</label>

			<label class="field full">
				<span class="field-label">Leverage · {leverage}x</span>
				<input type="range" min="1" max="20" step="1" bind:value={leverage} class="range" />
				<div class="range-ticks">
					<span>1x</span><span>5x</span><span>10x</span><span>15x</span><span>20x</span>
				</div>
			</label>

			<div class="summary panel-inner">
				<div class="sum-row">
					<span class="sum-label">Notional</span>
					<span class="sum-val">${notional.toLocaleString()}</span>
				</div>
				<div class="sum-row">
					<span class="sum-label">Base size</span>
					<span class="sum-val">{baseSize ? baseSize.toFixed(6) : '—'} {asset}</span>
				</div>
				<div class="sum-row">
					<span class="sum-label">Liquidation price</span>
					<span class="sum-val" style="color: var(--critical)">
						{liqPrice ? `$${liqPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '—'}
					</span>
				</div>
			</div>

			{#if submitError}
				<div class="err-banner">{submitError}</div>
			{/if}

			<div class="devnet-hint">
				On-chain path signs a Solana <strong>devnet</strong> transaction.
				Switch Phantom to devnet in Developer Settings before signing.
			</div>
		</div>

		<div class="modal-footer">
			<button
				class="btn btn-paper"
				on:click={submitPaper}
				disabled={submitting !== null || !wallet}
			>
				{submitting === 'paper' ? 'OPENING…' : 'PAPER TRADE'}
			</button>
			<button
				class="btn btn-onchain"
				on:click={submitOnChain}
				disabled={submitting !== null || !wallet || !onChainAvailable}
				title={onChainAvailable ? '' : 'On-chain deploy pending'}
			>
				{submitting === 'onchain' ? 'SIGNING…' : 'OPEN ON-CHAIN'}
			</button>
		</div>
	</div>
{/if}

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.65);
		z-index: 100;
	}
	.modal {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: min(520px, 92vw);
		z-index: 101;
		padding: 0;
	}
	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 16px 18px;
		border-bottom: 1px solid var(--border);
	}
	.modal-header h3 {
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 1.5px;
		color: var(--text-primary);
	}
	.close-btn {
		background: none;
		border: none;
		color: var(--text-dim);
		font-size: 24px;
		cursor: pointer;
		line-height: 1;
	}
	.close-btn:hover { color: var(--text-primary); }
	.modal-body {
		padding: 16px 18px;
		display: flex;
		flex-direction: column;
		gap: 14px;
	}
	.field-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 12px;
	}
	.field {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.field.full { grid-column: 1 / -1; }
	.field-label {
		font-size: 10px;
		color: var(--text-dim);
		letter-spacing: 1px;
	}
	.input, .range {
		background: var(--bg-base);
		border: 1px solid var(--border);
		color: var(--text-primary);
		padding: 8px 10px;
		font-family: inherit;
		font-size: 13px;
		border-radius: 2px;
		width: 100%;
	}
	.input:focus { outline: 1px solid var(--accent-green); }
	.range { padding: 0; height: 24px; }
	.range-ticks {
		display: flex;
		justify-content: space-between;
		font-size: 9px;
		color: var(--text-dim);
		margin-top: 2px;
	}
	.price-display {
		padding: 8px 10px;
		background: var(--bg-base);
		border: 1px solid var(--border);
		border-radius: 2px;
		font-size: 13px;
		font-weight: 600;
		color: var(--safe);
	}
	.dim { color: var(--text-dim); }
	.err { color: var(--critical); font-size: 11px; }
	.dir-toggle {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0;
		border: 1px solid var(--border);
		border-radius: 2px;
		overflow: hidden;
	}
	.dir-btn {
		background: transparent;
		border: none;
		color: var(--text-dim);
		padding: 10px;
		font-family: inherit;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 1.5px;
		cursor: pointer;
	}
	.dir-btn.active.dir-long {
		background: rgba(61, 220, 132, 0.18);
		color: var(--safe);
	}
	.dir-btn.active.dir-short {
		background: rgba(255, 68, 68, 0.18);
		color: var(--critical);
	}
	.summary {
		background: var(--bg-base);
		border: 1px solid var(--border);
		border-radius: 2px;
		padding: 10px 12px;
	}
	.panel-inner {
		display: flex;
		flex-direction: column;
		gap: 5px;
	}
	.sum-row {
		display: flex;
		justify-content: space-between;
		font-size: 11px;
	}
	.sum-label { color: var(--text-dim); }
	.sum-val { color: var(--text-primary); font-weight: 500; }
	.err-banner {
		padding: 8px 10px;
		background: rgba(255, 68, 68, 0.1);
		border-left: 3px solid var(--critical);
		color: var(--critical);
		font-size: 11px;
	}

	.devnet-hint {
		padding: 6px 10px;
		background: rgba(61, 220, 132, 0.05);
		border-left: 2px solid var(--border-bright);
		color: var(--text-dim);
		font-size: 10px;
		line-height: 1.4;
	}

	.devnet-hint strong {
		color: var(--accent-green);
		font-weight: 700;
	}
	.modal-footer {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
		padding: 14px 18px;
		border-top: 1px solid var(--border);
	}
	.btn {
		padding: 10px;
		font-family: inherit;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 1.5px;
		border: 1px solid var(--border-bright);
		border-radius: 2px;
		cursor: pointer;
		background: transparent;
		color: var(--text-secondary);
	}
	.btn:hover:not(:disabled) {
		border-color: var(--accent-green);
		color: var(--text-primary);
	}
	.btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.btn-paper { color: var(--warning); border-color: rgba(255, 170, 0, 0.3); }
	.btn-onchain { color: var(--accent-green); border-color: rgba(61, 220, 132, 0.3); }
</style>
